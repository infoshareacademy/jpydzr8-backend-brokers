from django.urls import path
from apps.backend_brokers import views
from django.contrib.auth.views import LoginView, LogoutView

urlpatterns = [
    path("", views.home, name="home"),
    path("register/", views.register, name="register"),
    path(
        "login/",
        LoginView.as_view(template_name="backend_brokers/login.html"),
        name="login",
    ),
    path("logout/", LogoutView.as_view(next_page="login"), name="logout"),
    path("profile/", views.profile, name="profile"),
    path("profile/edit/", views.profile_edit, name="profile_edit"),
    path("rates/", views.exchange_rates_view, name="exchange_rates"),
    path("wallets/", views.wallet, name="wallets"),
    path("wallet/add/", views.add_wallet, name="add_wallet"),
    path(
        "wallet/<int:wallet_id>/",
        views.wallet_properies_and_history,
        name="wallet_transactions",
    ),
    path("wallet/<int:wallet_id>/delete/", views.delete_wallet, name="delete_wallet"),
    path("wallets/transfer", views.transfer_funds, name="transfer_funds"),
    path("wallet/deposit/", views.deposit, name="deposit")
]
