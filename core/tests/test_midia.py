import tempfile
from io import StringIO
from pathlib import Path

from django.core.management import call_command
from django.core.management.base import CommandError
from django.test import TestCase, override_settings

from core.models import Episodio, Serie

from .test_series import FIXTURES

TMP = tempfile.mkdtemp(prefix="midia-teste-")


def _origem(raiz):
    """Cria uma origem mínima (ficheiros de poucos bytes) com o layout esperado."""
    for n in range(9):
        if n <= 4:
            pasta = raiz / "STAR-49" / "videos" / f"ia-ficcao-{n:02d}"
        else:
            pasta = raiz / "STAR-50" / "saida" / f"star-post{n}"
        pasta.mkdir(parents=True)
        (pasta / "video.mp4").write_bytes(b"v")
        (pasta / "poster.jpg").write_bytes(b"p")
        (pasta / "legendas.vtt").write_bytes(b"WEBVTT\n")
        aud = raiz / "STAR-50" / "audio" / f"star-audio-{n}"
        aud.mkdir(parents=True)
        (aud / "narracao.mp3").write_bytes(b"a")
        (aud / "narracao.opus").write_bytes(b"o")
    for n in (2, 7):
        v = raiz / "STAR-50" / "vertical" / "saida" / f"star-v{n:02d}"
        v.mkdir(parents=True)
        (v / "video.mp4").write_bytes(b"x")
    t = raiz / "STAR-50" / "saida" / "star-trailer"
    t.mkdir(parents=True)
    for nome in ("video.mp4", "poster.jpg", "legendas.vtt"):
        (t / nome).write_bytes(b"t")


@override_settings(MEDIA_ROOT=TMP)
class ImportarMidiaTests(TestCase):
    fixtures = FIXTURES

    def setUp(self):
        self.origem = Path(tempfile.mkdtemp(prefix="origem-teste-"))
        _origem(self.origem)

    def _importar(self, **kw):
        call_command("importar_midia", origem=str(self.origem), stdout=StringIO(), **kw)

    def test_preenche_campos_e_copia_ficheiros(self):
        self._importar()
        e = Episodio.objects.get(serie__slug="ia-na-ficcao", numero=1)
        self.assertEqual(e.video.name, "episodios/ia-na-ficcao/01/video.mp4")
        self.assertTrue((Path(TMP) / e.video.name).is_file())
        self.assertTrue(e.audio and e.audio_ogg and e.poster and e.legenda)
        self.assertFalse(e.video_vertical)

    def test_vertical_so_nos_pedidos(self):
        self._importar()
        com = set(
            Episodio.objects.exclude(video_vertical="").values_list("numero", flat=True)
        )
        self.assertEqual(com, {2, 7})

    def test_episodios_sem_post_ficam_preenchidos(self):
        self._importar()
        for n in (5, 7, 8):
            self.assertTrue(Episodio.objects.get(numero=n).video)

    def test_trailer_na_serie(self):
        self._importar()
        s = Serie.objects.get(slug="ia-na-ficcao")
        self.assertEqual(s.trailer.name, "series/ia-na-ficcao/trailer/video.mp4")

    def test_idempotente(self):
        self._importar()
        self._importar()
        self.assertEqual(Episodio.objects.exclude(video="").count(), 9)

    def test_dry_run_nao_escreve(self):
        self._importar(dry_run=True)
        self.assertEqual(Episodio.objects.exclude(video="").count(), 0)

    def test_origem_inexistente(self):
        with self.assertRaises(CommandError):
            call_command("importar_midia", origem="/nao/existe")


