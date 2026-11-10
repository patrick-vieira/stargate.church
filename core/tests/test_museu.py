import copy
import json
import shutil
import subprocess
import tempfile
import uuid
from io import StringIO
from pathlib import Path
from unittest.mock import patch

from django.conf import settings
from django.core.exceptions import ValidationError
from django.core.management import call_command
from django.core.management.base import CommandError
from django.test import TestCase
from django.urls import reverse

from core.models import GrafoMuseu, Serie
from core.servicos.imagetools import ImageToolsErro, consultar_audio, consultar_video
from core.servicos.museu import apresentar, validar_grafo


def grafo():
    return {
        "serie": "serie-ficticia",
        "blocos": [
            {
                "id": 1,
                "numero": 1,
                "tipo": "texto",
                "polo": "neutro",
                "profundidade": 0,
                "titulo": "[MOCK] Teste",
                "texto": "Texto fictício.",
                "escolhas": [{"tipo": "seguir", "rotulo": "Continuar", "destino": 1}],
            }
        ],
    }


class MuseuTests(TestCase):
    def importar(self, dados, manifesto=None):
        with tempfile.TemporaryDirectory() as pasta:
            ficheiro = Path(pasta) / "grafo.json"
            ficheiro.write_text(json.dumps(dados))
            argumentos = [str(ficheiro)]
            if manifesto is not None:
                audio = Path(pasta) / "audio.json"
                audio.write_text(json.dumps(manifesto))
                argumentos.extend(["--manifesto-audio", str(audio)])
            call_command("importar_grafo", *argumentos)

    def grafo_energia(self):
        dados = grafo()
        dados["serie"] = "mock-energia-sem-fim"
        modelo = dados["blocos"][0]
        dados["blocos"] = []
        for numero in range(1, 25):
            no = copy.deepcopy(modelo)
            no.update(id=numero, numero=numero, titulo=f"[MOCK] Bloco {numero}")
            no["escolhas"][0]["destino"] = numero + 1 if numero < 24 else 1
            dados["blocos"].append(no)
        return dados

    def manifesto_ficticio(self):
        return {
            str(numero): {
                **{
                    f"{tipo}_uuid": str(
                        uuid.uuid5(uuid.NAMESPACE_URL, f"ficticio-{numero}-{tipo}")
                    )
                    for tipo in ("narracao", "som")
                },
                "narracao_sha": "a" * 64,
                "som_sha": "b" * 64,
            }
            for numero in range(1, 25)
        }

    def importar_seis_series(self, **opcoes):
        pasta = Path(__file__).resolve().parents[1] / "dados" / "grafos"
        argumentos = []
        with tempfile.TemporaryDirectory() as temporario:
            for ficheiro in sorted(pasta.glob("*.grafo.json")):
                slug = json.loads(ficheiro.read_text(encoding="utf-8"))["serie"]
                manifesto = Path(temporario) / f"{slug}.json"
                manifesto.write_text(json.dumps(self.manifesto_ficticio()))
                argumentos.extend(["--manifesto-audio", f"{slug}={manifesto}"])
            call_command("importar_series_museu", *argumentos, **opcoes)

    def test_importacao_repetivel_e_nao_publica(self):
        self.importar(grafo())
        self.importar(grafo())
        self.assertEqual(GrafoMuseu.objects.count(), 1)
        self.assertFalse(Serie.objects.get().publicado)

    def test_invalido_nao_escreve(self):
        dados = grafo()
        dados["blocos"][0]["escolhas"][0]["destino"] = 99
        with self.assertRaises(CommandError):
            self.importar(dados)
        self.assertEqual(Serie.objects.count(), 0)

    def test_seis_fixtures_editoriais_validas(self):
        pasta = Path(__file__).resolve().parents[1] / "dados" / "grafos"
        ficheiros = sorted(pasta.glob("*.grafo.json"))
        self.assertEqual(len(ficheiros), 6)
        slugs = set()
        for ficheiro in ficheiros:
            dados = json.loads(ficheiro.read_text(encoding="utf-8"))
            with self.subTest(ficheiro=ficheiro.name):
                validar_grafo(dados)
            slugs.add(dados["serie"])
        self.assertEqual(len(slugs), 6)

    def test_importador_das_seis_series_e_repetivel_sem_publicar(self):
        saida = StringIO()
        self.importar_seis_series(stdout=saida)
        self.importar_seis_series(stdout=saida)

        self.assertEqual(GrafoMuseu.objects.count(), 6)
        self.assertFalse(Serie.objects.filter(publicado=True).exists())
        self.assertIn("a publicação existente foi preservada", saida.getvalue())

    def test_importador_preserva_series_publicadas_na_reimportacao(self):
        saida = StringIO()
        self.importar_seis_series(publicar=True, stdout=saida)
        self.importar_seis_series(stdout=saida)

        self.assertEqual(Serie.objects.filter(publicado=True).count(), 6)
        self.assertIn("a publicação existente foi preservada", saida.getvalue())

    def test_manifestos_invalidos_no_lote_nao_importam_serie_alguma(self):
        pasta = Path(__file__).resolve().parents[1] / "dados" / "grafos"
        argumentos = []
        with tempfile.TemporaryDirectory() as temporario:
            for indice, ficheiro in enumerate(sorted(pasta.glob("*.grafo.json"))):
                slug = json.loads(ficheiro.read_text(encoding="utf-8"))["serie"]
                manifesto = self.manifesto_ficticio()
                if indice == 5:
                    del manifesto["24"]
                caminho = Path(temporario) / f"{slug}.json"
                caminho.write_text(json.dumps(manifesto))
                argumentos.extend(["--manifesto-audio", f"{slug}={caminho}"])
            with self.assertRaises(CommandError):
                call_command("importar_series_museu", *argumentos)
        self.assertEqual(GrafoMuseu.objects.count(), 0)

    @patch(
        "core.servicos.imagetools.consultar_audio",
        return_value="https://cdn.invalid/audio.mp3",
    )
    def test_sete_series_importadas_com_audio_em_sala(self, consultar):
        self.importar_seis_series()
        dados = self.grafo_energia()
        manifesto = self.manifesto_ficticio()
        with tempfile.TemporaryDirectory() as temporario:
            grafo_path = Path(temporario) / "energia.json"
            audio_path = Path(temporario) / "energia.audio.json"
            grafo_path.write_text(json.dumps(dados))
            audio_path.write_text(json.dumps(manifesto))
            call_command(
                "importar_grafo", str(grafo_path), "--manifesto-audio", str(audio_path)
            )

        self.assertEqual(GrafoMuseu.objects.count(), 7)
        Serie.objects.update(publicado=True)
        for serie in Serie.objects.order_by("slug"):
            with self.subTest(serie=serie.slug):
                resposta = self.client.get(
                    reverse("core:museu_audio", args=[serie.slug, 1, "som"])
                )
                self.assertEqual(resposta.status_code, 200)
                self.assertEqual(
                    resposta.json(), {"url": "https://cdn.invalid/audio.mp3"}
                )
        self.assertEqual(consultar.call_count, 7)

    def test_lote_invalido_no_sexto_grafo_nao_inicia_escrita(self):
        from core.management.commands import importar_series_museu

        validar_real = importar_series_museu.validar_grafo
        chamadas = 0

        def invalida_sexto(dados):
            nonlocal chamadas
            chamadas += 1
            if chamadas == 6:
                raise ValidationError("falha editorial simulada")
            return validar_real(dados)

        with (
            patch.object(
                importar_series_museu, "validar_grafo", side_effect=invalida_sexto
            ),
            patch.object(Serie.objects, "get_or_create") as criar_serie,
            patch.object(GrafoMuseu.objects, "update_or_create") as gravar_grafo,
        ):
            with self.assertRaises(CommandError):
                call_command("importar_series_museu", stdout=StringIO())

        criar_serie.assert_not_called()
        gravar_grafo.assert_not_called()
        self.assertEqual(GrafoMuseu.objects.count(), 0)
        self.assertEqual(Serie.objects.count(), 0)

    def test_lote_reverte_importacoes_se_a_sexta_gravacao_falhar(self):
        atualizar_real = GrafoMuseu.objects.update_or_create
        chamadas = 0

        def falha_sexta_gravacao(*args, **kwargs):
            nonlocal chamadas
            chamadas += 1
            if chamadas == 6:
                raise RuntimeError("falha de gravação simulada")
            return atualizar_real(*args, **kwargs)

        with patch.object(
            GrafoMuseu.objects, "update_or_create", side_effect=falha_sexta_gravacao
        ):
            with self.assertRaises(RuntimeError):
                self.importar_seis_series(stdout=StringIO())

        self.assertEqual(chamadas, 6)
        self.assertEqual(GrafoMuseu.objects.count(), 0)
        self.assertEqual(Serie.objects.count(), 0)

    def test_vista_disponibiliza_seis_portas_e_ids_sem_colisao(self):
        call_command("importar_series_museu", publicar=True, stdout=StringIO())
        resposta = self.client.get(reverse("core:museu"))
        dados = resposta.context["dados"]

        self.assertEqual(len(dados["series"]), 6)
        self.assertEqual(len(dados["grafo"]["series"]), 6)
        ids = [no["id"] for no in dados["grafo"]["nos"]]
        self.assertEqual(len(ids), len(set(ids)))
        for serie in dados["series"]:
            self.assertContains(resposta, f"?serie={serie['slug']}")

    def test_valida_campos_e_topologia(self):
        base = grafo()
        for campo, valor in (
            ("tipo", []),
            ("polo", []),
            ("profundidade", True),
            ("texto", []),
            ("id", True),
            ("escolhas", []),
            ("fontes", [None]),
            ("narracao_imagetools_uuid", "uuid-ficticio"),
        ):
            with self.subTest(campo=campo):
                dados = copy.deepcopy(base)
                dados["blocos"][0][campo] = valor
                with self.assertRaises(ValidationError):
                    validar_grafo(dados)
        for duplicado in (True, False):
            dados = grafo()
            no = copy.deepcopy(dados["blocos"][0])
            if not duplicado:
                no.update(id=2, numero=2)
            dados["blocos"].append(no)
            with self.assertRaises(ValidationError):
                validar_grafo(dados)

    def test_vista_oculta_rascunho_e_entrega_json_seguro(self):
        self.importar(grafo())
        url = reverse("core:museu")
        resposta = self.client.get(url)
        self.assertEqual(resposta.status_code, 200)
        self.assertNotContains(resposta, "Texto fictício")
        Serie.objects.update(publicado=True)
        resposta = self.client.get(url)
        self.assertContains(resposta, "Texto fictício")
        self.assertContains(resposta, 'type="application/json"')
        self.assertContains(resposta, '<details class="series-museu">')
        self.assertContains(resposta, "<summary>Séries")
        self.assertContains(resposta, 'href="#n1"')
        self.assertContains(resposta, 'href="#principal"')
        dados = resposta.context["dados"]
        self.assertEqual(dados["grafo"]["nos"][0]["ligacoes"]["seguir"], 1)

    def test_vista_combina_grafos_publicados_com_ids_unicos(self):
        primeiro = grafo()
        segundo = grafo()
        segundo["serie"] = "outra-serie"
        self.importar(primeiro)
        self.importar(segundo)
        Serie.objects.update(publicado=True)

        resposta = self.client.get(reverse("core:museu"))
        dados = resposta.context["dados"]
        self.assertEqual(
            set(dados["grafo"]["series"]), {"serie-ficticia", "outra-serie"}
        )
        ids = [no["id"] for no in dados["grafo"]["nos"]]
        self.assertEqual(len(ids), len(set(ids)))
        self.assertEqual(
            {no["serie"] for no in dados["grafo"]["nos"]},
            {"serie-ficticia", "outra-serie"},
        )

    def test_serie_publicada_sem_grafo_exibe_fallback(self):
        Serie.objects.create(
            slug="sem-grafo", titulo="Série em preparação", publicado=True
        )
        resposta = self.client.get(reverse("core:museu"))
        self.assertEqual(resposta.status_code, 200)
        self.assertIsNone(resposta.context["dados"]["grafo"])
        self.assertEqual(resposta.context["dados"]["series"][0]["slug"], "sem-grafo")
        self.assertEqual(resposta.context["nos"], [])

    def test_adaptacao_camadas_dialogo(self):
        dados = grafo()
        dados["blocos"][0].update(
            tipo="camadas", camadas=[{"rotulo": "Abrir", "texto": "Camada fictícia"}]
        )
        validar_grafo(dados)
        serie = Serie(slug="ficticia", titulo="Fictícia")
        self.assertEqual(
            apresentar(serie, dados)["grafo"]["nos"][0]["camadas"][0]["texto"],
            "Camada fictícia",
        )

    def test_dialogo_e_saltos_de_profundidade(self):
        dados = grafo()
        dados["blocos"][0].update(
            tipo="dialogo",
            profundidade=2,
            dialogo={
                "personagem": {"nome": "Guia fictícia", "papel": "Guia"},
                "falas": ["Olá"],
                "respostas": [{"texto": "Voltar", "vai": 2}],
            },
        )
        segundo = copy.deepcopy(dados["blocos"][0])
        segundo.update(id=2, numero=2, tipo="texto", profundidade=0)
        dados["blocos"].append(segundo)
        dados["blocos"][0]["escolhas"] = [
            {"tipo": "subir", "rotulo": "Voltar ao início", "destino": 2}
        ]
        validar_grafo(dados)
        dados["blocos"][0]["escolhas"][0]["tipo"] = "aprofundar"
        with self.assertRaises(ValidationError):
            validar_grafo(dados)

    def test_falha_preserva_grafo_existente(self):
        self.importar(grafo())
        dados = grafo()
        dados["blocos"][0]["escolhas"] = []
        with self.assertRaises(CommandError):
            self.importar(dados)
        self.assertEqual(GrafoMuseu.objects.get().dados, grafo())

    def test_extras_preservam_editorial_e_colisao_24(self):
        dados = grafo()
        dados["serie"] = "mock-energia-sem-fim"
        modelo = dados["blocos"][0]
        dados["blocos"] = []
        for numero in range(1, 25):
            no = copy.deepcopy(modelo)
            no.update(
                id=numero, numero=numero, titulo=f"[MOCK] Bloco editorial {numero}"
            )
            no["escolhas"][0]["destino"] = numero + 1 if numero < 24 else 1
            dados["blocos"].append(no)
        antes = copy.deepcopy(dados)
        validar_grafo(dados)
        serie = Serie(slug=dados["serie"], titulo="Série fictícia")
        resultado = apresentar(serie, dados)["grafo"]
        self.assertEqual(dados, antes)
        self.assertEqual(len(resultado["nos"]), 28)
        por_id = {n["id"]: n for n in resultado["nos"]}
        self.assertEqual(por_id[24]["titulo"], "[MOCK] Bloco editorial 24")
        self.assertEqual(por_id[21]["ligacoes"]["seguir"], 22)
        self.assertEqual(por_id[21]["ligacoes"]["museu"], 27)
        self.assertEqual(
            {s["id"] for s in resultado["salas"]}, {"origens", "laboratorio", "futuros"}
        )
        self.assertEqual(resultado["visitas"][0]["passos"], [27, 1, 24, 25, 28, 26, 21])
        vistos, fila = set(), [resultado["entrada"]]
        while fila:
            atual = fila.pop()
            if atual not in vistos:
                vistos.add(atual)
                fila.extend(
                    v for v in por_id[atual]["ligacoes"].values() if v is not None
                )
                fila.extend(
                    r["vai"]
                    for r in por_id[atual].get("dialogo", {}).get("respostas", [])
                )
        self.assertEqual(vistos, set(por_id))

    def test_fontes_verificadas_no_html_sem_js(self):
        dados = grafo()
        dados["blocos"][0]["fontes"] = [
            {
                "titulo": "Fonte verificada",
                "url": "https://fonte.invalid/confirmada",
                "verificada": True,
            },
            {
                "titulo": "Fonte pendente",
                "url": "https://fonte.invalid/pendente",
                "verificada": False,
            },
        ]
        self.importar(dados)
        Serie.objects.update(publicado=True)
        resposta = self.client.get(reverse("core:museu"))
        self.assertContains(
            resposta, 'rel="noopener noreferrer">Fonte verificada</a></p>', html=False
        )
        self.assertContains(
            resposta,
            'rel="noopener noreferrer">Fonte pendente</a> · por verificar</p>',
            html=False,
        )

    def test_fluxo_javascript_para_pecas_ludico_e_sobrio(self):
        node = shutil.which("node")
        if not node:
            self.skipTest("Node necessário para executar os módulos ES puros.")
        pasta = settings.BASE_DIR / "static/museu"
        script = (Path(__file__).parent / "provar_museu.mjs").read_text()
        resultado = subprocess.run(
            [node, "--input-type=module", "-e", script, str(pasta)],
            capture_output=True,
            text=True,
            timeout=20,
            check=False,
        )
        self.assertEqual(resultado.returncode, 0, resultado.stdout + resultado.stderr)

    @patch("core.servicos.imagetools._http")
    @patch(
        "core.servicos.imagetools.configuracao",
        return_value=("https://media.invalid", "segredo-ficticio"),
    )
    def test_video_consulta_fresca_e_erros_seguros(self, config, http):
        http.return_value = {"file_url": "https://cdn.invalid/video.mp4"}
        self.assertEqual(
            consultar_video("uuid-ficticio"), "https://cdn.invalid/video.mp4"
        )
        consultar_video("uuid-ficticio")
        self.assertEqual(http.call_count, 2)
        self.assertEqual(
            consultar_audio("uuid-ficticio"), "https://cdn.invalid/video.mp4"
        )
        consultar_audio("uuid-ficticio")
        self.assertEqual(http.call_count, 4)
        http.side_effect = ImageToolsErro("segredo-ficticio")
        with self.assertRaisesMessage(ImageToolsErro, "Vídeo indisponível no momento."):
            consultar_video("uuid-ficticio")
        with self.assertRaisesMessage(ImageToolsErro, "Áudio indisponível no momento."):
            consultar_audio("uuid-ficticio")

    def test_video_rascunho_404_e_falha_segura(self):
        self.importar(grafo())
        url = reverse("core:museu_video", args=["serie-ficticia", 1])
        self.assertEqual(self.client.get(url).status_code, 404)
        Serie.objects.update(publicado=True)
        resposta = self.client.get(url)
        self.assertEqual(resposta.status_code, 503)
        self.assertEqual(resposta["Cache-Control"], "no-store")

    def test_manifesto_audio_valida_associa_apenas_uuids_e_e_repetivel(self):
        dados, manifesto = self.grafo_energia(), self.manifesto_ficticio()
        self.importar(dados, manifesto)
        self.importar(dados, manifesto)
        persistido = GrafoMuseu.objects.get().dados["blocos"]
        self.assertEqual(len(persistido), 24)
        self.assertEqual(
            persistido[0]["narracao_imagetools_uuid"], manifesto["1"]["narracao_uuid"]
        )
        self.assertEqual(
            persistido[23]["som_imagetools_uuid"], manifesto["24"]["som_uuid"]
        )
        self.assertNotIn("narracao_sha", persistido[0])
        apresentado = apresentar(
            Serie(slug="mock-energia-sem-fim", titulo="Fictícia"),
            {"blocos": persistido},
        )
        no = apresentado["grafo"]["nos"][0]
        self.assertEqual(
            no["narracao_audio_endpoint"],
            "/museu/mock-energia-sem-fim/audio/1/narracao/",
        )
        self.assertNotIn("narracao_imagetools_uuid", no)
        self.assertNotIn("som_imagetools_uuid", no)

    def test_manifesto_audio_invalido_nao_escreve(self):
        manifesto = self.manifesto_ficticio()
        del manifesto["24"]
        with self.assertRaises(CommandError):
            self.importar(self.grafo_energia(), manifesto)
        self.assertEqual(Serie.objects.count(), 0)

    @patch(
        "core.servicos.imagetools.consultar_audio",
        return_value="https://cdn.invalid/audio.mp3",
    )
    def test_audio_publicado_resolve_fresco_e_uuid_nao_arbitrario(self, consultar):
        self.importar(self.grafo_energia(), self.manifesto_ficticio())
        url = reverse("core:museu_audio", args=["mock-energia-sem-fim", 1, "narracao"])
        rascunho = self.client.get(url)
        self.assertEqual(rascunho.status_code, 404)
        self.assertEqual(rascunho["Cache-Control"], "no-store")
        Serie.objects.update(publicado=True)
        primeira = self.client.get(url)
        segunda = self.client.get(url)
        self.assertEqual(primeira.status_code, 200)
        self.assertEqual(segunda.status_code, 200)
        self.assertEqual(primeira.json(), {"url": "https://cdn.invalid/audio.mp3"})
        self.assertEqual(primeira["Cache-Control"], "no-store")
        self.assertEqual(consultar.call_count, 2)
        self.assertEqual(
            self.client.get(
                reverse("core:museu_audio", args=["mock-energia-sem-fim", 1, "outro"])
            ).status_code,
            404,
        )
        consultar.assert_called_with(self.manifesto_ficticio()["1"]["narracao_uuid"])
        consultar.side_effect = ImageToolsErro("segredo-ficticio")
        falha = self.client.get(url)
        self.assertEqual(falha.status_code, 503)
        self.assertEqual(falha["Cache-Control"], "no-store")
        self.assertNotContains(falha, "segredo-ficticio", status_code=503)
