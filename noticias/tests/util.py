"""Fábricas de dados fictícios para os testes."""

import itertools
from datetime import UTC, datetime, timedelta

from django.utils.text import slugify

from noticias.models import Artigo, Autor, Fonte, Tema

_contador = itertools.count(1)
BASE = datetime(2026, 10, 18, 12, 0, tzinfo=UTC)


def criar_tema(nome, slug=None):
    return Tema.objects.create(nome=nome, slug=slug or slugify(nome))


def criar_autor(nome="Helena Aragão", funcao="repórter de energia"):
    n = next(_contador)
    return Autor.objects.create(nome=nome, slug=f"autor-{n}", funcao=funcao)


def criar_fonte(nome=None, descricao="", confiavel=True):
    n = next(_contador)
    return Fonte.objects.create(
        nome=nome or f"Fonte {n}",
        url=f"https://exemplo.org/fonte-{n}",
        confiavel=confiavel,
        descricao=descricao,
    )


def criar_artigo(
    titulo=None,
    temas=(),
    fontes=1,
    estado=Artigo.Estado.PUBLICADO,
    dias_atras=0,
    autor=None,
    **extra,
):
    """Cria um artigo; `dias_atras` controla a ordem de publicação."""
    n = next(_contador)
    artigo = Artigo.objects.create(
        titulo=titulo or f"Artigo {n}",
        slug=f"artigo-{n}",
        resumo=f"Resumo {n}.",
        corpo=extra.pop("corpo", "<p>Texto.</p>"),
        autor=autor or criar_autor(),
        estado=estado,
        publicado_em=(
            BASE - timedelta(days=dias_atras)
            if estado == Artigo.Estado.PUBLICADO
            else None
        ),
        **extra,
    )
    artigo.temas.set(temas)
    artigo.fontes.set(
        [criar_fonte(descricao=f"Afirmação {n}.{i}") for i in range(fontes)]
    )
    return artigo
