from django.test import SimpleTestCase, TestCase
from django.urls import reverse

from noticias.templatetags.realce import realce, sem_realce

from .util import criar_artigo


class FiltrosTests(SimpleTestCase):
    def test_marcacao_vira_em(self):
        self.assertEqual(
            realce("Já está *acendendo* hoje"),
            'Já está <em class="sg-realce">acendendo</em> hoje',
        )

    def test_html_no_titulo_sai_escapado(self):
        saida = realce("<script>alert(1)</script> *ok*")
        self.assertNotIn("<script>", saida)
        self.assertIn("&lt;script&gt;", saida)
        self.assertIn('<em class="sg-realce">ok</em>', saida)

    def test_sem_marcacao_nao_muda(self):
        self.assertEqual(realce("Título simples"), "Título simples")
        self.assertEqual(sem_realce("Título simples"), "Título simples")

    def test_sem_realce_tira_asteriscos(self):
        self.assertEqual(sem_realce("Já está *acendendo*"), "Já está acendendo")


H1_REALCE = '<h1>Rede <em class="sg-realce">acesa</em> hoje</h1>'


class RenderTests(TestCase):
    def setUp(self):
        self.artigo = criar_artigo(titulo="Rede *acesa* hoje", destaque=True)

    def test_manchete_da_home_tem_realce_e_card_nao(self):
        resposta = self.client.get(reverse("core:home"))
        self.assertContains(resposta, H1_REALCE)

    def test_card_nao_mostra_asteriscos(self):
        outro = criar_artigo(titulo="Outro *destaque* aqui")
        resposta = self.client.get(reverse("core:home"))
        self.assertContains(resposta, "<h3>Outro destaque aqui</h3>")
        self.assertNotContains(resposta, "*destaque*")
        self.assertTrue(outro.pk)

    def test_artigo_h1_realce_e_title_limpo(self):
        resposta = self.client.get(self.artigo.get_absolute_url())
        self.assertContains(resposta, H1_REALCE)
        self.assertContains(resposta, "<title>Rede acesa hoje — Stargate</title>")

    def test_script_no_titulo_sai_escapado_na_pagina(self):
        art = criar_artigo(titulo="<script>x</script> *y*")
        resposta = self.client.get(art.get_absolute_url())
        self.assertNotContains(resposta, "<script>x</script>")
        self.assertContains(resposta, "&lt;script&gt;x&lt;/script&gt;")

    def test_titulo_sem_marcacao_nao_muda(self):
        art = criar_artigo(titulo="Título simples")
        resposta = self.client.get(art.get_absolute_url())
        self.assertContains(resposta, "<h1>Título simples</h1>")
        self.assertNotContains(resposta, "sg-realce")
