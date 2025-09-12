from django.contrib import admin
from .models import Profile, Wallet, Transaction, ExchangeRate


class WalletInline(admin.TabularInline):
    model = Wallet
    extra = 0


@admin.register(Profile)
class ProfileAdmin(admin.ModelAdmin):
    list_display = ("user", "account_type", "phone_number")
    search_fields = ("user__username", "user__email")
    inlines = [WalletInline]


@admin.register(Transaction)
class TransactionAdmin(admin.ModelAdmin):
    list_display = (
        "user",
        "from_currency",
        "to_currency",
        "amount",
        "rate",
        "result_amount",
        "created_at",
        "visible_to",
    )
    search_fields = ("user__user__username", "from_currency", "to_currency")
    list_filter = ("created_at", "from_currency", "to_currency", "visible_to")


@admin.register(ExchangeRate)
class ExchangeRateAdmin(admin.ModelAdmin):
    list_display = ("date", "currency", "rate")
    list_filter = ("date", "currency")
    search_fields = ("currency",)


@admin.register(Wallet)
class WalletAdmin(admin.ModelAdmin):
    list_display = (
        "user",
        "wallet_id",
        "currency",
        "balance",
        "wallet_status",
    )
    search_fields = ("user__user__username",)
    list_filter = ("user", "currency", "wallet_status")
