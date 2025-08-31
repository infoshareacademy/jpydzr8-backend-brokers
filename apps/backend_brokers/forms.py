from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User
from .models import Profile, Wallet


class RegisterForm(UserCreationForm):
    email = forms.EmailField(required=True)

    class Meta:
        model = User
        fields = [
            "username",
            "email",
            "first_name",
            "last_name",
            "password1",
            "password2",
        ]

    def save(self, commit=True):
        user = super().save(commit=False)
        user.email = self.cleaned_data["email"]
        user.first_name = self.cleaned_data["first_name"]
        user.last_name = self.cleaned_data["last_name"]

        if commit:
            user.save()
            Profile.objects.create(user=user)

        return user

    def clean_email(self):
        email = self.cleaned_data["email"].lower().strip()
        if User.objects.filter(email=email).exists():
            raise forms.ValidationError("Ten email jest już użyty.")
        return email


class UserEditForm(forms.ModelForm):
    class Meta:
        model = User
        fields = ["first_name", "last_name", "email"]
        labels = {
            "first_name": "Imię",
            "last_name": "Nazwisko",
            "email": "Email",
        }

    def clean_email(self):
        email = self.cleaned_data["email"].lower().strip()
        qs = User.objects.filter(email=email).exclude(pk=self.instance.pk)
        if qs.exists():
            raise forms.ValidationError("Ten email jest już użyty.")
        return email


class ProfileEditForm(forms.ModelForm):
    class Meta:
        model = Profile
        fields = ["phone_number", "address", "account_type", "date_of_birth"]
        labels = {
            "phone_number": "Telefon",
            "address": "Adres",
            "account_type": "Typ konta",
            "date_of_birth": "Data urodzenia",
        }
        widgets = {
            "date_of_birth": forms.DateInput(attrs={"type": "date"}),
        }


class AddWalletForm(forms.ModelForm):
    class Meta:
        model = Wallet
        fields = ["currency"]
        widgets = {
            "Proszę wybrać walutę": forms.Select(attrs={"class": "form-control"}),
        }


class WalletDeleteForm(forms.Form):
    confirmation = forms.CharField(label="Potwierdź usunięcie", max_length=10)

    def clean_confirmation(self):
        value = self.cleaned_data["confirmation"]
        if value.strip().lower() != "usuń":
            raise forms.ValidationError("Aby usunąć portfel, wpisz dokładnie: 'usuń'")
        return value


class TransferForm(forms.Form):
    source_wallet = forms.ModelChoiceField(
        queryset=Wallet.objects.none(), label="Konto źródłowe"
    )
    destination_wallet = forms.ModelChoiceField(
        queryset=Wallet.objects.none(), label="Konto docelowe"
    )
    amount = forms.DecimalField(max_digits=10, decimal_places=4, label="Kwota")

    def __init__(self, user, *args, **kwargs):
        super().__init__(*args, **kwargs)
        user_wallets = Wallet.objects.filter(user_id=user.id)
        self.fields["source_wallet"].queryset = user_wallets
        self.fields["destination_wallet"].queryset = user_wallets
