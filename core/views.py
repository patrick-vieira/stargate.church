from django.http import JsonResponse
from django.shortcuts import get_object_or_404, render

from noticias.views import home as home_noticias

from .imersivo import libs_opcionais
from .models import Ato, PostImersivo

# Efeito de página inteira → template próprio (STAR-41, STAR-42).
TEMPLATES_ATMOSFERA = {
    Ato.Efeito.ATMOSFERA: "core/imersivo_maquina_fria.html",
    Ato.Efeito.ATMOSFERA_GUERRA: "core/imersivo_guerra_maquinas.html",
    Ato.Efeito.ATMOSFERA_SER_HUMANO: "core/imersivo_ser_humano.html",
    Ato.Efeito.ATMOSFERA_ESCOLHAS: "core/imersivo_escolhas.html",
    Ato.Efeito.ATMOSFERA_IA_AFETIVA: "core/imersivo_ia_afetiva.html",
    Ato.Efeito.ATMOSFERA_LEIS_ROBOS_LIVROS: "core/imersivo_leis_robos_livros.html",
}


# Era do narrador (0 1920, 1 1960, 2 1980, 3 1990, 4 2000, 5 2010, 6 2020) por post.
# Posts fora da tabela ficam na era 6 (creme Stargate).
ERA_NARRADOR = {
    "a-maquina-fria": 1,
    "efeitos-maquina-fria-provisorio": 1,
    "o-medo-da-guerra-das-maquinas": 2,
    "escolhas-da-maquina": 5,
    "o-que-e-ser-humano": 3,
    "a-ia-afetiva": 5,
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
        "narrador_era": ERA_NARRADOR.get(post.slug, 6),
    }
    for a in atos:
        if a.efeito in TEMPLATES_ATMOSFERA:
            return render(request, TEMPLATES_ATMOSFERA[a.efeito], contexto)
    return render(request, "core/imersivo.html", contexto)
