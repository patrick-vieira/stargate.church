import os
import tempfile
from io import StringIO
from pathlib import Path
from unittest import mock

from django.core.management import call_command
from django.core.management.base import CommandError
from django.test import SimpleTestCase, TestCase, override_settings

from core.models import Episodio
from core.servicos import imagetools

from .test_series import FIXTURES

HTTP = "core.servicos.imagetools._http"
BASE = "https://it.invalid"  # domínio reservado: nunca resolve
AMBIENTE = {"IMAGETOOLS_API_URL": BASE + "/", "IMAGETOOLS_API_KEY": "chave-de-teste"}
SEM_AMBIENTE = {k: "" for k in (*AMBIENTE, "IMAGETOOLS_CREDENCIAIS")}


class ClienteTests(SimpleTestCase):
    def setUp(self):
        self.video = Path(tempfile.mkdtemp(prefix="it-teste-")) / "video.mp4"
        self.video.write_bytes(b"v")

    def test_envio_com_url_na_resposta_nao_faz_get(self):
        resp = {"uuid": "u-1", "file_url": "https://cdn.invalid/u-1.mp4"}
        with (
            mock.patch.dict(os.environ, AMBIENTE),
            mock.patch(HTTP, return_value=resp) as http,
        ):
            uuid, url = imagetools.enviar_video(self.video)
        self.assertEqual((uuid, url), ("u-1", "https://cdn.invalid/u-1.mp4"))
        http.assert_called_once_with(
            "POST",
            f"{BASE}/api/v2/media/",
            "chave-de-teste",
            ficheiro=self.video,
        )

    def test_file_url_vazio_cai_no_get(self):
        respostas = [
            {"uuid": "u-2", "file_url": ""},
            {"uuid": "u-2", "file_url": "https://cdn.invalid/u-2.mp4"},
        ]
        with (
            mock.patch.dict(os.environ, AMBIENTE),
            mock.patch(HTTP, side_effect=respostas) as http,
        ):
            uuid, url = imagetools.enviar_video(self.video)
        self.assertEqual(url, "https://cdn.invalid/u-2.mp4")
        self.assertEqual(
            http.call_args_list[1],
            mock.call("GET", f"{BASE}/api/v2/media/u-2/", "chave-de-teste"),
        )

    def test_sem_url_depois_do_get_e_erro(self):
        with (
            mock.patch.dict(os.environ, AMBIENTE),
            mock.patch(HTTP, return_value={"uuid": "u-3", "file_url": ""}),
        ):
            with self.assertRaisesMessage(imagetools.ImageToolsErro, "file_url"):
                imagetools.enviar_video(self.video)

    def test_resposta_sem_uuid_e_erro(self):
        with mock.patch.dict(os.environ, AMBIENTE), mock.patch(HTTP, return_value={}):
            with self.assertRaisesMessage(imagetools.ImageToolsErro, "uuid"):
                imagetools.enviar_video(self.video)

    def test_falta_de_variaveis_diz_quais(self):
        with mock.patch.dict(os.environ, SEM_AMBIENTE), mock.patch(HTTP) as http:
            with self.assertRaises(imagetools.ImageToolsErro) as ctx:
                imagetools.enviar_video(self.video)
        http.assert_not_called()
        msg = str(ctx.exception)
        self.assertIn("IMAGETOOLS_API_URL", msg)
        self.assertIn("IMAGETOOLS_API_KEY", msg)

    def test_so_a_chave_em_falta(self):
        amb = {**AMBIENTE, "IMAGETOOLS_API_KEY": ""}
        with mock.patch.dict(os.environ, amb):
            with self.assertRaises(imagetools.ImageToolsErro) as ctx:
                imagetools.configuracao()
        self.assertNotIn("IMAGETOOLS_API_URL", str(ctx.exception))

    def _credenciais(self, conteudo):
        caminho = Path(tempfile.mkdtemp(prefix="it-cred-")) / "cred.json"
        caminho.write_text(conteudo)
        return str(caminho)

    def test_le_credenciais_do_json(self):
        cred = self._credenciais('{"url": "https://j.invalid/", "token": "tok-falso"}')
        amb = {**SEM_AMBIENTE, "IMAGETOOLS_CREDENCIAIS": cred}
        with mock.patch.dict(os.environ, amb):
            self.assertEqual(
                imagetools.configuracao(), ("https://j.invalid", "tok-falso")
            )

    def test_variaveis_tem_precedencia_sobre_o_json(self):
        cred = self._credenciais('{"url": "https://j.invalid", "token": "tok-json"}')
        amb = {**AMBIENTE, "IMAGETOOLS_CREDENCIAIS": cred}
        with mock.patch.dict(os.environ, amb):
            self.assertEqual(imagetools.configuracao(), (BASE, "chave-de-teste"))
        parcial = {
            **SEM_AMBIENTE,
            "IMAGETOOLS_API_KEY": "so-chave",
            "IMAGETOOLS_CREDENCIAIS": cred,
        }
        with mock.patch.dict(os.environ, parcial):
            self.assertEqual(
                imagetools.configuracao(), ("https://j.invalid", "so-chave")
            )

    def test_json_incompleto_diz_o_que_falta_sem_token(self):
        cred = self._credenciais('{"token": "segredo-nunca-impresso"}')
        amb = {**SEM_AMBIENTE, "IMAGETOOLS_CREDENCIAIS": cred}
        with mock.patch.dict(os.environ, amb):
            with self.assertRaises(imagetools.ImageToolsErro) as ctx:
                imagetools.configuracao()
        self.assertIn("IMAGETOOLS_API_URL", str(ctx.exception))
        self.assertNotIn("segredo-nunca-impresso", str(ctx.exception))

    def test_json_invalido_ou_ausente_e_erro_sem_conteudo(self):
        cred = self._credenciais("token=segredo-nunca-impresso")
        for caminho in (cred, cred + ".nao-existe"):
            amb = {**SEM_AMBIENTE, "IMAGETOOLS_CREDENCIAIS": caminho}
            with mock.patch.dict(os.environ, amb):
                with self.assertRaises(imagetools.ImageToolsErro) as ctx:
                    imagetools.configuracao()
            self.assertNotIn("segredo-nunca-impresso", str(ctx.exception))

    def test_cabecalhos_enviados(self):
        import sys
        import types

        resp = mock.Mock()
        resp.json.return_value = {}
        falso = types.ModuleType("httpx")  # o venv de teste não precisa do httpx
        falso.HTTPError = type("HTTPError", (Exception,), {})
        falso.request = mock.Mock(return_value=resp)
        with mock.patch.dict(sys.modules, {"httpx": falso}):
            imagetools._http("GET", BASE + "/x", "chave-de-teste")
        req = falso.request
        cab = req.call_args.kwargs["headers"]
        self.assertEqual(cab["X-API-Key"], "chave-de-teste")
        self.assertEqual(cab["User-Agent"], "stargate.church/importar_midia")
        self.assertNotIn("Authorization", cab)

    def test_codigo_sem_valores_de_configuracao(self):
        fonte = Path(imagetools.__file__).read_text()
        self.assertNotIn("http://", fonte)
        self.assertNotIn("https://", fonte)


