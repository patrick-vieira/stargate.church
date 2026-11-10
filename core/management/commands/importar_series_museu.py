import json
from pathlib import Path

from django.core.exceptions import ValidationError
from django.core.management import BaseCommand, CommandError, call_command
from django.db import transaction

from core.models import GrafoMuseu, Serie
from core.servicos.museu import validar_grafo


class Command(BaseCommand):
    help = "Importa repetidamente as seis séries do museu; publicar exige --publicar."

    def add_arguments(self, parser):
        parser.add_argument(
            "--publicar",
            action="store_true",
            help="Publica as seis séries no banco selecionado depois da importação.",
        )

    def handle(self, *args, **options):
        pasta = Path(__file__).resolve().parents[2] / "dados" / "grafos"
        ficheiros = sorted(pasta.glob("*.grafo.json"))
        if len(ficheiros) != 6:
            raise CommandError("Esperados seis grafos editoriais.")

        importacoes = []
        for ficheiro in ficheiros:
            try:
                dados = validar_grafo(json.loads(ficheiro.read_text(encoding="utf-8")))
            except (OSError, ValueError, ValidationError) as exc:
                raise CommandError(
                    f"Grafo inválido em {ficheiro.name}: {exc}"
                ) from None
            importacoes.append((ficheiro, dados))

        slugs = [dados["serie"] for _, dados in importacoes]
        if len(set(slugs)) != 6:
            raise CommandError("Os seis grafos precisam ter séries distintas.")

        with transaction.atomic():
            for ficheiro, _ in importacoes:
                call_command("importar_grafo", str(ficheiro), stdout=self.stdout)

            if options["publicar"]:
                Serie.objects.filter(slug__in=slugs).update(publicado=True)

        quantidade = GrafoMuseu.objects.filter(serie__slug__in=slugs).count()
        if options["publicar"]:
            self.stdout.write(self.style.SUCCESS("Seis séries mock publicadas."))
        else:
            self.stdout.write(
                "Importadas; a publicação existente foi preservada e as novas "
                "séries ficam como rascunho."
            )
        self.stdout.write(f"Grafos disponíveis: {quantidade}.")
