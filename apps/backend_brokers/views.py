#import decimal
#import json
from datetime import datetime, timedelta
from collections import OrderedDict

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login
from django.conf import settings
from django.contrib.auth.decorators import login_required
from .forms import (
    RegisterForm,
    UserEditForm,
    ProfileEditForm,
    AddWalletForm,
    WalletDeleteForm,
    TransferForm,
    DepositForm,
)
from .models import Profile, Wallet, Transaction, ExchangeRate
from apps.backend_brokers.nbp_client import NBPClient
from schwifty import IBAN
import random
import os
from decimal import Decimal
from django.utils import timezone
from django_otp.decorators import otp_required
from django_otp.plugins.otp_totp.models import TOTPDevice
from django.db.models import Sum
from django.db.models.functions import TruncMonth
from dateutil.relativedelta import relativedelta
from django.http import JsonResponse
from django.http import HttpResponse
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from reportlab.lib.pagesizes import landscape, A4
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont

def home(request):
    return render(request, "backend_brokers/home.html")


def register(request):
    if request.method == "POST":
        form = RegisterForm(request.POST)
        if form.is_valid():
            user = form.save()
            Profile.objects.get_or_create(user=user)
            login(request, user)
            return redirect("two_factor:login")
    else:
        form = RegisterForm()

    return render(request, "backend_brokers/register.html", {"form": form})


def post_login_redirect(request):
    user = request.user
    if not TOTPDevice.objects.filter(user=user, confirmed=True).exists():
        return redirect("two_factor:setup")  # przekierowanie do konfiguracji OTP
    return render(request, "backend_brokers/profile.html")


# @otp_required
@login_required
def profile(request):
    # shows the logged-in user's data
    return render(request, "backend_brokers/profile.html")


@login_required
def profile_edit(request):
    # edits data for User + Profile
    user_form = UserEditForm(instance=request.user)
    profile_form = ProfileEditForm(instance=request.user.profile)

    if request.method == "POST":
        user_form = UserEditForm(request.POST, instance=request.user)
        profile_form = ProfileEditForm(request.POST, instance=request.user.profile)
        if user_form.is_valid() and profile_form.is_valid():
            user_form.save()
            profile_form.save()
            return redirect("profile")

    return render(
        request,
        "backend_brokers/profile_edit.html",
        {
            "uform": user_form,
            "pform": profile_form,
        },
    )


def exchange_rates_view(request):
    nbp = NBPClient()
    nbp.save_to_db()
    rates, effective_date = nbp.rates
    rates_sorted = {k: round(v, 3) for k, v in sorted(rates.items()) if k != "PLN"}
    return render(
        request,
        "backend_brokers/exchange_rates.html",
        {"rates": rates_sorted, "date": effective_date},
    )


@login_required
def wallet(request):
    now = timezone.now()
    wallets = Wallet.objects.filter(user_id=request.user.id, wallet_status="active")
    wallets_count = wallets.count()
    wallets_remaining = request.user.profile.wallet_limit - wallets_count
    transactions_current_month = Transaction.objects.filter(
        user_id=request.user.id,
        visible_to="user",
        created_at__year=now.year,
        created_at__month=now.month,
    )
    transactions_count = transactions_current_month.count()
    transactions_remaining = request.user.profile.transaction_limit - transactions_count
    return render(
        request,
        "backend_brokers/list_of_wallets.html",
        {
            "wallets": wallets,
            "wallets_count": wallets_count,
            "wallets_remaining": wallets_remaining,
            "transactions_current_month": transactions_current_month,
            "transactions_count": transactions_count,
            "transactions_remaining": transactions_remaining,
        },
    )


@login_required
def add_wallet(request):
    wallets_remaining = (
        request.user.profile.wallet_limit
        - Wallet.objects.filter(user_id=request.user.id).count()
    )
    if wallets_remaining <= 0:  # testing if wallet limit not exceeded
        return render(request, "backend_brokers/too_many_wallets.html")
    if request.method == "POST":
        form = AddWalletForm(request.POST)
        if form.is_valid():
            wallet = form.save(commit=False)
            wallet.user_id = request.user.id
            while True:  # makes sure there are no duplicate wallet ids
                wallet_id = str(random.randint(1, 999999999)).zfill(
                    9
                )  # generates random id and adds leading zeros up to 9 digits
                if wallet_id not in Wallet.objects.filter(wallet_id=wallet_id):
                    break
            wallet.iban = IBAN.generate(
                "PL", bank_code="252", account_code=wallet_id
            )  # generates valid IBAN, includes wallet_id
            wallet.wallet_id = wallet_id
            wallet.wallet_status = "active"
            wallet.save()
            return redirect("wallets")
    else:
        form = AddWalletForm()
    return render(request, "backend_brokers/add_wallet.html", {"form": form})


