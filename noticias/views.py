from django.shortcuts import get_object_or_404, render

from . import servicos
from .models import Tema


def home(request):
    destaque = servicos.manchete()
    recentes = servicos.futuro_hoje(destaque)
    contexto = {
        "manchete": destaque,
        "futuro_hoje": recentes,
        "ultimas": servicos.ultimas([destaque, *recentes], request.GET.get("pagina")),
        "numeros": servicos.numeros_destaque(),
    }
    return render(request, "noticias/home.html", contexto)


def tema(request, slug):
    tema_atual = get_object_or_404(Tema, slug=slug)
    contexto = {
        "tema": tema_atual,
        "tema_atual": tema_atual,
        "artigos": servicos.artigos_do_tema(tema_atual, request.GET.get("pagina")),
    }
    return render(request, "noticias/tema.html", contexto)


def artigo(request, slug):
    publicado = get_object_or_404(servicos.artigos_publicados(), slug=slug)
    corpo, indice = servicos.processar_corpo(publicado.corpo)
    fontes = list(publicado.fontes.all())
    contexto = {
        "artigo": publicado,
        "tema_atual": publicado.tema_principal,
        "corpo": corpo,
        "indice": indice,
        "fontes": fontes,
        "relacionados": servicos.relacionados(publicado),
    }
    return render(request, "noticias/artigo.html", contexto)
