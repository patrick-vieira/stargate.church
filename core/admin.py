from django.contrib import admin

from .models import Ato, Episodio, PostImersivo, Serie, VotoPlacar


class AtoInline(admin.StackedInline):
    model = Ato
    extra = 1
    ordering = ("ordem",)


@admin.register(PostImersivo)
class PostImersivoAdmin(admin.ModelAdmin):
    list_display = ("titulo", "slug", "publicado")
    list_filter = ("publicado",)
    search_fields = ("titulo", "slug")
    prepopulated_fields = {"slug": ("titulo",)}
    inlines = [AtoInline]


class EpisodioInline(admin.TabularInline):
    model = Episodio
    extra = 0
    ordering = ("numero",)


@admin.register(Serie)
class SerieAdmin(admin.ModelAdmin):
    list_display = ("titulo", "slug", "ordem", "publicado")
    list_filter = ("publicado",)
    search_fields = ("titulo", "slug")
    prepopulated_fields = {"slug": ("titulo",)}
    inlines = [EpisodioInline]
    fields = (
        "slug",
        "titulo",
        "resumo",
        "capa",
        "ordem",
        "publicado",
        "hub",
        "trailer",
        "trailer_poster",
        "trailer_legenda",
    )


@admin.register(Episodio)
class EpisodioAdmin(admin.ModelAdmin):
    list_display = ("__str__", "serie", "numero", "publicado")
    list_filter = ("serie", "publicado")
    search_fields = ("titulo", "slug")


@admin.register(VotoPlacar)
class VotoPlacarAdmin(admin.ModelAdmin):
    list_display = ("obra", "utilizador", "proximidade", "preocupacao", "atualizado_em")
    list_filter = ("obra",)
    search_fields = ("obra",)
    raw_id_fields = ("utilizador",)