@login_required
def wallet_properies_and_history(request, wallet_id):
    now = timezone.now()
    transactions_current_month = Transaction.objects.filter(
        user_id=request.user.id, created_at__year=now.year, created_at__month=now.month
    )
    transactions_count = transactions_current_month.count()
    transactions_remaining = request.user.profile.transaction_limit - transactions_count
    wallet = get_object_or_404(
        Wallet, id=wallet_id, user=request.user.id, wallet_status="active"
    )
    iban = wallet.iban

    transactions = (
        Transaction.objects.filter(source_iban=iban, visible_to="user")
        | Transaction.objects.filter(destination_iban=iban, visible_to="user")
        | Transaction.objects.filter(destination_iban=iban, visible_to="deposit")
    )  # list of all transactions containing given wallet iban

    transactions = transactions.order_by(
        "-created_at"
    )  # newsest transactions at the top

    return render(
        request,
        "backend_brokers/wallet.html",
        {
            "wallet": wallet,
            "transactions": transactions,
            "transactions_remaining": transactions_remaining,
        },
    )


@login_required
def delete_wallet(
    request, wallet_id
):  # access should be impossible directely (link not active) if there are any funds left. For safety, additional test is performed in case indirect access to this routine.
    wallet = get_object_or_404(Wallet, id=wallet_id, user=request.user.id)

    if wallet.balance != 0:  # the test
        return render(
            request,
            "backend_brokers/wallet_delete_blocked.html",
            {
                "wallet": wallet,
                "message": "Portfel nie może zostać usunięty, ponieważ są na nim środki. Opróżnij konto przed jego usunięciem.",
            },
        )

    if request.method == "POST":
        form = WalletDeleteForm(request.POST)
        if form.is_valid():
            wallet.wallet_status = "deleted"
            wallet.save()
            return redirect("wallets")
    else:
        form = WalletDeleteForm()

    return render(
        request,
        "backend_brokers/wallet_confirm_delete.html",
        {"form": form, "wallet": wallet},
    )


