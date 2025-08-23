from django.contrib import admin
from .models import Profile, UserData, Wallet


@admin.register(Profile)
class ProfileAdmin(admin.ModelAdmin):
    list_display = ("user", "account_type", "phone_number")
    search_fields = ("user__username", "user__email")

class WalletInline(admin.TabularInline):
    model = Wallet
    extra = 0

class UserDataAdmin(admin.ModelAdmin):
    inlines = [WalletInline]
    list_display = ['email', 'first_name', 'last_name', 'account_type']

admin.site.register(UserData, UserDataAdmin)