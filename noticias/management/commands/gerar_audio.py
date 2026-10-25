from django.core.management.base import BaseCommand, CommandError
from django.utils.html import strip_tags

from noticias.easyon import ClienteEasyON, EasyONIndisponivel
from noticias.models import Artigo


class Command(BaseCommand):
    help = "Gera o áudio (voz de IA) dos artigos cujo autor tem agente EasyON."

    def add_arguments(self, parser):
        parser.add_argument("--artigo", help="Slug de um só artigo.")
        parser.add_argument(
            "--forcar", action="store_true", help="Regenera mesmo com áudio."
        )

    def handle(self, *args, **opcoes):
        artigos = (
            Artigo.objects.filter(estado=Artigo.Estado.PUBLICADO)
            .exclude(autor__agente_easyon="")
            .select_related("autor")
        )
        if opcoes["artigo"]:
            artigos = artigos.filter(slug=opcoes["artigo"])
            if not artigos.exists():
                raise CommandError("Artigo publicado com agente não encontrado.")
        if not opcoes["forcar"]:
            artigos = artigos.filter(audio_url="")
        cliente = ClienteEasyON()
        feitos = falhas = 0
        for artigo in artigos:
            texto = f"{artigo.titulo}. {strip_tags(artigo.corpo)}".strip()
            try:
                resposta = cliente.gerar_audio(artigo.autor.agente_easyon, texto)
            except EasyONIndisponivel as erro:
                falhas += 1
                self.stderr.write(f"{artigo.slug}: falhou — {erro}")
                continue
            artigo.audio_url = resposta["url"]
            artigo.save(update_fields=["audio_url", "atualizado_em"])
            feitos += 1
            self.stdout.write(f"{artigo.slug}: ok")
        self.stdout.write(f"Gerados: {feitos}; falhas: {falhas}.")