def transfer_funds(request):
    SPREAD_VALUE_PROMO = 0.01
    SPREAD_VALUE_STANDARD = 0.02
    spread_value = SPREAD_VALUE_STANDARD
    now = timezone.now()
    transactions_current_month = Transaction.objects.filter(
        user_id=request.user.id,
        visible_to="user",
        created_at__year=now.year,
        created_at__month=now.month,
    )
    transactions_count = transactions_current_month.count()
    transactions_remaining = request.user.profile.transaction_limit - transactions_count
    if transactions_remaining > 0:
        spread_value = SPREAD_VALUE_PROMO

    if request.method == "POST":
        form = TransferForm(request.user, request.POST)
        if form.is_valid():
            source = form.cleaned_data["source_wallet"]
            master_wallet_buy = Wallet.objects.filter(
                user_id="10", wallet_status="active", currency=source.currency
            )[0]
            print(master_wallet_buy)
            destination = form.cleaned_data["destination_wallet"]
            master_wallet_sell = Wallet.objects.filter(
                user_id="10", wallet_status="active", currency=destination.currency
            )[0]
            destination = form.cleaned_data["destination_wallet"]
            amount = form.cleaned_data["amount"]

            if source == destination:
                form.add_error(None, "Nie możesz przelać środków na to samo konto.")
            elif source.balance < amount:
                form.add_error("amount", "Brak wystarczających środków.")
            elif 0 > amount:
                form.add_error("amount", "Nie można wykonać przelewu na ujemną kwotę.")
            else:
                source_rate = (
                    ExchangeRate.objects.filter(currency=source.currency)
                    .order_by("-date")
                    .first()
                    .rate
                )
                destination_rate = (
                    ExchangeRate.objects.filter(currency=destination.currency)
                    .order_by("-date")
                    .first()
                    .rate
                )
                exchange_rate = (source_rate / destination_rate) * Decimal(
                    1 - spread_value
                )
                converted_amount = amount * Decimal(str(exchange_rate))

                # Balance updates
                source.balance -= amount
                master_wallet_buy.balance += amount
                destination.balance += converted_amount
                master_wallet_sell.balance -= converted_amount
                source.save()
                destination.save()
                master_wallet_sell.save()
                master_wallet_buy.save()

                # Save details to DB - visible to user
                Transaction.objects.create(
                    user=request.user.profile,
                    source_iban=source.iban,
                    from_currency=source.currency,
                    to_currency=destination.currency,
                    destination_iban=destination.iban,
                    amount=amount,
                    rate=exchange_rate,
                    result_amount=converted_amount,
                    visible_to="user",
                )

                # Save details to DB - user to wallet-master transfer
                Transaction.objects.create(
                    user=request.user.profile,
                    source_iban=source.iban,
                    from_currency=source.currency,
                    to_currency=source.currency,
                    destination_iban=master_wallet_buy.iban,
                    amount=amount,
                    rate=Decimal(1),
                    result_amount=amount,
                    visible_to="admin-noprofit",
                )

                # Save details to DB - wallet-master to user transfer
                Transaction.objects.create(
                    user=request.user.profile,
                    source_iban=master_wallet_sell.iban,
                    from_currency=destination.currency,
                    to_currency=destination.currency,
                    destination_iban=destination.iban,
                    amount=converted_amount,
                    rate=Decimal(1),
                    result_amount=converted_amount,
                    visible_to="admin-noprofit",
                )
                # Save details to DB - wallet-master profit (user-source x spread)
                Transaction.objects.create(
                    user=request.user.profile,
                    source_iban=source.iban,
                    from_currency=destination.currency,
                    to_currency=destination.currency,
                    destination_iban=master_wallet_sell.iban,
                    amount=amount
                    * Decimal(
                        str((source_rate / destination_rate) * Decimal(spread_value))
                    ),
                    rate=exchange_rate,
                    result_amount=amount
                    * Decimal(
                        str((source_rate / destination_rate) * Decimal(spread_value))
                    ),
                    visible_to="admin-profit",
                )

                return redirect("wallets")
    else:
        form = TransferForm(request.user)

    return render(request, "backend_brokers/transfer_form.html", {"form": form})


@login_required
def deposit(request):
    if request.method == "POST":
        form = DepositForm(request.user, request.POST)
        if form.is_valid():
            wallet = form.cleaned_data["wallet"]
            amount = form.cleaned_data["amount"]

            wallet.balance += amount
            wallet.save()

            Transaction.objects.create(
                user=request.user.profile,
                source_iban=wallet.iban,
                from_currency=wallet.currency,
                to_currency=wallet.currency,
                destination_iban=wallet.iban,
                amount=amount,
                rate=Decimal(1),
                result_amount=amount,
                visible_to="deposit",
            )

            return redirect("wallets")
    else:
        form = DepositForm(request.user)

    return render(request, "backend_brokers/deposit.html", {"form": form})

