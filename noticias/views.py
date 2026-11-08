from django.contrib import messages
from django.contrib.auth.decorators import login_required
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


def _render_artigo(request, publicado, form, status=200):
    corpo, indice = servicos.processar_corpo(publicado.corpo)
    fontes = list(publicado.fontes.filter(confiavel=True))
    teto = tecto.limite(UsoDiario.COMENTARIO)
    contexto = {
        "artigo": publicado,
        "tema_atual": publicado.tema_principal,
        "corpo": corpo,
        "indice": indice,
        "fontes": fontes,
        "relacionados": servicos.relacionados(publicado),
        "form_comentario": form,
        "comentarios_teto": teto,
        "comentarios_restantes": tecto.restante(request.user, UsoDiario.COMENTARIO),
    }
    return render(request, "noticias/artigo.html", contexto, status=status)


def artigo(request, slug):
    publicado = get_object_or_404(servicos.artigos_publicados(), slug=slug)
    return _render_artigo(request, publicado, ComentarioForm())


@require_POST
@login_required
def comentar(request, slug):
    publicado = get_object_or_404(servicos.artigos_publicados(), slug=slug)
    form = ComentarioForm(request.POST)
    if not form.is_valid():
        # Re-renderiza o artigo com o form e os erros: sem redirect, sem perder o texto.
        return _render_artigo(request, publicado, form, status=400)
    # O tecto só gasta depois de o form validar.
    if not tecto.consumir(request.user, UsoDiario.COMENTARIO):
        messages.error(request, "Limite diário de comentários atingido. Volte amanhã.")
        return _render_artigo(request, publicado, form, status=429)
    Comentario.objects.create(
        artigo=publicado,
        autor=request.user,
        nome=form.cleaned_data["nome"],
        texto=form.cleaned_data["texto"],
    )
    messages.success(request, "Recebemos o seu comentário. Ele aparece após a revisão.")
    return redirect(f"{publicado.get_absolute_url()}#comentarios")
