from django.core.exceptions import ValidationError
from django.db import models
from django.urls import reverse
from django.utils import timezone


class Tema(models.Model):
    nome = models.CharField("nome", max_length=100)
    slug = models.SlugField("slug", unique=True)

    class Meta:
        ordering = ["nome"]
        verbose_name = "tema"
        verbose_name_plural = "temas"

    def __str__(self):
        return self.nome


class Fonte(models.Model):
    nome = models.CharField("nome", max_length=200)
    url = models.URLField("URL", unique=True)
    confiavel = models.BooleanField("confiável", default=False)
    descricao = models.CharField(
        "descrição",
        max_length=300,
        blank=True,
        help_text="Afirmação que a fonte sustenta; aparece na validação de fatos.",
    )

    class Meta:
        ordering = ["nome"]
        verbose_name = "fonte"
        verbose_name_plural = "fontes"

    def __str__(self):
        return self.nome


class Autor(models.Model):
    """Persona de IA que assina os artigos."""

    nome = models.CharField("nome", max_length=100)
    slug = models.SlugField("slug", unique=True)
    bio = models.TextField("bio", blank=True)
    funcao = models.CharField(
        "função", max_length=100, blank=True, help_text="Ex.: repórter de energia."
    )
    ativo = models.BooleanField("ativo", default=True)
    agente_easyon = models.SlugField(
        "agente EasyON",
        blank=True,
        help_text="Slug do agente no EasyON que dá voz a este autor (opcional).",
    )

    class Meta:
        ordering = ["nome"]
        verbose_name = "autor"
        verbose_name_plural = "autores"

    def __str__(self):
        return self.nome


class Artigo(models.Model):
    class Estado(models.TextChoices):
        RASCUNHO = "rascunho", "Rascunho"
        VERIFICADO = "verificado", "Verificado"
        PUBLICADO = "publicado", "Publicado"

    titulo = models.CharField("título", max_length=200)
    slug = models.SlugField("slug", max_length=200, unique=True)
    resumo = models.TextField("resumo", blank=True)
    corpo = models.TextField("corpo", blank=True)
    autor = models.ForeignKey(
        Autor,
        on_delete=models.PROTECT,
        related_name="artigos",
        verbose_name="autor",
    )
    temas = models.ManyToManyField(
        Tema, blank=True, related_name="artigos", verbose_name="temas"
    )
    fontes = models.ManyToManyField(
        Fonte, blank=True, related_name="artigos", verbose_name="fontes"
    )
    estado = models.CharField(
        "estado",
        max_length=20,
        choices=Estado.choices,
        default=Estado.RASCUNHO,
    )
    destaque = models.BooleanField(
        "destaque",
        default=False,
        help_text="Manchete da home: vale o artigo publicado mais recente marcado.",
    )
    imagem_url = models.URLField(
        "URL da imagem",
        blank=True,
        help_text="Se vazia, usa-se a ilustração do tema.",
    )
    audio_url = models.URLField(
        "URL do áudio",
        blank=True,
        help_text="Voz gerada por IA (comando gerar_audio); o player some se vazia.",
    )
    tempo_leitura = models.PositiveSmallIntegerField(
        "tempo de leitura (min)", default=5
    )
    porque_boa_noticia = models.TextField(
        "por que isto é uma boa notícia",
        blank=True,
        help_text="HTML editorial curto; a caixa só aparece se houver texto.",
    )
    criado_em = models.DateTimeField("criado em", auto_now_add=True)
    atualizado_em = models.DateTimeField("atualizado em", auto_now=True)
    publicado_em = models.DateTimeField("publicado em", null=True, blank=True)

    class Meta:
        ordering = ["-criado_em"]
        verbose_name = "artigo"
        verbose_name_plural = "artigos"

    def __str__(self):
        return self.titulo

    def get_absolute_url(self):
        return reverse("noticias:artigo", args=[self.slug])

    @property
    def tema_principal(self):
        """Primeiro tema cadastrado entre os do artigo (None se não houver)."""
        return min(self.temas.all(), key=lambda tema: tema.pk, default=None)

    def verificar(self):
        """rascunho → verificado."""
        if self.estado != self.Estado.RASCUNHO:
            raise ValidationError(
                "Só é possível verificar um artigo em rascunho "
                f"(estado atual: {self.get_estado_display()})."
            )
        self.estado = self.Estado.VERIFICADO
        self.save(update_fields=["estado", "atualizado_em"])

    def publicar(self):
        """verificado → publicado; exige ao menos uma fonte."""
        if self.estado != self.Estado.VERIFICADO:
            raise ValidationError(
                "Só é possível publicar um artigo verificado "
                f"(estado atual: {self.get_estado_display()})."
            )
        if not self.fontes.exists():
            raise ValidationError("Publicar exige ao menos uma fonte.")
        self.estado = self.Estado.PUBLICADO
        self.publicado_em = timezone.now()
        self.save(update_fields=["estado", "publicado_em", "atualizado_em"])


class NumeroDestaque(models.Model):
    """Dado de «Boas notícias em números» na home."""

    valor = models.CharField("valor", max_length=30)
    texto = models.CharField("texto", max_length=200)
    fonte_texto = models.CharField("fonte", max_length=200)
    tema = models.ForeignKey(
        Tema,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="numeros",
        verbose_name="tema",
    )
    ordem = models.PositiveSmallIntegerField("ordem", default=0)
    ativo = models.BooleanField("ativo", default=True)

    class Meta:
        ordering = ["ordem", "pk"]
        verbose_name = "número em destaque"
        verbose_name_plural = "números em destaque"

    def __str__(self):
        return f"{self.valor} — {self.texto}"
