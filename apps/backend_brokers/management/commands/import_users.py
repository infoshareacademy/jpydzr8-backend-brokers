import json
from datetime import datetime
from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from apps.backend_brokers.models import Profile, Wallet

class Command(BaseCommand):
    help = "Load users and wallets from JSON files into Profile and Wallet models"

    def add_arguments(self, parser):
        parser.add_argument(
            "--users",
            type=str,
            help="Path to users JSON file",
            default="users_data.json"
        )
        parser.add_argument(
            "--wallets",
            type=str,
            help="Path to wallets JSON file",
            default="wallets.json"
        )

    def handle(self, *args, **options):
        users_file = options["users"]
        wallets_file = options["wallets"]

        self.stdout.write(f"Loading users from {users_file}...")
        with open(users_file, encoding="utf-8") as f:
            users_data = json.load(f)

        for email, data in users_data.items():
            user, _ = User.objects.get_or_create(
                username=email,
                defaults={
                    "first_name": data.get("first_name", ""),
                    "last_name": data.get("last_name", ""),
                    "email": email
                }
            )

            dob_str = data.get("date of birth") or data.get("date_of_birth")
            dob = None
            if dob_str:
                try:
                    dob = datetime.strptime(dob_str, "%d-%m-%Y").date()
                except ValueError:
                    self.stdout.write(self.style.WARNING(f"Invalid date for {email}: {dob_str}"))

            profile, _ = Profile.objects.get_or_create(
                user=user,
                defaults={
                    "phone_number": data.get("phone_number", ""),
                    "address": data.get("address", ""),
                    "account_type": data.get("account_type", "personal"),
                    "date_of_birth": dob
                }
            )

        self.stdout.write(self.style.SUCCESS("Users loaded successfully!"))

        self.stdout.write(f"Loading wallets from {wallets_file}...")
        with open(wallets_file, encoding="utf-8") as f:
            wallets_data = json.load(f)

        for user_key, wallets in wallets_data.get("users", {}).items():
            try:
                profile = Profile.objects.get(user__email=user_key)
            except Profile.DoesNotExist:
                self.stdout.write(self.style.WARNING(f"Profile not found for: {user_key}"))
                continue

            for w in wallets:
                Wallet.objects.get_or_create(
                    user=profile,
                    wallet_id=w.get("wallet_id"),
                    defaults={
                        "currency": w.get("currency", "PLN"),
                        "iban": w.get("iban", ""),
                        "balance": w.get("balance", 0)
                    }
                )

        self.stdout.write(self.style.SUCCESS("Wallets loaded successfully!"))
