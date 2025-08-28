from django.contrib import admin
from .models import Profile, Wallet, Transaction


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
    list_display = ("user", "from_currency", "to_currency", "amount", "rate", "result_amount", "created_at")
    search_fields = ("user__user__username", "from_currency", "to_currency")
    list_filter = ("created_at", "from_currency", "to_currency")
