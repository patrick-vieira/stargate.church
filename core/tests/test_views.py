from django.test import TestCase
from django.urls import reverse

from core.models import Episodio, PostImersivo, Serie


def _post(slug, publicado=True):
    return PostImersivo.objects.create(slug=slug, titulo=slug, publicado=publicado)


class HomeTests(TestCase):
    def test_home_responde_200_em_portugues(self):
        resposta = self.client.get(reverse("core:home"))
        self.assertEqual(resposta.status_code, 200)
        self.assertContains(resposta, 'lang="pt-BR"')

    def test_home_usa_o_template_do_portal(self):
        resposta = self.client.get(reverse("core:home"))
        self.assertTemplateUsed(resposta, "core/portal.html")
        self.assertNotIn("manchete", resposta.context)

    def test_lista_serie_publicada_com_link(self):
        serie = Serie.objects.create(
            slug="serie-a", titulo="Serie Alfa", publicado=True, hub=_post("hub-a")
        )
        resposta = self.client.get(reverse("core:home"))
        self.assertContains(resposta, "Serie Alfa")
        self.assertContains(resposta, f'href="{serie.get_absolute_url()}"')

    def test_nao_lista_serie_nao_publicada(self):
        Serie.objects.create(slug="serie-b", titulo="Serie Beta", hub=_post("hub-b"))
        resposta = self.client.get(reverse("core:home"))
        self.assertNotContains(resposta, "Serie Beta")

    def test_serie_sem_hub_aparece_sem_link(self):
        Serie.objects.create(slug="serie-c", titulo="Serie Gama", publicado=True)
        resposta = self.client.get(reverse("core:home"))
        self.assertContains(resposta, "Serie Gama")
        self.assertNotContains(resposta, "/series/serie-c/")

    def test_conta_apenas_episodios_publicados(self):
        hub = _post("hub-d")
        serie = Serie.objects.create(
            slug="serie-d", titulo="Serie Delta", publicado=True, hub=hub
        )
        Episodio.objects.create(
            serie=serie, slug="e1", numero=1, post=hub, publicado=True
        )
        Episodio.objects.create(
            serie=serie, slug="e2", numero=2, post=_post("p2"), publicado=False
        )
        resposta = self.client.get(reverse("core:home"))
        self.assertContains(resposta, "1 episódio<")

    def test_vazio_responde_200_com_mensagem(self):
        resposta = self.client.get(reverse("core:home"))
        self.assertEqual(resposta.status_code, 200)
        self.assertContains(resposta, "Ainda não há séries publicadas")

    def test_liga_para_as_noticias(self):
        resposta = self.client.get(reverse("core:home"))
        self.assertContains(resposta, f'href="{reverse("noticias:home")}"')


class NoticiasHomeTests(TestCase):
    def test_noticias_home_em_slash_noticias(self):
        self.assertEqual(reverse("noticias:home"), "/noticias/")
        resposta = self.client.get("/noticias/")
        self.assertEqual(resposta.status_code, 200)
        self.assertTemplateUsed(resposta, "noticias/home.html")
        for chave in ("manchete", "futuro_hoje", "ultimas", "numeros"):
            self.assertIn(chave, resposta.context)


class SaudeTests(TestCase):
    def test_saude_responde_200_com_status_ok(self):
        # A test runner já cria um banco vazio.
        # Verifica-se se a API de saúde funciona sem banco
        resposta = self.client.get("/saude/")
        self.assertEqual(resposta.status_code, 200)
        self.assertEqual(resposta.json(), {"status": "ok"})
