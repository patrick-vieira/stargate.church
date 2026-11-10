import json
import re

from django.conf import settings
from django.core.exceptions import ValidationError
from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models
from django.urls import reverse


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
        chaves = {"decada", "titulo", "slug", "texto"}
        if not isinstance(e, dict) or not set(e) <= chaves:
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


def _perguntas(valor):
    """Lista de 1 a 8 {id, rotulo, slugs:[slug de estação]}; ids únicos."""
    if not isinstance(valor, list) or not 1 <= len(valor) <= 8:
        return False
    ids = set()
    for p in valor:
        if not isinstance(p, dict) or set(p) != {"id", "rotulo", "slugs"}:
            return False
        if not (_texto(p["id"]) and _SLUG.fullmatch(p["id"])) or p["id"] in ids:
            return False
        ids.add(p["id"])
        if not _texto(p["rotulo"]) or len(p["rotulo"]) > 40:
            return False
        slugs = p["slugs"]
        if not isinstance(slugs, list) or not all(
            _texto(s) and _SLUG.fullmatch(s) for s in slugs
        ):
            return False
    return True


def _previa(valor):
    """Lista de 1 a 6 pontos da prévia do placar.

    Cada ponto é {id} (uma obra de core/dados/placar.json, a forma preferida) ou
    {obra, x, y} com x e y entre 0 e 100 (forma escrita à mão, mantida).
    """
    from . import placar

    if not isinstance(valor, list) or not 1 <= len(valor) <= 6:
        return False
    for p in valor:
        if isinstance(p, dict) and set(p) == {"id"}:
            if not isinstance(p["id"], str) or placar.obra(p["id"]) is None:
                return False
            continue
        if not isinstance(p, dict) or set(p) != {"obra", "x", "y"}:
            return False
        if not _texto(p["obra"]) or len(p["obra"]) > 60:
            return False
        if not (_numero(p["x"], 0, 100) and _numero(p["y"], 0, 100)):
            return False
    return True


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
    "linha-tempo:decadas": {
        "intensidade": (_entre(0, 1), "um número entre 0 e 1"),
        "estacoes": (
            _estacoes,
            "uma lista não vazia de objetos {decada: 1920..2020, titulo, "
            "slug (opcional), texto (opcional)}",
        ),
    },
    # Hub (STAR-63): chips que atenuam as estações do trilho; grelha dos posts.
    "filtro:chips": {
        "perguntas": (
            _perguntas,
            "uma lista de 1 a 8 objetos {id, rotulo, slugs: [slugs de estações]}",
        ),
    },
    "grelha:posts": {
        "previa": (
            _previa,
            "uma lista de 1 a 6 objetos {id: id de uma obra do placar} "
            "ou {obra, x: 0..100, y: 0..100}",
        ),
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
    # Atmosfera do post 3 (STAR-43): sala de vidro e teste; conteúdo no template.
    "atmosfera:ser-humano": {},
    # Atmosfera do post 6 (STAR-46): narrativa ramificada, estado no cliente.
    "atmosfera:escolhas": {},
    # Atmosfera inteira (STAR-44/STAR-51): o conteúdo vive no template.
    "atmosfera:ia-afetiva": {},
    # Atmosfera do post 5 (STAR-45): livro que vira em 3D, regras que se reescrevem.
    "atmosfera:leis-robos-livros": {},
    # Atmosfera do post 8 (STAR-48): placar; as obras vêm de core/dados/placar.json.
    "atmosfera:placar": {},
    # Atmosfera do post 7 (STAR-47): cidade de vigilância, celular que racha.
    "atmosfera:quase-presente": {},
    # Atmosfera do hub (STAR-70): névoa, luz por década e faixa; cartões no template.
    "atmosfera:hub": {},
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
        FILTRO_CHIPS = "filtro:chips", "Filtro por chips (perguntas)"
        GRELHA_POSTS = "grelha:posts", "Grelha dos posts da série"
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
        ATMOSFERA_ESCOLHAS = (
            "atmosfera:escolhas",
            "Atmosfera «Escolhas da máquina»",
        )
        ATMOSFERA_IA_AFETIVA = "atmosfera:ia-afetiva", "Atmosfera «IA afetiva»"
        ATMOSFERA_LEIS_ROBOS_LIVROS = (
            "atmosfera:leis-robos-livros",
            "Atmosfera «Leis, robôs e livros»",
        )
        ATMOSFERA_QUASE_PRESENTE = (
            "atmosfera:quase-presente",
            "Atmosfera «O quase-presente»",
        )
        ATMOSFERA_PLACAR = "atmosfera:placar", "Atmosfera «O placar»"
        ATMOSFERA_HUB = "atmosfera:hub", "Atmosfera «Hub»"

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
        if decada < 1960:
            return "valvulas"
        if decada < 1970:
            return "transistor"
        if decada < 1990:
            return "fosforo"
        if decada < 2010:
            return "pixels"
        if decada < 2020:
            return "vidro"
        return "rede"

    @property
    def estacoes(self):
        """Estações da linha do tempo, com a forma decorativa da época."""
        params = self.parametros
        lista = params.get("estacoes") if isinstance(params, dict) else None
        if not isinstance(lista, list):
            return []
        validas = [
            e for e in lista if isinstance(e, dict) and isinstance(e.get("decada"), int)
        ]
        vistas = {}
        estacoes = []
        for e in validas:
            n = vistas.get(e["decada"], 0)
            vistas[e["decada"]] = n + 1
            estacoes.append(
                {
                    **e,
                    "forma": self._forma(e["decada"]),
                    # Posição dentro da mesma década: variante visual da arte.
                    "variante": n % 3,
                    "url": getattr(self, "urls_episodios", {}).get(e.get("slug")),
                }
            )
        return estacoes

    @property
    def previa_pontos(self):
        """Pontos da prévia do placar já em coordenadas do SVG (400×260)."""
        params = self.parametros
        lista = params.get("previa") if isinstance(params, dict) else None
        if not isinstance(lista, list):
            return []
        from . import placar

        base = []
        for p in lista:
            if not isinstance(p, dict):
                continue
            if set(p) == {"id"}:
                p = placar.ponto_previa(p["id"])
                if p is None:
                    continue
            if not (_numero(p.get("x")) and _numero(p.get("y"))):
                continue
            cx = round(50 + p["x"] * 3.3, 1)
            cy = round(210 - p["y"] * 1.9, 1)
            base.append((p, cx, cy))

        def caixa(cx, cy, ancora, w, lado):
            # Caixa (x0, y0, x1, y1) do rótulo; o texto de 13 px tem ~16 px de altura.
            if lado == "v":
                x0 = cx - w / 2
                return (x0, cy - 30, x0 + w, cy - 14)
            if lado == "b":
                x0 = cx - w / 2
                return (x0, cy + 11, x0 + w, cy + 27)
            x0 = cx + 10 if ancora == "start" else cx - 10 - w
            return (x0, cy - 12, x0 + w, cy + 4)

        def cruza(a, b):
            return a[0] < b[2] and b[0] < a[2] and a[1] < b[3] and b[1] < a[3]

        discos = [(cx - 9, cy - 9, cx + 9, cy + 9) for _, cx, cy in base]
        ocupadas = []
        pontos = []
        for i, (p, cx, cy) in enumerate(base):
            w = len(str(p["obra"])) * 7.4  # ~13 px em fonte sem serifa
            pref = "end" if cx > 260 else "start"
            outro = "start" if pref == "end" else "end"
            opcoes = [(pref, "h"), (outro, "h"), ("middle", "v"), ("middle", "b")]

            def livre(o, i=i, cx=cx, cy=cy, w=w):
                c = caixa(cx, cy, o[0], w, o[1])
                return (
                    c[0] >= 52
                    and c[2] <= 380
                    and c[1] >= 22
                    and c[3] <= 208
                    and not any(cruza(c, d) for k, d in enumerate(discos) if k != i)
                    and not any(cruza(c, d) for d in ocupadas)
                )

            esc = next((o for o in opcoes if livre(o)), opcoes[0])
            c = caixa(cx, cy, esc[0], w, esc[1])
            ocupadas.append(c)
            if esc[1] != "h":
                tx = cx
            else:
                tx = cx + 10 if esc[0] == "start" else cx - 10
            pontos.append(
                {
                    **p,
                    "cx": cx,
                    "cy": cy,
                    "tx": round(tx, 1),
                    "ty": round(c[1] + 12, 1),
                    "ancora": esc[0],
                }
            )
        return pontos

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


class Serie(models.Model):
    slug = models.SlugField("slug", unique=True)
    titulo = models.CharField("título", max_length=200)
    resumo = models.TextField("resumo", blank=True)
    capa = models.CharField(
        "capa",
        max_length=200,
        blank=True,
        help_text="Caminho estático da imagem de capa (opcional).",
    )
    ordem = models.PositiveIntegerField("ordem", default=0)
    publicado = models.BooleanField("publicado", default=False)
    hub = models.ForeignKey(
        PostImersivo,
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name="series_hub",
        verbose_name="página da série (hub)",
        help_text="Post imersivo renderizado em /series/<série>/.",
    )

    trailer = models.FileField(
        "trailer (16:9)", upload_to="series/trailer/", blank=True, max_length=200
    )
    trailer_poster = models.FileField(
        "poster do trailer", upload_to="series/trailer/", blank=True, max_length=200
    )
    trailer_legenda = models.FileField(
        "legenda do trailer (VTT)",
        upload_to="series/trailer/",
        blank=True,
        max_length=200,
    )

    class Meta:
        verbose_name = "série"
        verbose_name_plural = "séries"
        ordering = ["ordem", "titulo"]

    def __str__(self):
        return self.titulo

    def get_absolute_url(self):
        return reverse("core:serie", args=[self.slug])


class Episodio(models.Model):
    serie = models.ForeignKey(
        Serie,
        on_delete=models.CASCADE,
        related_name="episodios",
        verbose_name="série",
    )
    numero = models.PositiveIntegerField("número")
    slug = models.SlugField("slug")
    titulo = models.CharField("título", max_length=200, blank=True)
    post = models.OneToOneField(
        PostImersivo,
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name="episodio",
        verbose_name="conteúdo imersivo",
    )
    publicado = models.BooleanField("publicado", default=False)
    video = models.FileField(
        "vídeo 16:9", upload_to="episodios/", blank=True, max_length=200
    )
    video_url = models.URLField(
        "vídeo 16:9 (URL externo, ImageTools)", max_length=500, blank=True
    )
    video_imagetools_uuid = models.CharField(
        "uuid do vídeo no ImageTools", max_length=64, blank=True
    )
    video_vertical = models.FileField(
        "vídeo 9:16 (opcional, com voz)",
        upload_to="episodios/",
        blank=True,
        max_length=200,
    )
    poster = models.FileField(
        "poster do vídeo", upload_to="episodios/", blank=True, max_length=200
    )
    audio = models.FileField(
        "áudio da narração (MP3)", upload_to="episodios/", blank=True, max_length=200
    )
    audio_ogg = models.FileField(
        "áudio da narração (Opus/OGG, opcional)",
        upload_to="episodios/",
        blank=True,
        max_length=200,
    )
    legenda = models.FileField(
        "legenda (VTT)", upload_to="episodios/", blank=True, max_length=200
    )
    transcricao = models.TextField("transcrição", blank=True)

    class Meta:
        verbose_name = "episódio"
        verbose_name_plural = "episódios"
        ordering = ["serie", "numero"]
        constraints = [
            models.UniqueConstraint(
                fields=["serie", "numero"], name="episodio_numero_unico_na_serie"
            ),
            models.UniqueConstraint(
                fields=["serie", "slug"], name="episodio_slug_unico_na_serie"
            ),
        ]

    def __str__(self):
        return f"{self.serie.slug} · {self.numero}. {self.titulo or self.slug}"

    def get_absolute_url(self):
        return reverse("core:episodio", args=[self.serie.slug, self.slug])

    @property
    def tem_midia(self):
        return bool(self.video_url or self.video or self.audio)


class VotoPlacar(models.Model):
    """Voto de um leitor numa obra do placar (STAR-48): uma linha por leitor e obra."""

    utilizador = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="votos_placar",
        verbose_name="leitor",
    )
    obra = models.SlugField("obra", max_length=60)
    proximidade = models.PositiveSmallIntegerField(
        "perto", validators=[MinValueValidator(0), MaxValueValidator(5)]
    )
    preocupacao = models.PositiveSmallIntegerField(
        "preocupação", validators=[MinValueValidator(0), MaxValueValidator(5)]
    )
    atualizado_em = models.DateTimeField("atualizado em", auto_now=True)

    class Meta:
        verbose_name = "voto no placar"
        verbose_name_plural = "votos no placar"
        constraints = [
            models.UniqueConstraint(
                fields=["utilizador", "obra"], name="voto_placar_unico_por_obra"
            )
        ]

    def __str__(self):
        return f"{self.utilizador} · {self.obra}: {self.proximidade}/{self.preocupacao}"


class GrafoMuseu(models.Model):
    serie = models.OneToOneField(
        Serie, on_delete=models.CASCADE, related_name="grafo_museu"
    )
    dados = models.JSONField("grafo editorial")

    class Meta:
        verbose_name = "grafo do museu"

    def __str__(self):
        return self.serie.titulo
