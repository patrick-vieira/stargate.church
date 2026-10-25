from django.core.exceptions import ValidationError
from django.db import models
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
    ativo = models.BooleanField("ativo", default=True)

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
    slug = models.SlugField("slug", unique=True)
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
    criado_em = models.DateTimeField("criado em", auto_now_add=True)
    atualizado_em = models.DateTimeField("atualizado em", auto_now=True)
    publicado_em = models.DateTimeField("publicado em", null=True, blank=True)

    class Meta:
        ordering = ["-criado_em"]
        verbose_name = "artigo"
        verbose_name_plural = "artigos"

    def __str__(self):
        return self.titulo

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
