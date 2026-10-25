"""Regras de leitura do portal: o que aparece na home e na página de artigo."""

import re
from html import unescape

from django.core.paginator import Paginator
from django.db.models import F
from django.utils import timezone
from django.utils.html import strip_tags
from django.utils.safestring import mark_safe
from django.utils.text import slugify

from .models import Artigo, NumeroDestaque, Tema

TOTAL_FUTURO_HOJE = 4
POR_PAGINA_ULTIMAS = 6
TOTAL_RELACIONADOS = 3
TOTAL_NUMEROS = 4

_H2 = re.compile(r"<h2(?P<attrs>[^>]*)>(?P<texto>.*?)</h2>", re.IGNORECASE | re.DOTALL)
_ID = re.compile(r"""\sid\s*=\s*["'](?P<id>[^"']+)["']""", re.IGNORECASE)


def hoje():
    return timezone.localdate()


def temas_do_menu():
    """Temas na ordem em que foram cadastrados (a ordem do menu)."""
    return list(Tema.objects.order_by("pk"))


def artigos_publicados():
    """Só artigos publicados, do mais recente para o mais antigo."""
    return (
        Artigo.objects.filter(estado=Artigo.Estado.PUBLICADO)
        .select_related("autor")
        .prefetch_related("temas")
        .order_by(F("publicado_em").desc(nulls_last=True), "-pk")
    )


def manchete():
    """O destaque publicado mais recente; sem destaque, o artigo mais recente."""
    publicados = artigos_publicados()
    return publicados.filter(destaque=True).first() or publicados.first()


def futuro_hoje(manchete_atual, limite=TOTAL_FUTURO_HOJE):
    """Os artigos mais recentes, sem a manchete."""
    recentes = artigos_publicados()
    if manchete_atual:
        recentes = recentes.exclude(pk=manchete_atual.pk)
    return list(recentes[:limite])


def ultimas(excluidos, pagina, por_pagina=POR_PAGINA_ULTIMAS):
    """Página de «Últimas notícias», sem os artigos já exibidos acima."""
    ids = [artigo.pk for artigo in excluidos if artigo]
    paginador = Paginator(artigos_publicados().exclude(pk__in=ids), por_pagina)
    return paginador.get_page(pagina)


def artigos_do_tema(tema, pagina, por_pagina=POR_PAGINA_ULTIMAS * 2):
    paginador = Paginator(artigos_publicados().filter(temas=tema), por_pagina)
    return paginador.get_page(pagina)


def relacionados(artigo, limite=TOTAL_RELACIONADOS):
    """Artigos publicados que partilham algum tema com o dado."""
    return list(
        artigos_publicados()
        .filter(temas__in=artigo.temas.all())
        .exclude(pk=artigo.pk)
        .distinct()[:limite]
    )


def numeros_destaque(limite=TOTAL_NUMEROS):
    return list(
        NumeroDestaque.objects.filter(ativo=True).select_related("tema")[:limite]
    )


def processar_corpo(corpo):
    """Garante um id em cada <h2> e devolve (html, [(id, texto), ...]).

    O corpo é HTML editorial confiável (escrito pela redação), por isso é
    marcado como seguro.
    """
    indice = []
    usados = set()

    def com_id(encontrado):
        attrs = encontrado.group("attrs")
        texto = unescape(strip_tags(encontrado.group("texto"))).strip()
        existente = _ID.search(attrs)
        if existente:
            ancora = existente.group("id")
        else:
            ancora = _ancora_livre(slugify(texto) or "secao", usados)
            attrs = f'{attrs} id="{ancora}"'
        usados.add(ancora)
        indice.append((ancora, texto))
        return f"<h2{attrs}>{encontrado.group('texto')}</h2>"

    html = _H2.sub(com_id, corpo or "")
    return mark_safe(html), indice


def _ancora_livre(base, usados):
    ancora, n = base, 2
    while ancora in usados:
        ancora = f"{base}-{n}"
        n += 1
    return ancora
