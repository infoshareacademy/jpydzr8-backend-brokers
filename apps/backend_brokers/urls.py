from django.urls import path
from apps.backend_brokers import views

urlpatterns = [
    path("", views.home, name="home"),
]
