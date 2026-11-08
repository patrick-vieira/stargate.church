from django.contrib import admin

from .models import Ato, PostImersivo


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