@login_required
def stats_dashboard(request):
    user_profile = None
    error_message = None

    try:
        user_profile = request.user.profile
    except Exception:
        error_message = "Wystąpił nieoczekiwany błąd podczas ładowania profilu."

    months = []
    totals = []
    profits = []
    transactions_agg_list = []
    profit_agg_list = []

    if user_profile:
        now = datetime.now()
        months_range = 12 if request.user.is_superuser else 6
        start_month = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0) - relativedelta(months=months_range - 1)

        if request.user.is_superuser:
            trans_qs = (
                Transaction.objects
                .filter(visible_to="user", created_at__gte=start_month)
                .annotate(month=TruncMonth('created_at'))
                .order_by('month')
            )

            profit_qs = (
                Transaction.objects
                .filter(visible_to="admin-profit", created_at__gte=start_month)
                .annotate(month=TruncMonth('created_at'))
                .order_by('month')
            )
        else:
            trans_qs = (
                Transaction.objects
                .filter(user=user_profile, visible_to="user", created_at__gte=start_month)
                .annotate(month=TruncMonth('created_at'))
                .order_by('month')
            )
            profit_qs = []

        date_format = '%b %Y'
        month_data = OrderedDict()
        profit_data = OrderedDict()

        current = start_month
        for i in range(months_range):
            label = current.strftime(date_format)
            month_data[label] = 0.0
            profit_data[label] = 0.0
            current += relativedelta(months=1)

        for t in trans_qs:
            month_key = t.month.strftime(date_format)

            amount_to = Decimal(t.result_amount or 0)
            to_currency = t.to_currency.upper()
            amount_to_pln = amount_to

            if to_currency != "PLN":
                rate_to = ExchangeRate.objects.filter(currency=to_currency).order_by('-date').first()
                if rate_to:
                    amount_to_pln = amount_to * Decimal(rate_to.rate)

            month_data[month_key] += float(amount_to_pln)

        if request.user.is_superuser:
            for p in profit_qs:
                month_key = p.month.strftime(date_format)
                profit_amount = Decimal(p.amount or 0)
                currency = p.to_currency.upper()

                if currency != "PLN":
                    rate = ExchangeRate.objects.filter(currency=currency).order_by('-date').first()
                    if rate:
                        profit_amount *= Decimal(rate.rate)

                profit_data[month_key] += float(profit_amount)
        else:
            for t in trans_qs:
                month_key = t.month.strftime(date_format)

                amount_from = Decimal(t.amount or 0)
                amount_to = Decimal(t.result_amount or 0)

                from_currency = t.from_currency.upper()
                to_currency = t.to_currency.upper()

                amount_from_pln = amount_from
                amount_to_pln = amount_to

                if from_currency != "PLN":
                    rate_from = ExchangeRate.objects.filter(currency=from_currency).order_by('-date').first()
                    if rate_from:
                        amount_from_pln = amount_from * Decimal(rate_from.rate)

                if to_currency != "PLN":
                    rate_to = ExchangeRate.objects.filter(currency=to_currency).order_by('-date').first()
                    if rate_to:
                        amount_to_pln = amount_to * Decimal(rate_to.rate)

                profit_data[month_key] += float(amount_to_pln - amount_from_pln)

        transactions_agg_list = [
            {'month': datetime.strptime(month, date_format), 'total': total}
            for month, total in month_data.items()
        ]

        profit_agg_list = [
            {'month': datetime.strptime(month, date_format), 'profit': profit}
            for month, profit in profit_data.items()
        ]

        months = list(month_data.keys())
        totals = [round(v, 2) for v in month_data.values()]
        profits = [round(v, 2) for v in profit_data.values()]
        total_sum = round(sum(totals), 2)
        total_profit = round(sum(profits), 2)

    context = {
        'months_json': months,
        'totals_json': totals,
        'transactions_agg': transactions_agg_list,
        'profit_agg': profit_agg_list,
        'error_message': error_message,
        'total_sum': total_sum,
        'total_profit': total_profit,
    }

    return render(request, 'backend_brokers/stats_dashboard.html', context)

def estimate_exchange(request):
    if request.method != "GET":
        return JsonResponse({"error": "Invalid method"}, status=400)

    source_wallet_id = request.GET.get("source_wallet")
    destination_wallet_id = request.GET.get("destination_wallet")
    amount = request.GET.get("amount")

    if not source_wallet_id or not destination_wallet_id or not amount:
        return JsonResponse({"error": "Missing params"}, status=400)

    try:
        source_wallet = Wallet.objects.get(id=source_wallet_id)
        destination_wallet = Wallet.objects.get(id=destination_wallet_id)
        amount = Decimal(amount)
    except:
        return JsonResponse({"error": "Invalid parameters"}, status=400)

    source_rate = ExchangeRate.objects.filter(currency=source_wallet.currency).order_by("-date").first().rate
    destination_rate = ExchangeRate.objects.filter(currency=destination_wallet.currency).order_by("-date").first().rate

    SPREAD_VALUE_PROMO = Decimal("0.01")
    SPREAD_VALUE_STANDARD = Decimal("0.02")

    now = timezone.now()
    transactions_current_month = Transaction.objects.filter(
        user_id=request.user.id,
        visible_to="user",
        created_at__year=now.year,
        created_at__month=now.month,
    )
    transactions_count = transactions_current_month.count()

    spread_value = SPREAD_VALUE_PROMO if transactions_count < request.user.profile.transaction_limit else SPREAD_VALUE_STANDARD

    exchange_rate = (source_rate / destination_rate) * (Decimal(1) - spread_value)

    converted_amount = amount * exchange_rate

    return JsonResponse({
        "result": f"{converted_amount:.2f}",
        "rate": f"{exchange_rate:.4f}",
        "spread": str(spread_value)
    })

