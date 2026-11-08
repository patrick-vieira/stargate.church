import json
import re

from django.core.exceptions import ValidationError
from django.db import models


def _numero(valor, minimo=None, maximo=None):
    if isinstance(valor, bool) or not isinstance(valor, int | float):
        return False
    return (minimo is None or valor >= minimo) and (maximo is None or valor <= maximo)


def _texto(valor):
    return isinstance(valor, str) and bool(valor.strip())


def _entre(minimo, maximo):
    return lambda valor: _numero(valor, minimo, maximo)


_SLUG = re.compile(r"[-a-zA-Z0-9_]+")


def _estacoes(valor):
    """Lista não vazia de {decada 1920..2020, titulo, slug?, texto?}."""
    if not isinstance(valor, list) or not valor:
        return False
    for e in valor:
        if not isinstance(e, dict) or not set(e) <= {"decada", "titulo", "slug", "texto"}:
            return False
        d = e.get("decada")
        if isinstance(d, bool) or not isinstance(d, int) or not 1920 <= d <= 2020:
            return False
        if not _texto(e.get("titulo")):
            return False
        if "slug" in e and not (_texto(e["slug"]) and _SLUG.fullmatch(e["slug"])):
            return False
        if "texto" in e and not _texto(e["texto"]):
            return False
    return True


# efeito -> {chave: (validador, descrição legível)}. Efeito novo = entrada nova aqui.
def _booleano(valor):
    return isinstance(valor, bool)


_FIXAR = (_booleano, "verdadeiro ou falso")

PARAMETROS_POR_EFEITO = {
    "parallax:camadas": {
        "intensidade": (_entre(0, 1), "um número entre 0 e 1"),
        "fixar": _FIXAR,
    },
    "scroll:revela": {
        "atraso": (_entre(0, 2), "um número entre 0 e 2 (segundos)"),
    },
    "three:gira": {
        "voltas": (_entre(0, 10), "um número entre 0 e 10"),
        "fixar": _FIXAR,
    },
    "rive:estado": {
        "propriedade": (_texto, "um texto não vazio"),
        "fixar": _FIXAR,
    },
    "diagrama:constroi": {
        "atraso": (_entre(0, 2), "um número entre 0 e 2 (segundos)"),
    },
    "linha-tempo:decadas": {
        "intensidade": (_entre(0, 1), "um número entre 0 e 1"),
        "estacoes": (
            _estacoes,
            "uma lista não vazia de objetos {decada: 1920..2020, titulo, "
            "slug (opcional), texto (opcional)}",
        ),
    },
}


class PostImersivo(models.Model):
    slug = models.SlugField("slug", unique=True)
    titulo = models.CharField("título", max_length=200)
    publicado = models.BooleanField("publicado", default=False)

    class Meta:
        verbose_name = "post imersivo"
        verbose_name_plural = "posts imersivos"
        ordering = ["titulo"]

    def __str__(self):
        return self.titulo

    @classmethod
    def publicados(cls):
        return cls.objects.filter(publicado=True)


class Ato(models.Model):
    class Efeito(models.TextChoices):
        PARALLAX = "parallax:camadas", "Parallax em camadas"
        SCROLL = "scroll:revela", "Revela ao rolar"
        THREE = "three:gira", "Cena 3D que gira"
        RIVE = "rive:estado", "Rive com estado"
        DIAGRAMA = "diagrama:constroi", "Diagrama que se constrói"
        LINHA_TEMPO = "linha-tempo:decadas", "Linha do tempo por décadas"

    class Reduzido(models.TextChoices):
        ESTATICO = "estatico", "Estático"
        OMITIR = "omitir", "Omitir"

    post = models.ForeignKey(
        PostImersivo,
        on_delete=models.CASCADE,
        related_name="atos",
        verbose_name="post",
    )
    ordem = models.PositiveIntegerField("ordem", default=0)
    titulo = models.CharField("título", max_length=200)
    texto = models.TextField("texto")
    efeito = models.CharField("efeito", max_length=30, choices=Efeito.choices)
    parametros = models.JSONField(
        "parâmetros",
        default=dict,
        blank=True,
        help_text="Objeto JSON; as chaves aceitas dependem do efeito.",
    )
    reduzido = models.CharField(
        "com movimento reduzido",
        max_length=10,
        choices=Reduzido.choices,
        default=Reduzido.ESTATICO,
    )

    class Meta:
        verbose_name = "ato"
        verbose_name_plural = "atos"
        ordering = ["post", "ordem", "pk"]

    def __str__(self):
        return f"{self.ordem}. {self.titulo}"

    @property
    def parametros_json(self):
        return json.dumps(self.parametros, ensure_ascii=False, sort_keys=True)

    @staticmethod
    def _forma(decada):
        if decada < 1940:
            return "papel"
        if decada < 1970:
            return "valvulas"
        if decada < 1990:
            return "fosforo"
        if decada < 2010:
            return "pixels"
        return "vidro"

    @property
    def estacoes(self):
        """Estações da linha do tempo, com a forma decorativa da época."""
        lista = self.parametros.get("estacoes") if isinstance(self.parametros, dict) else None
        if not isinstance(lista, list):
            return []
        return [
            {**e, "forma": self._forma(e["decada"])}
            for e in lista
            if isinstance(e, dict) and isinstance(e.get("decada"), int)
        ]

    def clean(self):
        super().clean()
        if not isinstance(self.parametros, dict):
            raise ValidationError(
                {"parametros": "Os parâmetros devem ser um objeto JSON."}
            )
        regras = PARAMETROS_POR_EFEITO.get(self.efeito)
        if regras is None:
            return
        erros = []
        for chave, valor in self.parametros.items():
            if chave not in regras:
                aceitas = ", ".join(sorted(regras))
                erros.append(
                    f"Parâmetro desconhecido «{chave}» para {self.efeito} "
                    f"(aceitos: {aceitas})."
                )
            elif not regras[chave][0](valor):
                erros.append(
                    f"Parâmetro «{chave}» inválido: esperado {regras[chave][1]}."
                )
        if erros:
            raise ValidationError({"parametros": erros})
