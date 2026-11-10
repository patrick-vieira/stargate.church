import json

from django.contrib.auth import get_user_model
from django.test import Client, TestCase, override_settings
from django.urls import reverse

from core import placar
from core.models import Ato, VotoPlacar
from leitores.models import UsoDiario

User = get_user_model()
URL = "/placar/voto/"


class VotoBase(TestCase):
    fixtures = ["placar_post"]

    def setUp(self):
        self.user = User.objects.create_user("a@b.com", "a@b.com", "uma-senha-forte-91")
        self.client.force_login(self.user)

    def votar(self, obra="her-2013", x=4, y=3, client=None, **extra):
        corpo = {"obra": obra, "proximidade": x, "preocupacao": y, **extra}
        return (client or self.client).post(
            URL, json.dumps(corpo), content_type="application/json"
        )


class VotoTests(VotoBase):
    def test_rota(self):
        self.assertEqual(reverse("core:placar_voto"), URL)

    def test_so_post(self):
        self.assertEqual(self.client.get(URL).status_code, 405)

    def test_anonimo_401(self):
        r = self.votar(client=Client())
        self.assertEqual(r.status_code, 401)
        self.assertFalse(VotoPlacar.objects.exists())

    def test_anonimo_com_corpo_invalido_tambem_401(self):
        r = Client().post(URL, "x", content_type="application/json")
        self.assertEqual(r.status_code, 401)

    def test_voto_valido_grava_e_devolve_media(self):
        r = self.votar(x=4, y=3)
        self.assertEqual(r.status_code, 200)
        corpo = r.json()
        self.assertEqual(corpo["n"], 1)
        self.assertEqual(corpo["proximidade"], 4)
        self.assertEqual(corpo["preocupacao"], 3)
        voto = VotoPlacar.objects.get()
        self.assertEqual(
            (voto.utilizador, voto.obra, voto.proximidade, voto.preocupacao),
            (self.user, "her-2013", 4, 3),
        )
        self.assertEqual(UsoDiario.objects.get(tipo="voto").quantidade, 1)

    def test_media_com_dois_leitores(self):
        outro = User.objects.create_user("c@d.com", "c@d.com", "outra-senha-forte-91")
        self.votar(x=4, y=2)
        c2 = Client()
        c2.force_login(outro)
        r = self.votar(x=1, y=5, client=c2)
        self.assertEqual(r.json()["n"], 2)
        self.assertEqual(r.json()["proximidade"], 2.5)
        self.assertEqual(r.json()["preocupacao"], 3.5)

    def test_formulario_tambem_serve(self):
        r = self.client.post(
            URL, {"obra": "moon-2009", "proximidade": "2", "preocupacao": "0"}
        )
        self.assertEqual(r.status_code, 200)
        self.assertEqual(VotoPlacar.objects.get().preocupacao, 0)

    def test_repeticao_atualiza_a_mesma_linha(self):
        self.votar(x=1, y=1)
        r = self.votar(x=5, y=4)
        self.assertEqual(r.status_code, 200)
        self.assertEqual(VotoPlacar.objects.count(), 1)
        voto = VotoPlacar.objects.get()
        self.assertEqual((voto.proximidade, voto.preocupacao), (5, 4))
        self.assertEqual(r.json()["n"], 1)

    def test_obras_diferentes_sao_linhas_diferentes(self):
        self.votar("her-2013")
        self.votar("moon-2009")
        self.assertEqual(VotoPlacar.objects.count(), 2)

    @override_settings(STARGATE_TECTO_VOTO=2)
    def test_tecto_esgotado_429(self):
        self.assertEqual(self.votar("her-2013").status_code, 200)
        self.assertEqual(self.votar("moon-2009").status_code, 200)
        r = self.votar("portal-2007")
        self.assertEqual(r.status_code, 429)
        self.assertFalse(VotoPlacar.objects.filter(obra="portal-2007").exists())

    @override_settings(STARGATE_TECTO_VOTO=1)
    def test_voto_invalido_nao_gasta_o_tecto(self):
        self.assertEqual(self.votar(x=9).status_code, 400)
        self.assertFalse(UsoDiario.objects.filter(tipo="voto").exists())
        self.assertEqual(self.votar().status_code, 200)

    def test_notas_e_obra_invalidas_400(self):
        ruins = [
            {"obra": "nao-existe"},
            {"x": 6},
            {"x": -1},
            {"y": 6},
            {"x": 1.5},
            {"x": True},
            {"x": "abc"},
            {"x": None},
            {"obra": ""},
            {"obra": 7},
        ]
        for mudanca in ruins:
            with self.subTest(mudanca=mudanca):
                corpo = {"obra": "her-2013", "proximidade": 3, "preocupacao": 3}
                for k, v in mudanca.items():
                    corpo[{"x": "proximidade", "y": "preocupacao"}.get(k, k)] = v
                r = self.client.post(
                    URL, json.dumps(corpo), content_type="application/json"
                )
                self.assertEqual(r.status_code, 400)
        self.assertFalse(VotoPlacar.objects.exists())

    def test_corpo_sem_json_400(self):
        for bruto in ("não é json", "[1, 2]", ""):
            with self.subTest(bruto=bruto):
                r = self.client.post(URL, bruto, content_type="application/json")
                self.assertEqual(r.status_code, 400)

    def test_notas_nos_extremos(self):
        self.assertEqual(self.votar(x=0, y=5).status_code, 200)
        self.assertEqual(self.votar(x=5, y=0).status_code, 200)

    def test_csrf_e_exigido(self):
        c = Client(enforce_csrf_checks=True)
        c.force_login(self.user)
        self.assertEqual(self.votar(client=c).status_code, 403)
        self.assertFalse(VotoPlacar.objects.exists())

    def test_tecto_voto_por_omissao_30(self):
        from django.conf import settings

        from leitores import tecto

        self.assertEqual(settings.STARGATE_TECTO_VOTO, 30)
        self.assertEqual(tecto.limite("voto"), 30)