def wallet_to_pln(wallet):
    """
    Zwraca saldo walletu przeliczone na PLN na podstawie ostatniego dostępnego kursu.
    """
    if wallet.currency == "PLN":
        return wallet.balance

    rate = ExchangeRate.objects.filter(currency=wallet.currency).order_by("-date").first()
    if not rate:
        return Decimal(0)

    try:
        return wallet.balance * Decimal(rate.rate)
    except:
        return Decimal(0)

def total_user_balance_pln(profile):
    """
    Sumuje wszystkie wallety użytkownika i zwraca saldo w PLN.
    """
    wallets = Wallet.objects.filter(user=profile)
    return sum(wallet_to_pln(w) for w in wallets)

def user_transaction_stats(profile):
    """
    Zwraca tuple: (wszystkie transakcje, transakcje z ostatnich 30 dni)
    """
    total_tx = Transaction.objects.filter(user=profile).count()
    last_month = timezone.now() - timedelta(days=30)
    recent_tx = Transaction.objects.filter(user=profile, created_at__gte=last_month).count()
    return total_tx, recent_tx

def generate_user_report(request):
    if not request.user.is_superuser:
        return HttpResponse("Brak dostępu", status=403)

    font_path = os.path.join(
    settings.BASE_DIR,
    "apps",
    "backend_brokers",
    "static",
    "backend_brokers",
    "fonts",
    "DejaVuSans.ttf"
    )   
    pdfmetrics.registerFont(TTFont("DejaVu", font_path))

    # Tworzymy odpowiedź PDF
    response = HttpResponse(content_type='application/pdf')
    response['Content-Disposition'] = 'attachment; filename="raport_uzytkownicy.pdf"'

    # PDF w orientacji poziomej A4
    doc = SimpleDocTemplate(
        response,
        pagesize=landscape(A4),
        rightMargin=20,
        leftMargin=20,
        topMargin=20,
        bottomMargin=20
    )

    styles = getSampleStyleSheet()
    styles['Normal'].fontName = "DejaVu"
    styles['Title'].fontName = "DejaVu"

    elements = []

    # Tytuł
    title = Paragraph("Raport użytkowników – " + datetime.now().strftime("%Y-%m-%d"), styles['Title'])
    elements.append(title)
    elements.append(Spacer(1, 12))

    # Nagłówki tabeli
    data = [
        ["Username", "Email", "Typ konta", "Saldo walletów", "Transakcji razem", "Transakcji w ostatnim miesiącu"]
    ]

    all_profiles = Profile.objects.all()

    for profile in all_profiles:
        total_balance = total_user_balance_pln(profile)
        total_tx, recent_tx = user_transaction_stats(profile)


        data.append([
            profile.user.username,
            profile.user.email,
            "Biznesowe" if profile.account_type == "business" else "Osobiste",
            f"{total_balance:.2f} zł",
            total_tx,
            recent_tx
        ])

    # Tabela z automatyczną szerokością kolumn
    col_widths = [100, 180, 100, 120, 120, 150]  # dopasowane do poziomego A4

    table = Table(data, colWidths=col_widths, repeatRows=1)

    table.setStyle(TableStyle([
        ('FONT', (0, 0), (-1, -1), 'DejaVu', 9),

        ('BACKGROUND', (0,0), (-1,0), colors.lightgrey),
        ('TEXTCOLOR', (0,0), (-1,0), colors.black),

        ('ALIGN', (0,0), (-1,-1), 'CENTER'),
        ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),

        ('GRID', (0,0), (-1,-1), 0.5, colors.grey),
        ('BOTTOMPADDING', (0,0), (-1,0), 8),
        ('TOPPADDING', (0,0), (-1,0), 8),
    ]))

    elements.append(table)

    doc.build(elements)
    return response