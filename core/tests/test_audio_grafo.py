import json
import os
import tempfile
from io import StringIO
from pathlib import Path
from unittest import mock

import httpx
from django.core.management import call_command
from django.test import SimpleTestCase


class AudioGrafoTests(SimpleTestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.pasta = Path(self.tmp.name)
        self.grafo = self.pasta / "grafo.json"
        self.saida = self.pasta / "manifesto.json"
        self.chaves = self.pasta / "chaves.json"
        self.chaves.write_text(
            json.dumps(
                {"api_key": "segredo-ficticio", "base_url": "https://audio.invalid/"}
            )
        )
        self.blocos = [
            {"id": n, "narracao": f"Fala {n}", "som": f"Som {n}"} for n in (1, 2)
        ]
        self.ambiente = mock.patch.dict(
            os.environ,
            {
                "IMAGETOOLS_API_URL": "https://midia.invalid",
                "IMAGETOOLS_API_KEY": "upload-ficticio",
            },
        )
        self.ambiente.start()
        self.addCleanup(self.ambiente.stop)

    def executar(self, **kwargs):
        self.grafo.write_text(
            json.dumps({"serie": "serie-teste", "blocos": self.blocos})
        )
        self.out, self.err = StringIO(), StringIO()
        call_command(
            "gerar_audio_grafo",
            grafo=self.grafo,
            saida=self.saida,
            chaves=self.chaves,
            voz="voz-teste",
            max_narracoes=kwargs.pop("max_narracoes", 10),
            max_sons=kwargs.pop("max_sons", 10),
            max_caracteres=kwargs.pop("max_caracteres", 10000),
            stdout=self.out,
            stderr=self.err,
            **kwargs,
        )
        return json.loads(self.saida.read_text()) if self.saida.exists() else None

    def resposta(self):
        resp = mock.Mock(content=(bytes.fromhex("fffb9000") + bytes(413)) * 10)
        resp.json.return_value = {"uuid": "uuid-ficticio"}
        return resp

    @mock.patch("httpx.request")
    @mock.patch("httpx.post")
    def test_pedidos_manifesto_e_cache(self, post, upload):
        post.return_value = upload.return_value = self.resposta()
        self.blocos[1].update(narracao="Fala 1", som="Som 1")
        dados = self.executar()
        self.assertEqual(post.call_count, 2)
        self.assertEqual(upload.call_count, 2)
        self.assertEqual(
            post.call_args_list[0].args,
            ("https://audio.invalid/v1/text-to-speech/voz-teste",),
        )
        self.assertEqual(
            post.call_args_list[0].kwargs["json"],
            {"text": "Fala 1", "model_id": "eleven_multilingual_v2"},
        )
        self.assertEqual(
            post.call_args_list[0].kwargs["headers"], {"xi-api-key": "segredo-ficticio"}
        )
        self.assertEqual(
            post.call_args_list[1].args, ("https://audio.invalid/v1/sound-generation",)
        )
        self.assertEqual(
            post.call_args_list[1].kwargs["json"],
            {"text": "Som 1", "duration_seconds": 4},
        )
        pedido = upload.call_args.kwargs
        self.assertEqual(
            upload.call_args.args, ("POST", "https://midia.invalid/api/v2/media/")
        )
        self.assertEqual(pedido["headers"]["X-API-Key"], "upload-ficticio")
        self.assertEqual(pedido["data"]["folder"], "stargate/audio/serie-teste/")
        self.assertEqual(pedido["files"]["file"][2], "audio/mpeg")
        self.assertEqual(dados["1"], dados["2"])
        self.assertEqual(dados["1"]["narracao_uuid"], "uuid-ficticio")
        self.assertEqual(len(dados["1"]["narracao_sha"]), 64)
        self.executar()
        self.assertEqual(post.call_count, 2)
        self.assertEqual(upload.call_count, 2)

    @mock.patch("httpx.request")
    @mock.patch("httpx.post")
    def test_tetos(self, post, upload):
        post.return_value = upload.return_value = self.resposta()
        dados = self.executar(max_narracoes=1, max_sons=0)
        self.assertEqual(post.call_count, 1)
        self.assertIsNone(dados["2"]["narracao_uuid"])
        self.assertIsNone(dados["1"]["som_uuid"])

    @mock.patch("httpx.request")
    @mock.patch("httpx.post")
    def test_seco_sem_rede_nem_arquivos(self, post, upload):
        self.executar(seco=True)
        post.assert_not_called()
        upload.assert_not_called()
        self.assertFalse(self.saida.exists())
        self.assertFalse(self.saida.with_name(self.saida.name + ".cache.json").exists())

    @mock.patch("httpx.request")
    @mock.patch("httpx.post")
    def test_erros_seguem_sem_vazar_segredo(self, post, upload):
        post.side_effect = [
            httpx.ConnectError("segredo-ficticio"),
            self.resposta(),
            self.resposta(),
            self.resposta(),
        ]
        upload.return_value = self.resposta()
        dados = self.executar()
        self.assertEqual(post.call_count, 4)
        self.assertIsNone(dados["1"]["narracao_uuid"])
        self.assertEqual(dados["2"]["narracao_uuid"], "uuid-ficticio")
        self.assertNotIn("segredo-ficticio", self.err.getvalue())
        self.assertIn("1 erros", self.out.getvalue())

    @mock.patch("httpx.request")
    @mock.patch("httpx.post")
    def test_retomada_upload_sem_regerar(self, post, upload):
        post.return_value = self.resposta()
        upload.side_effect = httpx.ConnectError("falha")
        self.executar(max_narracoes=1, max_sons=0)
        upload.side_effect = None
        upload.return_value = self.resposta()
        dados = self.executar(max_narracoes=1, max_sons=0)
        self.assertEqual(post.call_count, 1)
        self.assertEqual(dados["1"]["narracao_uuid"], "uuid-ficticio")

    @mock.patch("httpx.request")
    @mock.patch("httpx.post")
    def test_teto_caracteres_e_duracao(self, post, upload):
        post.return_value = upload.return_value = self.resposta()
        dados = self.executar(max_caracteres=6)
        self.assertEqual(post.call_count, 1)
        self.assertAlmostEqual(dados["1"]["duracao"], 0.261, places=3)
        self.assertIsNone(dados["2"]["duracao"])
        self.executar(max_caracteres=0)
        self.assertEqual(post.call_count, 1)
        self.assertEqual(json.loads(self.saida.read_text())["1"]["duracao"], 0.261)

    @mock.patch("httpx.request")
    @mock.patch("httpx.post")
    def test_base_com_v1_sem_duplicar_versao(self, post, upload):
        post.return_value = upload.return_value = self.resposta()
        self.chaves.write_text(
            json.dumps(
                {"api_key": "segredo-ficticio", "base_url": "https://audio.invalid/v1/"}
            )
        )
        self.executar(max_narracoes=1, max_sons=1)
        self.assertEqual(
            [chamada.args[0] for chamada in post.call_args_list],
            [
                "https://audio.invalid/v1/text-to-speech/voz-teste",
                "https://audio.invalid/v1/sound-generation",
            ],
        )