class PaginaDoPlacarTests(VotoBase):
    def setUp(self):
        super().setUp()
        self.url = reverse("core:imersivo", args=["o-placar"])

    def _dados(self, resposta):
        return resposta.context["placar_dados"]

    def test_logado_ve_o_formulario_e_o_cookie_csrf(self):
        r = self.client.get(self.url)
        self.assertContains(r, 'id="pl-voto"')
        self.assertContains(r, 'id="pl-f-obra"')
        self.assertNotContains(r, 'id="pl-entrar"')
        self.assertIn("csrftoken", r.cookies)
        self.assertTrue(self._dados(r)["logado"])
        self.assertEqual(self._dados(r)["voto_url"], URL)

    def test_anonimo_ve_o_convite_a_entrar(self):
        r = Client().get(self.url)
        self.assertContains(r, 'id="pl-entrar"')
        self.assertContains(r, reverse("leitores:entrar"))
        self.assertNotContains(r, 'id="pl-voto"')
        self.assertContains(r, 'id="pl-f-camada"')
        self.assertFalse(self._dados(r)["logado"])

    def test_aviso_honesto_sem_texto_livre(self):
        r = self.client.get(self.url)
        self.assertContains(r, "Isto não é pesquisa científica")
        self.assertContains(r, "sem texto livre")
        self.assertNotContains(r, "simulada")
        self.assertNotContains(r, "Dados locais")
        self.assertNotContains(r, 'type="text"')
        self.assertNotContains(r, "<textarea")

    def test_medias_reais_entram_no_contexto_e_no_json(self):
        self.votar("her-2013", 4, 2)
        outro = User.objects.create_user("c@d.com", "c@d.com", "outra-senha-forte-91")
        c2 = Client()
        c2.force_login(outro)
        self.votar("her-2013", 2, 4, client=c2)
        r = Client().get(self.url)
        medias = self._dados(r)["medias"]
        self.assertEqual(list(medias), ["her-2013"])
        self.assertEqual(
            medias["her-2013"], {"proximidade": 3.0, "preocupacao": 3.0, "n": 2}
        )
        self.assertEqual(r.context["placar_total_votos"], 2)
        self.assertContains(r, '"her-2013": {"proximidade": 3.0')

    def test_sem_votos_nao_ha_medias(self):
        r = self.client.get(self.url)
        self.assertEqual(self._dados(r)["medias"], {})
        self.assertEqual(r.context["placar_total_votos"], 0)

    def test_o_leitor_recebe_so_o_proprio_voto(self):
        self.votar("her-2013", 4, 2)
        outro = User.objects.create_user("c@d.com", "c@d.com", "outra-senha-forte-91")
        c2 = Client()
        c2.force_login(outro)
        r = c2.get(self.url)
        self.assertEqual(self._dados(r)["meus"], {})
        r = self.client.get(self.url)
        self.assertEqual(self._dados(r)["meus"], {"her-2013": [4, 2]})

    def test_dados_pessoais_fora_do_json(self):
        self.votar()
        r = self.client.get(self.url)
        self.assertNotIn("a@b.com", json.dumps(r.context["placar_dados"]))


