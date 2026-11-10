"""Copia os ficheiros finais de vídeo/áudio para o MEDIA_ROOT e liga-os aos modelos.

Uso: manage.py importar_midia --origem <pasta> [--origem <outra>] [--serie ia-na-ficcao]
     [--vertical 2,7] [--limite-mb 50] [--alvo-mb 40] [--destino local|imagetools]
     [--dry-run]

--destino imagetools envia o vídeo 16:9 (recomprimido se preciso) ao ImageTools e
guarda video_url + video_imagetools_uuid; o resto segue para o MEDIA_ROOT.

--origem repete-se; para cada ficheiro vale a primeira origem que o tiver.
Layouts aceites:
  <origem>/videos/ia-ficcao-NN/{video.mp4,poster.jpg,legendas.vtt}  (entrega)
  <origem>/STAR-49/videos/ia-ficcao-00…04/…                         (antigo)
  <origem>/STAR-50/saida/star-post5…8/… e star-trailer/
  <origem>/STAR-50/audio/star-audio-N/narracao.{mp3,opus}
  <origem>/STAR-50/vertical/saida/star-vNN/video.mp4
O episódio 0 é o vídeo do hub (sem migration).

Vídeos acima de --limite-mb são recomprimidos (libx264, ≤1080p, +faststart, alvo
--alvo-mb) para o destino; o original fica intacto. Nada de mídia entra no git.
"""

import shutil
import subprocess
import tempfile
from pathlib import Path

from django.conf import settings
from django.core.management.base import BaseCommand, CommandError

from core.models import Serie
from core.servicos import imagetools

MB = 1024 * 1024


def _pastas_video(origem, numero):
    """Pastas candidatas do vídeo do episódio `numero` numa origem."""
    pastas = [
        origem / "videos" / f"ia-ficcao-{numero:02d}",
        origem / "STAR-49" / "videos" / f"ia-ficcao-{numero:02d}",
    ]
    if numero >= 5:
        pastas.append(origem / "STAR-50" / "saida" / f"star-post{numero}")
    return pastas


def recomprimir_ffmpeg(origem, destino, alvo_bytes):
    """ÚNICO ponto que chama o ffmpeg/ffprobe; `origem` fica intacta.

    Escreve em `destino`: libx264 ≤1080p, +faststart, débito para `alvo_bytes`.
    """
    sonda = subprocess.run(
        ["ffprobe", "-v", "error", "-show_entries", "format=duration"]
        + ["-of", "default=nw=1:nk=1", str(origem)],
        capture_output=True,
        text=True,
        check=True,
    )
    duracao = max(float(sonda.stdout.strip()), 1.0)
    audio_bps = 128_000
    video_bps = max(int(alvo_bytes * 8 / duracao) - audio_bps, 200_000)
    subprocess.run(
        ["ffmpeg", "-y", "-i", str(origem), "-vf", "scale=-2:'min(1080,ih)'"]
        + ["-c:v", "libx264", "-b:v", str(video_bps)]
        + ["-maxrate", str(int(video_bps * 1.2)), "-bufsize", str(video_bps * 2)]
        + ["-c:a", "aac", "-b:a", "128k"]
        + ["-movflags", "+faststart", str(destino)],
        capture_output=True,
        check=True,
    )