@override_settings(MEDIA_ROOT=TMP)
class PlayerTests(TestCase):
    fixtures = FIXTURES

    def _com_midia(self, numero=1, **extra):
        e = Episodio.objects.get(numero=numero)
        e.video = "episodios/x/video.mp4"
        e.poster = "episodios/x/poster.jpg"
        e.legenda = "episodios/x/legendas.vtt"
        e.audio = "episodios/x/narracao.mp3"
        e.audio_ogg = "episodios/x/narracao.opus"
        for k, v in extra.items():
            setattr(e, k, v)
        e.save()
        return e

    def test_sem_midia_sem_player(self):
        r = self.client.get("/series/ia-na-ficcao/a-maquina-fria/")
        self.assertNotContains(r, "data-midia")
        self.assertNotContains(r, "<video")

    def test_player_com_poster_preload_none_sem_autoplay(self):
        self._com_midia()
        r = self.client.get("/series/ia-na-ficcao/a-maquina-fria/")
        html = r.content.decode()
        self.assertIn('preload="none"', html)
        self.assertIn('poster="/midia/episodios/x/poster.jpg"', html)
        self.assertIn('<track kind="captions"', html)
        self.assertIn("Ouvir este episódio", html)
        self.assertNotIn("autoplay", html.lower())
        self.assertNotIn("muted", html.lower())

    def test_audio_nao_carrega_sem_clique(self):
        self._com_midia()
        r = self.client.get("/series/ia-na-ficcao/a-maquina-fria/")
        self.assertContains(r, '<audio preload="none"')

    def test_vertical_so_quando_ha_ficheiro(self):
        self._com_midia()
        r = self.client.get("/series/ia-na-ficcao/a-maquina-fria/")
        self.assertNotContains(r, "Versão vertical")
        self._com_midia(video_vertical="episodios/x/vertical.mp4")
        r = self.client.get("/series/ia-na-ficcao/a-maquina-fria/")
        self.assertContains(r, "Versão vertical")

    def test_player_em_todos_os_templates_de_episodio(self):
        for n, slug in [
            (1, "a-maquina-fria"),
            (2, "o-medo-da-guerra-das-maquinas"),
            (3, "o-que-e-ser-humano"),
            (4, "a-ia-afetiva"),
            (6, "escolhas-da-maquina"),
            (7, "o-quase-presente"),
        ]:
            self._com_midia(n)
            with self.subTest(slug=slug):
                r = self.client.get(f"/series/ia-na-ficcao/{slug}/")
                self.assertContains(r, "data-midia")

    def test_bloco_vem_depois_do_h1_em_todos_os_templates(self):
        for n, slug in [
            (1, "a-maquina-fria"),
            (2, "o-medo-da-guerra-das-maquinas"),
            (3, "o-que-e-ser-humano"),
            (4, "a-ia-afetiva"),
            (6, "escolhas-da-maquina"),
            (7, "o-quase-presente"),
        ]:
            self._com_midia(n)
            with self.subTest(slug=slug):
                html = self.client.get(f"/series/ia-na-ficcao/{slug}/").content.decode()
                self.assertGreater(html.index("data-midia"), html.index("<h1"))

    def test_sem_estilo_inline_e_css_estatico(self):
        self._com_midia(video_vertical="episodios/x/vertical.mp4", transcricao="T")
        html = self.client.get("/series/ia-na-ficcao/a-maquina-fria/").content.decode()
        ini = html.index("data-midia")
        bloco = html[ini : html.index("</section>", ini)]
        self.assertNotIn("style=", bloco)
        self.assertNotIn("<style", bloco)
        self.assertNotIn("system-ui", bloco)
        self.assertIn("css/midia.css", bloco)
        self.assertIn("Ver e ouvir", bloco)

    def test_css_so_com_tokens(self):
        from django.conf import settings

        css = (settings.BASE_DIR / "static" / "css" / "midia.css").read_text()
        self.assertNotRegex(css, r"#[0-9a-fA-F]{3,8}\b")
        self.assertNotIn("system-ui", css)

    def test_trailer_no_hub(self):
        s = Serie.objects.get(slug="ia-na-ficcao")
        s.trailer = "series/t/video.mp4"
        s.trailer_poster = "series/t/poster.jpg"
        s.save()
        r = self.client.get("/series/ia-na-ficcao/")
        self.assertContains(r, 'src="/midia/series/t/video.mp4"')
        self.assertContains(r, "Trailer")

    def test_transcricao_aparece(self):
        self._com_midia(transcricao="Linha um.")
        r = self.client.get("/series/ia-na-ficcao/a-maquina-fria/")
        self.assertContains(r, "Linha um.")

    def test_media_servida_em_debug(self):
        from django.conf import settings

        self.assertEqual(settings.MEDIA_URL, "/midia/")
        src = str(settings.BASE_DIR / "core")
        self.assertFalse(str(settings.MEDIA_ROOT).startswith(src))