class PreviaDoHubTests(TestCase):
    def ato(self, previa):
        return Ato(
            titulo="T",
            texto="x",
            efeito="grelha:posts",
            parametros={"previa": previa},
        )

    def test_id_resolve_titulo_e_posicao_a_partir_do_placar(self):
        her = placar.obra("her-2013")
        (p,) = self.ato([{"id": "her-2013"}]).previa_pontos
        self.assertEqual(p["obra"], her["titulo"])
        self.assertEqual(p["x"], her["proximidade"] / 5 * 100)
        self.assertEqual(p["y"], her["preocupacao"] / 5 * 100)
        self.assertEqual(p["cx"], round(50 + p["x"] * 3.3, 1))

    def test_validacao_aceita_ids_e_formato_antigo(self):
        self.ato([{"id": "her-2013"}]).clean()
        self.ato([{"obra": "R.U.R. (1920)", "x": 25, "y": 70}]).clean()
        self.ato([{"id": "her-2013"}, {"obra": "A", "x": 1, "y": 2}]).clean()

    def test_validacao_recusa_id_desconhecido_ou_misturado(self):
        from django.core.exceptions import ValidationError

        for ruim in (
            [{"id": "nao-existe"}],
            [{"id": 3}],
            [{"id": "her-2013", "x": 1}],
            [{"id": "her-2013", "obra": "A"}],
        ):
            with self.subTest(valor=ruim), self.assertRaises(ValidationError):
                self.ato(ruim).clean()

    def test_formato_antigo_continua_a_funcionar(self):
        (p,) = self.ato([{"obra": "R.U.R. (1920)", "x": 25, "y": 70}]).previa_pontos
        self.assertEqual((p["obra"], p["x"], p["y"]), ("R.U.R. (1920)", 25, 70))

    def test_previa_do_hub_le_os_mesmos_dados_que_o_placar(self):
        from django.core.management import call_command

        call_command("loaddata", "imersivo_hub_decadas", verbosity=0)
        hub = Ato.objects.get(efeito="grelha:posts")
        ids = [p["id"] for p in hub.parametros["previa"]]
        self.assertEqual(len(ids), 3)
        pontos = hub.previa_pontos
        self.assertEqual(len(pontos), 3)
        for id_, ponto in zip(ids, pontos, strict=True):
            obra = placar.obra(id_)
            self.assertIsNotNone(obra)
            self.assertEqual(ponto["obra"], obra["titulo"])
            self.assertEqual(ponto["x"], obra["proximidade"] * 20)
            self.assertEqual(ponto["y"], obra["preocupacao"] * 20)
        hub.full_clean()

    def test_pagina_do_hub_mostra_os_titulos_do_placar(self):
        from django.core.management import call_command

        from core.models import PostImersivo, Serie

        call_command("loaddata", "imersivo_hub_decadas", verbosity=0)
        Serie.objects.create(
            slug="ia-na-ficcao",
            titulo="S",
            publicado=True,
            hub=PostImersivo.objects.get(slug="ia-na-ficcao"),
        )
        r = self.client.get("/series/ia-na-ficcao/")
        for id_ in ("rur-1920", "i-robot-book-1950", "her-2013"):
            self.assertContains(r, placar.obra(id_)["titulo"])
