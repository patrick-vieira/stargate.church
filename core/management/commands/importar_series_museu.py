import json
from pathlib import Path

from django.core.exceptions import ValidationError
from django.core.management import BaseCommand, CommandError
from django.db import transaction

from core.management.commands.importar_grafo import associar_audio
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
        parser.add_argument(
            "--manifesto-audio",
            action="append",
            default=[],
            metavar="SLUG=CAMINHO",
            help="Manifesto de áudio de uma série; informe uma vez para cada série.",
        )

    def handle(self, *args, **options):
        pasta = Path(__file__).resolve().parents[2] / "dados" / "grafos"
        ficheiros = sorted(pasta.glob("*.grafo.json"))
        if len(ficheiros) != 6:
            raise CommandError("Esperados seis grafos editoriais.")

        manifestos = {}
        for argumento in options["manifesto_audio"]:
            slug, separador, caminho = argumento.partition("=")
            if not separador or not slug or not caminho or slug in manifestos:
                raise CommandError(
                    "Informe cada manifesto como SLUG=CAMINHO, sem repetição."
                )
            manifestos[slug] = Path(caminho)

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
        if manifestos and set(manifestos) != set(slugs):
            raise CommandError(
                "Informe exatamente um manifesto para cada uma das seis séries."
            )

        # Validar o lote completo antes de abrir a transação ou gravar qualquer série.
        for ficheiro, dados in importacoes:
            if not manifestos:
                break
            try:
                manifesto = json.loads(
                    manifestos[dados["serie"]].read_text(encoding="utf-8")
                )
                associar_audio(dados, manifesto)
            except (OSError, ValueError, ValidationError) as exc:
                raise CommandError(
                    f"Manifesto inválido para {dados['serie']} ({ficheiro.name}): {exc}"
                ) from None

        with transaction.atomic():
            for _, dados in importacoes:
                serie, _ = Serie.objects.get_or_create(
                    slug=dados["serie"],
                    defaults={"titulo": dados["blocos"][0]["titulo"]},
                )
                GrafoMuseu.objects.update_or_create(
                    serie=serie, defaults={"dados": dados}
                )

            if options["publicar"]:
                Serie.objects.filter(slug__in=slugs).update(publicado=True)

        quantidade = GrafoMuseu.objects.filter(serie__slug__in=slugs).count()
        if options["publicar"]:
            self.stdout.write(
                self.style.SUCCESS("Seis séries mock importadas e publicadas.")
            )
        else:
            self.stdout.write(
                "Importadas; a publicação existente foi preservada e as novas "
                "séries ficam como rascunho."
            )
        self.stdout.write(f"Grafos disponíveis: {quantidade}.")
