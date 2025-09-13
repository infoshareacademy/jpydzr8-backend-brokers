import decimal

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login
from django.contrib.auth.decorators import login_required
from .forms import (
    RegisterForm,
    UserEditForm,
    ProfileEditForm,
    AddWalletForm,
    WalletDeleteForm,
    TransferForm,
    DepositForm
)
from .models import Profile, Wallet, Transaction, ExchangeRate
from apps.backend_brokers.nbp_client import NBPClient
from schwifty import IBAN
import random
from decimal import Decimal
from django.utils import timezone


def home(request):
    return render(request, "backend_brokers/home.html")


def register(request):
    if request.method == "POST":
        form = RegisterForm(request.POST)
        if form.is_valid():
            user = form.save()
            Profile.objects.get_or_create(user=user)
            login(request, user)
            return redirect("profile")
    else:
        form = RegisterForm()

    return render(request, "backend_brokers/register.html", {"form": form})


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
        user_id=request.user.id, created_at__year=now.year, created_at__month=now.month
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

    transactions = Transaction.objects.filter(
        source_iban=iban, visible_to="user"
    ) | Transaction.objects.filter(
        destination_iban=iban, visible_to="user"
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
        user_id=request.user.id, created_at__year=now.year, created_at__month=now.month
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
                visible_to="user",
            )

            return redirect("wallets")
    else:
        form = DepositForm(request.user)

    return render(request, "backend_brokers/deposit.html", {"form": form})

