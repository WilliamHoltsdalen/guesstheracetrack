from django.shortcuts import render


def landing_page(request):
    return render(request, "landing_page/landing_page.html")


def privacy_policy(request):
    return render(request, "landing_page/privacy_policy.html")
