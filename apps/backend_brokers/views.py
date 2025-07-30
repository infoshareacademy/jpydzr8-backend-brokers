from django.shortcuts import render


def homepage(request):
    return render(request, "backend_brokers/homepage.html")