TMP = tempfile.mkdtemp(prefix="it-media-")


@override_settings(MEDIA_ROOT=TMP)
class ImportarImageToolsTests(TestCase):
    fixtures = FIXTURES

    def setUp(self):
        self.origem = Path(tempfile.mkdtemp(prefix="it-origem-"))
        for n in (0, 1):
            p = self.origem / "videos" / f"ia-ficcao-{n:02d}"
            p.mkdir(parents=True)
            (p / "video.mp4").write_bytes(b"v")
            (p / "poster.jpg").write_bytes(b"p")

    def _cmd(self, **kw):
        out = StringIO()
        call_command(
            "importar_midia",
            "--origem",
            str(self.origem),
            stdout=out,
            stderr=StringIO(),
            **kw,
        )
        return out.getvalue()

    def test_padrao_local_nao_toca_o_imagetools(self):
        with mock.patch(HTTP) as http:
            self._cmd()
        http.assert_not_called()
        e = Episodio.objects.get(numero=1)
        self.assertTrue(e.video)
        self.assertEqual(e.video_url, "")

    def test_destino_imagetools_guarda_url_e_uuid(self):
        resp = {"uuid": "u-9", "file_url": "https://cdn.invalid/u-9.mp4"}
        with (
            mock.patch.dict(os.environ, AMBIENTE),
            mock.patch(HTTP, return_value=resp) as http,
        ):
            self._cmd(destino="imagetools")
        self.assertEqual(http.call_count, 2)  # episódios 0 e 1
        e = Episodio.objects.get(numero=1)
        self.assertEqual(e.video_url, "https://cdn.invalid/u-9.mp4")
        self.assertEqual(e.video_imagetools_uuid, "u-9")
        self.assertFalse(e.video)
        self.assertTrue(e.poster)  # o resto continua local

    def test_recomprime_antes_de_enviar(self):
        p = self.origem / "videos" / "ia-ficcao-01" / "video.mp4"
        with open(p, "wb") as f:
            f.truncate(1024 * 1024 + 1)
        enviados = []

        def falso_ffmpeg(src, dst, alvo):
            Path(dst).write_bytes(b"pequeno")

        def falso_http(metodo, url, chave, ficheiro=None):
            enviados.append(Path(ficheiro).read_bytes() if ficheiro else None)
            return {"uuid": "u", "file_url": "https://cdn.invalid/x.mp4"}

        mod = "core.management.commands.importar_midia"
        with (
            mock.patch.dict(os.environ, AMBIENTE),
            mock.patch(f"{mod}.recomprimir_ffmpeg", side_effect=falso_ffmpeg) as rec,
            mock.patch(HTTP, side_effect=falso_http),
        ):
            self._cmd(destino="imagetools", limite_mb=1, alvo_mb=1)
        rec.assert_called_once()
        self.assertIn(b"pequeno", enviados)

    def test_sem_variaveis_erro_claro_e_nada_escrito(self):
        with mock.patch.dict(os.environ, SEM_AMBIENTE), mock.patch(HTTP) as http:
            with self.assertRaisesMessage(CommandError, "IMAGETOOLS_API_URL"):
                self._cmd(destino="imagetools")
        http.assert_not_called()
        self.assertFalse(Episodio.objects.exclude(poster="").exists())

    def test_falha_do_imagetools_vira_erro_de_comando(self):
        with (
            mock.patch.dict(os.environ, AMBIENTE),
            mock.patch(HTTP, side_effect=imagetools.ImageToolsErro("boom")),
        ):
            with self.assertRaisesMessage(CommandError, "boom"):
                self._cmd(destino="imagetools")

    def test_dry_run_nao_envia(self):
        with mock.patch.dict(os.environ, AMBIENTE), mock.patch(HTTP) as http:
            self._cmd(destino="imagetools", dry_run=True)
        http.assert_not_called()


@override_settings(MEDIA_ROOT=TMP)
class PlayerUrlTests(TestCase):
    fixtures = FIXTURES

    URL = "/series/ia-na-ficcao/a-maquina-fria/"

    def test_url_externo_tem_prioridade_sobre_o_ficheiro(self):
        e = Episodio.objects.get(numero=1)
        e.video = "episodios/x/video.mp4"
        e.video_url = "https://cdn.invalid/e1.mp4"
        e.save()
        html = self.client.get(self.URL).content.decode()
        self.assertIn('src="https://cdn.invalid/e1.mp4"', html)
        self.assertNotIn("/midia/episodios/x/video.mp4", html)

    def test_so_url_externo_mostra_o_player(self):
        e = Episodio.objects.get(numero=1)
        e.video_url = "https://cdn.invalid/e1.mp4"
        e.save()
        self.assertContains(self.client.get(self.URL), "data-midia")

    def test_so_ficheiro_continua_a_funcionar(self):
        e = Episodio.objects.get(numero=1)
        e.video = "episodios/x/video.mp4"
        e.save()
        self.assertContains(
            self.client.get(self.URL), 'src="/midia/episodios/x/video.mp4"'
        )
