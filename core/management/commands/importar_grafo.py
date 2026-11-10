import json
import uuid
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
        parser.add_argument(
            "--manifesto-audio",
            help="Manifesto externo com UUIDs de narração e som ambiente por bloco.",
        )

    def handle(self, *args, **options):
        try:
            dados = validar_grafo(
                json.loads(Path(options["ficheiro"]).read_text(encoding="utf-8"))
            )
            if options.get("manifesto_audio"):
                dados = associar_audio(
                    dados,
                    json.loads(
                        Path(options["manifesto_audio"]).read_text(encoding="utf-8")
                    ),
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


def associar_audio(dados, manifesto):
    """Valida o manifesto completo antes de associar apenas UUIDs ao grafo."""
    esperado = {str(numero) for numero in range(1, 25)}
    if (
        dados.get("serie") != "mock-energia-sem-fim"
        or not isinstance(manifesto, dict)
        or set(manifesto) != esperado
    ):
        raise ValidationError("Manifesto de áudio incompatível com a série.")
    por_numero = {bloco["numero"]: bloco for bloco in dados["blocos"]}
    if set(por_numero) != set(range(1, 25)) or any(
        por_numero[numero]["id"] != numero for numero in range(1, 25)
    ):
        raise ValidationError("A série precisa ter os 24 IDs editoriais coerentes.")
    vistos = set()
    associa = {}
    for numero in range(1, 25):
        entrada = manifesto[str(numero)]
        if not isinstance(entrada, dict):
            raise ValidationError("Entrada de áudio inválida.")
        uuids = {}
        for tipo in ("narracao", "som"):
            try:
                valor = str(uuid.UUID(entrada[f"{tipo}_uuid"]))
            except (KeyError, ValueError, TypeError, AttributeError):
                raise ValidationError("UUID de áudio inválido.") from None
            if valor in vistos:
                raise ValidationError("UUIDs de áudio repetidos.")
            vistos.add(valor)
            uuids[f"{tipo}_imagetools_uuid"] = valor
        associa[numero] = uuids
    for numero, bloco in por_numero.items():
        bloco.update(associa[numero])
    return dados
