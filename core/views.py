from django.http import JsonResponse
from django.shortcuts import render

from noticias.views import home as home_noticias


def home(request):
    """A home é a das notícias; o nome `core:home` continua valendo."""
    return home_noticias(request)


def saude(request):
    return JsonResponse({"status": "ok"})


def lab_spike(request):
    """Página de prova do STAR-19: WebGL, Rive e diagrama ao scroll (laboratório)."""
    return render(request, "core/lab_spike.html")
