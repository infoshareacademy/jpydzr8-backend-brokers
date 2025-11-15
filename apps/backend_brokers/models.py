from email.policy import default
from random import choices

from django.db import models
from django.contrib.auth.models import User
from django.utils.translation import gettext_lazy as _

ACCOUNT_CHOICES = (("personal", "Personal"), ("business", "Business"))


def _limits_for(account_type: str) -> tuple[int, int]:
    """
    Returns tuple (transaction_limit, wallet_limit) based on account type.
    personal -> (10, 5)
    business -> (50, 10)
    """
    return (50, 10) if account_type == "business" else (10, 5)


class Profile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)

    # user data
    phone_number = models.CharField(_("Telefon"), max_length=20, blank=True)
    address = models.CharField(_("Adres"), max_length=255, blank=True)
    account_type = models.CharField(
        _("Typ konta"), max_length=20, choices=ACCOUNT_CHOICES, default="personal"
    )
    date_of_birth = models.DateField(_("Data urodzenia"), null=True, blank=True)

    # limits and counter (for transactions)
    transaction_limit = models.PositiveIntegerField(default=10)
    wallet_limit = models.PositiveIntegerField(default=5)

    # meta
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def save(self, *args, **kwargs):
        if self.account_type == "personal":
            self.transaction_limit = 10
            self.wallet_limit = 5
        elif self.account_type == "business":
            self.transaction_limit = 100
            self.wallet_limit = 50

        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.user.first_name} {self.user.last_name} ({self.user.username})"


class Wallet(models.Model):
    SELECTABLE_CURRENCIES = [
        ("PLN", _("polski nowy złoty")),
        ("EUR", _("euro")),
        ("USD", _("dolar amerykański")),
        ("AUD", _("dolar australijski")),
        ("BGN", _("lew (Bułgaria)")),
        ("BRL", _("real (Brazylia)")),
        ("CAD", _("dolar kanadyjski")),
        ("CHF", _("frank szwajcarski")),
        ("CLP", _("peso chilijskie")),
        ("CNY", _("yuan renminbi (Chiny)")),
        ("CZK", _("korona czeska")),
        ("DKK", _("korona duńska")),
        ("GBP", _("funt szterling")),
        ("HKD", _("dolar Hongkongu")),
        ("HUF", _("forint (Węgry)")),
        ("IDR", _("rupia indonezyjska")),
        ("ILS", _("nowy izraelski szekel")),
        ("INR", _("rupia indyjska")),
        ("ISK", _("korona islandzka")),
        ("JPY", _("jen (Japonia)")),
        ("KRW", _("won południowokoreański")),
        ("MXN", _("peso meksykańskie")),
        ("MYR", _("ringgit (Malezja)")),
        ("NOK", _("korona norweska")),
        ("NZD", _("dolar nowozelandzki")),
        ("PHP", _("peso filipińskie")),
        ("RON", _("lej rumuński")),
        ("SEK", _("korona szwedzka")),
        ("SGD", _("dolar singapurski")),
        ("THB", _("bat (Tajlandia)")),
        ("TRY", _("lira turecka")),
        ("UAH", _("hrywna (Ukraina)")),
        ("XDR", _("SDR (MFW)")),
        ("ZAR", _("rand (Republika Południowej Afryki)")),
    ]  # Added to automate drop-down lists
    user = models.ForeignKey(
        "Profile",
        verbose_name=_("Użytkownik"),
        on_delete=models.SET_DEFAULT,
        related_name="wallets",
        default="deleted_user",
    )
    wallet_id = models.CharField(_("Portfel"), max_length=50, unique=True)
    currency = models.CharField(_("Waluta"), max_length=10, choices=SELECTABLE_CURRENCIES)
    iban = models.CharField(_("IBAN"),max_length=34, unique=True)
    balance = models.DecimalField(_("Stan konta"), max_digits=12, decimal_places=2, default=0.00)
    wallet_status = models.CharField(_("Status portfela"), max_length=50, default="active")

    def __str__(self):
        return "{} {} ({} {})".format(_("Portfel"), self.wallet_id, self.balance, self.currency)


class Transaction(models.Model):
    user = models.ForeignKey(
        Profile, on_delete=models.CASCADE, related_name="transactions"
    )
    source_iban = models.CharField(max_length=34, default="test")
    from_currency = models.CharField(max_length=10)  # np. "USD"
    to_currency = models.CharField(max_length=10)  # np. "PLN"
    destination_iban = models.CharField(max_length=34, default="test")

    # transaction data
    amount = models.DecimalField(
        max_digits=12, decimal_places=2
    )  # amount in source currency
    rate = models.DecimalField(max_digits=10, decimal_places=4)  # exchange rate

    # exchange result, form now its editable, need to turn off later
    result_amount = models.DecimalField(max_digits=12, decimal_places=2, editable=True)
    created_at = models.DateTimeField(auto_now_add=True)
    visible_to = models.CharField(max_length=32)  # np. "admin", "user"

    def __str__(self):
        return f"{self.user.user.username}: {self.amount} {self.from_currency} → {self.to_currency} @ {self.rate}"


class ExchangeRate(models.Model):
    date = models.DateField(_("Data"))
    currency = models.CharField(_("Waluta"), max_length=3)
    rate = models.DecimalField(_("Kurs wymiany"), max_digits=12, decimal_places=4)

    class Meta:
        unique_together = ("date", "currency")
        ordering = ["-date", "currency"]

    def __str__(self):
        return f"{self.date} - {self.currency}: {self.rate}"
