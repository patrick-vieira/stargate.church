import json

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


# efeito -> {chave: (validador, descrição legível)}. Efeito novo = entrada nova aqui.
def _booleano(valor):
    return isinstance(valor, bool)


_FIXAR = (_booleano, "verdadeiro ou falso")


def _linhas(valor):
    return (
        isinstance(valor, list)
        and 1 <= len(valor) <= 12
        and all(_texto(v) and len(v) <= 80 for v in valor)
    )


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
    "terminal:fala": {
        "linhas": (_linhas, "uma lista de 1 a 12 textos de até 80 caracteres"),
        "velocidade": (_entre(10, 120), "um número entre 10 e 120 (ms por letra)"),
    },
    "three:corredor": {
        "profundidade": (_entre(4, 40), "um número entre 4 e 40 (aros)"),
        "fixar": _FIXAR,
    },
    "olho:segue": {
        "alcance": (_entre(0, 1), "um número entre 0 e 1"),
        "fixar": _FIXAR,
    },
    # Atmosfera inteira (STAR-41/STAR-51): o conteúdo vive no template.
    "atmosfera:maquina-fria": {},
    # Atmosfera do post 2 (STAR-42): HUD, glitch e scanlines; conteúdo no template.
    "atmosfera:guerra-maquinas": {},
    # Atmosfera do post 3 (STAR-43): sala de vidro e teste interativo; conteúdo no template.
    "atmosfera:ser-humano": {},
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
        TERMINAL = "terminal:fala", "Terminal que fala"
        CORREDOR = "three:corredor", "Corredor 3D"
        OLHO = "olho:segue", "Olho que segue o cursor"
        ATMOSFERA = "atmosfera:maquina-fria", "Atmosfera «Máquina fria»"
        ATMOSFERA_GUERRA = (
            "atmosfera:guerra-maquinas",
            "Atmosfera «Guerra das máquinas»",
        )
        ATMOSFERA_SER_HUMANO = (
            "atmosfera:ser-humano",
            "Atmosfera «O que é ser humano?»",
        )

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
