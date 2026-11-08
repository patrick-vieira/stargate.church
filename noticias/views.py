from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.http import HttpResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_POST

from leitores import tecto
from leitores.models import UsoDiario

from . import servicos
from .forms import ComentarioForm
from .models import Comentario, Tema


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
    fontes = list(publicado.fontes.filter(confiavel=True))
    contexto = {
        "artigo": publicado,
        "tema_atual": publicado.tema_principal,
        "corpo": corpo,
        "indice": indice,
        "fontes": fontes,
        "relacionados": servicos.relacionados(publicado),
    }
    return render(request, "noticias/artigo.html", contexto)


@require_POST
@login_required
def comentar(request, slug):
    publicado = get_object_or_404(servicos.artigos_publicados(), slug=slug)
    form = ComentarioForm(request.POST)
    if not form.is_valid():
        messages.error(request, "Confira o nome e o comentário.")
        return redirect(publicado.get_absolute_url())
    # O tecto só gasta depois de o form validar.
    if not tecto.consumir(request.user, UsoDiario.COMENTARIO):
        return HttpResponse("Limite diário de comentários atingido.", status=429)
    Comentario.objects.create(
        artigo=publicado,
        autor=request.user,
        nome=form.cleaned_data["nome"],
        texto=form.cleaned_data["texto"],
    )
    messages.success(request, "Recebemos o seu comentário. Ele aparece após a revisão.")
    return redirect(publicado.get_absolute_url())
