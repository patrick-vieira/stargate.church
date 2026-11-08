from django.http import JsonResponse
from django.shortcuts import get_object_or_404, render

from noticias.views import home as home_noticias

from .imersivo import libs_opcionais
from .models import PostImersivo


def home(request):
    """A home é a das notícias; o nome `core:home` continua valendo."""
    return home_noticias(request)


def saude(request):
    return JsonResponse({"status": "ok"})


def lab_spike(request):
    """Página de prova do STAR-19: WebGL, Rive e diagrama ao scroll (laboratório)."""
    return render(request, "core/lab_spike.html")


def imersivo(request, slug):
    """Post imersivo: atos em dados, efeitos pelo motor JS."""
    post = get_object_or_404(PostImersivo.publicados(), slug=slug)
    contexto = {"post": post, "atos": post.atos.all(), "libs": libs_opcionais()}
    return render(request, "core/imersivo.html", contexto)
