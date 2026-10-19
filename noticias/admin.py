from django.contrib import admin, messages
from django.core.exceptions import ValidationError

from .models import Artigo, Autor, Fonte, NumeroDestaque, Tema


@admin.register(Tema)
class TemaAdmin(admin.ModelAdmin):
    list_display = ("nome", "slug")
    search_fields = ("nome", "slug")
    prepopulated_fields = {"slug": ("nome",)}


@admin.register(Fonte)
class FonteAdmin(admin.ModelAdmin):
    list_display = ("nome", "url", "descricao", "confiavel")
    list_filter = ("confiavel",)
    search_fields = ("nome", "url")


@admin.register(Autor)
class AutorAdmin(admin.ModelAdmin):
    list_display = ("nome", "slug", "funcao", "ativo")
    list_filter = ("ativo",)
    search_fields = ("nome", "slug")
    prepopulated_fields = {"slug": ("nome",)}


@admin.register(Artigo)
class ArtigoAdmin(admin.ModelAdmin):
    list_display = (
        "titulo",
        "autor",
        "estado",
        "destaque",
        "criado_em",
        "publicado_em",
    )
    list_filter = ("estado", "destaque", "temas")
    search_fields = ("titulo", "slug", "resumo")
    prepopulated_fields = {"slug": ("titulo",)}
    filter_horizontal = ("temas", "fontes")
    actions = ["verificar_artigos", "publicar_artigos"]

    def _aplicar(self, request, queryset, metodo, rotulo):
        feitos = 0
        for artigo in queryset:
            try:
                getattr(artigo, metodo)()
            except ValidationError as exc:
                self.message_user(
                    request,
                    f"{artigo}: {' '.join(exc.messages)}",
                    level=messages.ERROR,
                )
            else:
                feitos += 1
        if feitos:
            self.message_user(request, f"{feitos} artigo(s) {rotulo}.")

    @admin.action(description="Verificar artigos selecionados")
    def verificar_artigos(self, request, queryset):
        self._aplicar(request, queryset, "verificar", "verificado(s)")

    @admin.action(description="Publicar artigos selecionados")
    def publicar_artigos(self, request, queryset):
        self._aplicar(request, queryset, "publicar", "publicado(s)")


@admin.register(NumeroDestaque)
class NumeroDestaqueAdmin(admin.ModelAdmin):
    list_display = ("valor", "texto", "tema", "ordem", "ativo")
    list_filter = ("ativo", "tema")
    list_editable = ("ordem", "ativo")
