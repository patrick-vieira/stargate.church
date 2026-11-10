from pathlib import Path
from urllib.parse import parse_qs, urlsplit

from django.template import engines
from django.test import RequestFactory, TestCase
from django.urls import reverse

from core.estilos import envelope
from core.models import PostImersivo


class EstilosTests(TestCase):
    def test_padrao_e_convite(self):
        resposta = self.client.get(reverse("core:home"))
        self.assertContains(resposta, 'data-envelope="base" data-estilo="3"')
        self.assertContains(resposta, "Experimente Bloco")
        self.assertContains(resposta, "Escolher aparência")
        self.assertIn("Cookie", resposta["Vary"])

    def test_viagem_apenas_na_noite_estrelada(self):
        for estilo in ("0", "3", "5"):
            for rota in ("/", "/noticias/", reverse("leitores:entrar")):
                with self.subTest(estilo=estilo, rota=rota):
                    resposta = self.client.get(rota, {"estilo": estilo})
                    self.assertEqual(resposta.context["estilo_base"], estilo)
                    for arquivo in ("css/viagem-estrelas.css", "js/viagem-estrelas.js"):
                        if estilo == "3":
                            self.assertContains(resposta, arquivo)
                        else:
                            self.assertNotContains(resposta, arquivo)

    def test_contexto_do_estilo_respeita_query_cookie_e_padrao(self):
        fabrica = RequestFactory()
        request = fabrica.get("/")
        self.assertEqual(envelope(request)["estilo_base"], "3")
        request.COOKIES["stargate_estilo"] = "5"
        self.assertEqual(envelope(request)["estilo_base"], "5")
        request = fabrica.get("/?estilo=3")
        request.COOKIES["stargate_estilo"] = "5"
        self.assertEqual(envelope(request)["estilo_base"], "3")

    def test_escolha_persiste_em_todas_as_paginas(self):
        for estilo in ("0", "3", "5"):
            resposta = self.client.get("/", {"estilo": estilo})
            cookie = resposta.cookies["stargate_estilo"]
            self.assertEqual(cookie.value, estilo)
            self.assertEqual(cookie["samesite"], "Lax")
            self.assertEqual(cookie["path"], "/")
            self.assertEqual(resposta["Cache-Control"], "private")
            for rota in ("/", "/noticias/", reverse("leitores:entrar")):
                pagina = self.client.get(rota)
                self.assertContains(pagina, f'data-estilo="{estilo}"')
                self.assertNotContains(pagina, "data-convite-estilo")

    def test_entrada_invalida_nao_vira_html_nem_cookie(self):
        for valor in ("99", '"><script>alert(1)</script>', ""):
            resposta = self.client.get("/", {"estilo": valor})
            self.assertContains(resposta, 'data-estilo="3"')
            self.assertNotIn("stargate_estilo", resposta.cookies)
        self.client.cookies["stargate_estilo"] = "invalido"
        self.assertContains(self.client.get("/"), 'data-estilo="3"')

    def test_query_tem_precedencia_e_cookie_https_seguro(self):
        self.client.cookies["stargate_estilo"] = "5"
        resposta = self.client.get("/?estilo=0", secure=True)
        self.assertContains(resposta, 'data-estilo="0"')
        self.assertTrue(resposta.cookies["stargate_estilo"]["secure"])

    def test_convite_dispensado(self):
        self.client.cookies["stargate_convite"] = "fechado"
        self.assertNotContains(self.client.get("/"), "data-convite-estilo")
        self.assertContains(self.client.get("/"), "Escolher aparência")

    def test_links_preservam_filtros_e_escapam_valores(self):
        request = RequestFactory().get("/noticias/?busca=a%26b&page=2&estilo=3")
        for opcao in envelope(request)["estilos_base"]:
            query = parse_qs(urlsplit(opcao["url"]).query)
            self.assertEqual(query["busca"], ["a&b"])
            self.assertEqual(query["page"], ["2"])
            self.assertEqual(query["estilo"], [opcao["valor"]])

    def test_post_imersivo_livre_de_envelope(self):
        post = PostImersivo.objects.create(
            titulo="Post livre", slug="post-livre", publicado=True
        )
        for estilo in ("0", "3", "5"):
            resposta = self.client.get(
                reverse("core:imersivo", args=[post.slug]), {"estilo": estilo}
            )
            self.assertContains(resposta, 'data-envelope="livre"')
            self.assertNotContains(resposta, "Escolher aparência")
            self.assertNotContains(resposta, "viagem-estrelas")

    def test_sete_guardas_de_sinks(self):
        raiz = Path(__file__).resolve().parents[2]
        template = (raiz / "noticias/templates/noticias/_estilos.html").read_text()
        js = (raiz / "static/js/estilos.js").read_text()
        for sink in (
            "|safe",
            "mark_safe",
            "autoescape off",
            "javascript:",
            "innerHTML",
            "outerHTML",
            "insertAdjacentHTML",
        ):
            with self.subTest(sink=sink):
                self.assertNotIn(sink, template + js)

    def test_template_pode_dispensar_envelope_sem_ser_post(self):
        template = engines["django"].from_string(
            '{% extends "noticias/base.html" %}'
            "{% block envelope %}livre{% endblock %}"
            "{% block topo_envelope %}{% endblock %}"
            "{% block rodape_envelope %}{% endblock %}"
            "{% block newsletter %}{% endblock %}"
        )
        html = template.render({}, RequestFactory().get("/"))
        self.assertIn('data-envelope="livre"', html)
        self.assertNotIn('class="sg-cab"', html)
        self.assertNotIn('class="sg-rodape"', html)
        self.assertNotIn("Escolher aparência", html)
