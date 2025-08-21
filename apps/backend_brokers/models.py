from django.db import models
from django.contrib.auth.models import User

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
    phone_number = models.CharField(max_length=20, blank=True)
    address = models.CharField(max_length=255, blank=True)
    account_type = models.CharField(
        max_length=20, choices=ACCOUNT_CHOICES, default="personal"
    )
    date_of_birth = models.DateField(null=True, blank=True)

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