class Command(BaseCommand):
    help = "Copia vídeos e narrações finais para o MEDIA_ROOT e liga-os aos modelos."

    def add_arguments(self, parser):
        parser.add_argument(
            "--origem",
            required=True,
            action="append",
            help="Pasta com as origens (repetível; vale a primeira com o ficheiro).",
        )
        parser.add_argument("--serie", default="ia-na-ficcao")
        parser.add_argument(
            "--vertical",
            default="2,7",
            help="Números dos episódios com 9:16 com voz (vazio = nenhum).",
        )
        parser.add_argument(
            "--limite-mb",
            type=int,
            default=50,
            help="Vídeos acima disto são recomprimidos.",
        )
        parser.add_argument(
            "--alvo-mb",
            type=int,
            default=40,
            help="Tamanho alvo da recompressão.",
        )
        parser.add_argument(
            "--destino",
            choices=["local", "imagetools"],
            default="local",
            help="Onde ficam os vídeos 16:9: MEDIA_ROOT (dev) ou ImageTools "
            "(IMAGETOOLS_API_URL e IMAGETOOLS_API_KEY no ambiente).",
        )
        parser.add_argument("--dry-run", action="store_true")

    def _achar(self, candidatos):
        for c in candidatos:
            if c.is_file():
                return c
        return None

    def _copiar(self, candidatos, destino_rel, dry):
        """Copia a 1.ª origem existente → MEDIA_ROOT/destino_rel (devolve-o, ou '')."""
        origem = self._achar(candidatos)
        if origem is None:
            self.stderr.write(f"  falta: {candidatos[0]}")
            return ""
        tamanho = origem.stat().st_size
        recomprimir = origem.suffix == ".mp4" and tamanho > self.limite
        if not dry:
            destino = Path(settings.MEDIA_ROOT) / destino_rel
            destino.parent.mkdir(parents=True, exist_ok=True)
            if recomprimir:
                try:
                    recomprimir_ffmpeg(origem, destino, self.alvo)
                except (OSError, subprocess.CalledProcessError, ValueError) as exc:
                    msg = f"Recompressão falhou ({origem}): {exc}"
                    raise CommandError(msg) from exc
            else:
                shutil.copyfile(origem, destino)
        nota = " [recomprimir]" if recomprimir else ""
        self.stdout.write(f"  {destino_rel}  ({tamanho // 1024} KB){nota}")
        return destino_rel

    def _enviar(self, candidatos, dry):
        """Recomprime se preciso, envia ao ImageTools → (uuid, url) ou ('', '')."""
        origem = self._achar(candidatos)
        if origem is None:
            self.stderr.write(f"  falta: {candidatos[0]}")
            return "", ""
        tamanho = origem.stat().st_size
        recomprimir = tamanho > self.limite
        nota = " [recomprimir]" if recomprimir else ""
        if dry:
            self.stdout.write(f"  → imagetools  ({tamanho // 1024} KB){nota}")
            return "", ""
        try:
            with tempfile.TemporaryDirectory(prefix="importar-midia-") as tmp:
                envio = origem
                if recomprimir:
                    envio = Path(tmp) / "video.mp4"
                    recomprimir_ffmpeg(origem, envio, self.alvo)
                uuid, url = imagetools.enviar_video(envio)
        except imagetools.ImageToolsErro as exc:
            raise CommandError(str(exc)) from exc
        except (OSError, subprocess.CalledProcessError, ValueError) as exc:
            raise CommandError(f"Recompressão falhou ({origem}): {exc}") from exc
        self.stdout.write(f"  → {url}  ({tamanho // 1024} KB){nota}")
        return uuid, url

    def handle(self, *args, **opts):
        brutas = opts["origem"]
        if isinstance(brutas, (str, Path)):  # call_command(origem="…")
            brutas = [brutas]
        origens = [Path(o).resolve() for o in brutas]
        for o in origens:
            if not o.is_dir():
                raise CommandError(f"Origem inexistente: {o}")
        try:
            serie = Serie.objects.get(slug=opts["serie"])
        except Serie.DoesNotExist:
            raise CommandError(f"Série inexistente: {opts['serie']}") from None
        dry = opts["dry_run"]
        self.limite = opts["limite_mb"] * MB
        self.alvo = opts["alvo_mb"] * MB
        self.destino = opts["destino"]
        if self.destino == "imagetools":
            try:
                imagetools.configuracao()  # falha cedo, antes de tocar em ficheiros
            except imagetools.ImageToolsErro as exc:
                raise CommandError(str(exc)) from exc
        verticais = {int(n) for n in opts["vertical"].split(",") if n.strip()}

        for ep in serie.episodios.order_by("numero"):
            n = ep.numero
            pastas = [p for o in origens for p in _pastas_video(o, n)]
            audios = [o / "STAR-50" / "audio" / f"star-audio-{n}" for o in origens]
            base = f"episodios/{serie.slug}/{n:02d}"
            self.stdout.write(f"Episódio {n} ({ep.slug})")
            fontes = {
                "video": ([p / "video.mp4" for p in pastas], "video.mp4"),
                "poster": ([p / "poster.jpg" for p in pastas], "poster.jpg"),
                "legenda": ([p / "legendas.vtt" for p in pastas], "legendas.vtt"),
                "audio": ([a / "narracao.mp3" for a in audios], "narracao.mp3"),
                "audio_ogg": ([a / "narracao.opus" for a in audios], "narracao.opus"),
            }
            if n in verticais:
                nome_v = f"star-v{n:02d}"
                verts = [
                    o / "STAR-50" / "vertical" / "saida" / nome_v / "video.mp4"
                    for o in origens
                ]
                fontes["video_vertical"] = (verts, "vertical.mp4")
            for campo, (cands, nome) in fontes.items():
                if campo == "video" and self.destino == "imagetools":
                    uuid, url = self._enviar(cands, dry)
                    if url:
                        ep.video_imagetools_uuid, ep.video_url = uuid, url
                    continue
                setattr(ep, campo, self._copiar(cands, f"{base}/{nome}", dry))
            if not dry:
                ep.save()

        trailers = [o / "STAR-50" / "saida" / "star-trailer" for o in origens]
        base = f"series/{serie.slug}/trailer"
        self.stdout.write("Trailer")
        for campo, arq in (
            ("trailer", "video.mp4"),
            ("trailer_poster", "poster.jpg"),
            ("trailer_legenda", "legendas.vtt"),
        ):
            cands = [t / arq for t in trailers]
            setattr(serie, campo, self._copiar(cands, f"{base}/{arq}", dry))
        if not dry:
            serie.save()
        self.stdout.write(self.style.SUCCESS("Concluído." if not dry else "Simulação."))
