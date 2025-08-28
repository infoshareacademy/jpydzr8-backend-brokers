from django.shortcuts import render, redirect
from django.contrib.auth import login
from django.contrib.auth.decorators import login_required
from .forms import RegisterForm, UserEditForm, ProfileEditForm
from .models import Profile
from apps.backend_brokers.nbp_client import NBPClient


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
    rates = nbp.rates
    rates_sorted = {k: round(v, 3) for k, v in sorted(rates.items()) if k != "PLN"}
    return render(request, "backend_brokers/exchange_rates.html", {"rates": rates_sorted})
