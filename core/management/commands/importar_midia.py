"""Copia os ficheiros finais de vídeo/áudio para o MEDIA_ROOT e liga-os aos modelos.

Uso: manage.py importar_midia --origem <pasta> [--serie ia-na-ficcao] [--vertical 2,7]

A pasta de origem tem o layout:
  STAR-49/videos/ia-ficcao-00…04/{video.mp4,poster.jpg,legendas.vtt}
  STAR-50/saida/star-post5…8/ e star-trailer/
  STAR-50/audio/star-audio-N/narracao.{mp3,opus}
  STAR-50/vertical/saida/star-vNN/video.mp4
Nada de mídia entra no git; o caminho da origem vem sempre por argumento.
"""

import shutil
from pathlib import Path

from django.conf import settings
from django.core.management.base import BaseCommand, CommandError

from core.models import Serie


def _pasta_video(origem, numero):
    if numero <= 4:
        return origem / "STAR-49" / "videos" / f"ia-ficcao-{numero:02d}"
    return origem / "STAR-50" / "saida" / f"star-post{numero}"


class Command(BaseCommand):
    help = "Copia vídeos e narrações finais para o MEDIA_ROOT e liga-os aos modelos."

    def add_arguments(self, parser):
        parser.add_argument("--origem", required=True, help="Pasta com as origens.")
        parser.add_argument("--serie", default="ia-na-ficcao")
        parser.add_argument(
            "--vertical",
            default="2,7",
            help="Números dos episódios com 9:16 com voz (vazio = nenhum).",
        )
        parser.add_argument("--dry-run", action="store_true")

    def _copiar(self, origem, destino_rel, dry):
        """Copia origem → MEDIA_ROOT/destino_rel; devolve o caminho relativo ou ''."""
        if not origem.is_file():
            self.stderr.write(f"  falta: {origem}")
            return ""
        if not dry:
            destino = Path(settings.MEDIA_ROOT) / destino_rel
            destino.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(origem, destino)
        self.stdout.write(f"  {destino_rel}  ({origem.stat().st_size // 1024} KB)")
        return destino_rel

    def handle(self, *args, **opts):
        origem = Path(opts["origem"]).resolve()
        if not origem.is_dir():
            raise CommandError(f"Origem inexistente: {origem}")
        try:
            serie = Serie.objects.get(slug=opts["serie"])
        except Serie.DoesNotExist:
            raise CommandError(f"Série inexistente: {opts['serie']}") from None
        dry = opts["dry_run"]
        verticais = {int(n) for n in opts["vertical"].split(",") if n.strip()}

        for ep in serie.episodios.order_by("numero"):
            n = ep.numero
            pasta = _pasta_video(origem, n)
            audio = origem / "STAR-50" / "audio" / f"star-audio-{n}"
            base = f"episodios/{serie.slug}/{n:02d}"
            self.stdout.write(f"Episódio {n} ({ep.slug})")
            fontes = {
                "video": (pasta / "video.mp4", "video.mp4"),
                "poster": (pasta / "poster.jpg", "poster.jpg"),
                "legenda": (pasta / "legendas.vtt", "legendas.vtt"),
                "audio": (audio / "narracao.mp3", "narracao.mp3"),
                "audio_ogg": (audio / "narracao.opus", "narracao.opus"),
            }
            if n in verticais:
                vert = origem / "STAR-50" / "vertical" / "saida" / f"star-v{n:02d}"
                fontes["video_vertical"] = (vert / "video.mp4", "vertical.mp4")
            for campo, (arq, nome) in fontes.items():
                setattr(ep, campo, self._copiar(arq, f"{base}/{nome}", dry))
            if not dry:
                ep.save()

        trailer = origem / "STAR-50" / "saida" / "star-trailer"
        base = f"series/{serie.slug}/trailer"
        self.stdout.write("Trailer")
        for campo, arq, nome in (
            ("trailer", "video.mp4", "video.mp4"),
            ("trailer_poster", "poster.jpg", "poster.jpg"),
            ("trailer_legenda", "legendas.vtt", "legendas.vtt"),
        ):
            setattr(serie, campo, self._copiar(trailer / arq, f"{base}/{nome}", dry))
        if not dry:
            serie.save()
        self.stdout.write(self.style.SUCCESS("Concluído." if not dry else "Simulação."))
