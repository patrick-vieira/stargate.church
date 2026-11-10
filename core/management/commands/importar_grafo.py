import json
from pathlib import Path

from django.core.exceptions import ValidationError
from django.core.management.base import BaseCommand, CommandError
from django.db import transaction

from core.models import GrafoMuseu, Serie
from core.servicos.museu import validar_grafo


class Command(BaseCommand):
    help = "Valida e importa um grafo editorial atomicamente, sem publicar a série."

    def add_arguments(self, parser):
        parser.add_argument("ficheiro")

    def handle(self, *args, **options):
        try:
            dados = validar_grafo(
                json.loads(Path(options["ficheiro"]).read_text(encoding="utf-8"))
            )
        except (OSError, ValueError, ValidationError) as exc:
            raise CommandError("Grafo inválido: " + str(exc)) from None
        with transaction.atomic():
            serie, _ = Serie.objects.get_or_create(
                slug=dados["serie"], defaults={"titulo": dados["blocos"][0]["titulo"]}
            )
            GrafoMuseu.objects.update_or_create(serie=serie, defaults={"dados": dados})
        self.stdout.write(
            self.style.SUCCESS("Grafo importado; publicação da série preservada.")
        )
