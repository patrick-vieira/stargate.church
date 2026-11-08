from django.http import JsonResponse
from django.shortcuts import get_object_or_404, render

from noticias.views import home as home_noticias

from .imersivo import libs_opcionais
from .models import Ato, PostImersivo

# Efeito de página inteira → template próprio (STAR-41, STAR-42).
TEMPLATES_ATMOSFERA = {
    Ato.Efeito.ATMOSFERA: "core/imersivo_maquina_fria.html",
    Ato.Efeito.ATMOSFERA_GUERRA: "core/imersivo_guerra_maquinas.html",
    Ato.Efeito.ATMOSFERA_ESCOLHAS: "core/imersivo_escolhas.html",
}


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
    atos = post.atos.all()
    contexto = {
        "post": post,
        "atos": atos,
        "libs": libs_opcionais(),
        "publicados": set(PostImersivo.publicados().values_list("slug", flat=True)),
    }
    for a in atos:
        if a.efeito in TEMPLATES_ATMOSFERA:
            return render(request, TEMPLATES_ATMOSFERA[a.efeito], contexto)
    return render(request, "core/imersivo.html", contexto)
