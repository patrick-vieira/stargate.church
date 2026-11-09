from django.test import TestCase
from django.urls import reverse

from core.models import Episodio, PostImersivo, Serie

FIXTURES = [
    "imersivo_hub",
    "maquina_fria",
    "guerra_maquinas",
    "ser_humano",
    "ia_afetiva",
    "escolhas",
    "quase_presente",
    "leis_robos_livros",
    "placar_post",
    "serie_ia_na_ficcao",
]


class FumoRotasTests(TestCase):
    fixtures = FIXTURES

    def test_home_200_e_html_valido(self):
        resposta = self.client.get(reverse("core:home"))
        self.assertEqual(resposta.status_code, 200)
        self.assertContains(resposta, 'lang="pt-BR"')
        self.assertContains(resposta, "<title>")
        self.assertNotContains(resposta, "Lorem")
        self.assertNotContains(resposta, "TODO")

    def test_saude_200_e_json_ok(self):
        resposta = self.client.get(reverse("core:saude"))
        self.assertEqual(resposta.status_code, 200)
        self.assertEqual(resposta.json(), {"status": "ok"})

    def test_imersivos_200_e_html_valido(self):
        posts = PostImersivo.publicados().values_list("slug", flat=True)
        for slug in posts:
            with self.subTest(slug=slug):
                resposta = self.client.get(reverse("core:imersivo", args=[slug]))
                # Posts com série redirecionam para a rota da série
                if resposta.status_code == 301:
                    resposta = self.client.get(resposta.url, follow=True)
                self.assertEqual(resposta.status_code, 200)
                self.assertContains(resposta, 'lang="pt-BR"')
                self.assertContains(resposta, "<title>")
                self.assertNotContains(resposta, "Lorem")
                self.assertNotContains(resposta, "TODO")

    def test_series_200_e_html_valido(self):
        series = Serie.objects.filter(publicado=True).values_list("slug", flat=True)
        for slug in series:
            with self.subTest(slug=slug):
                resposta = self.client.get(reverse("core:serie", args=[slug]))
                self.assertEqual(resposta.status_code, 200)
                self.assertContains(resposta, 'lang="pt-BR"')
                self.assertContains(resposta, "<title>")
                self.assertNotContains(resposta, "Lorem")
                self.assertNotContains(resposta, "TODO")

    def test_episodios_200_e_html_valido(self):
        episodios = Episodio.objects.filter(
            publicado=True, post__publicado=True, serie__publicado=True
        ).select_related("serie")
        for episodio in episodios:
            with self.subTest(slug=f"{episodio.serie.slug}/{episodio.slug}"):
                resposta = self.client.get(
                    reverse(
                        "core:episodio",
                        args=[episodio.serie.slug, episodio.slug],
                    )
                )
                # Episódio 0 (hub) redireciona para a série
                if resposta.status_code == 301:
                    resposta = self.client.get(resposta.url, follow=True)
                self.assertEqual(resposta.status_code, 200)
                self.assertContains(resposta, 'lang="pt-BR"')
                self.assertContains(resposta, "<title>")
                self.assertNotContains(resposta, "Lorem")
                self.assertNotContains(resposta, "TODO")

    def test_imersivo_inexistente_404(self):
        resposta = self.client.get(reverse("core:imersivo", args=["nao-existe"]))
        self.assertEqual(resposta.status_code, 404)

    def test_serie_inexistente_404(self):
        resposta = self.client.get(reverse("core:serie", args=["nao-existe"]))
        self.assertEqual(resposta.status_code, 404)

    def test_episodio_inexistente_404(self):
        resposta = self.client.get(
            reverse("core:episodio", args=["ia-na-ficcao", "nao-existe"])
        )
        self.assertEqual(resposta.status_code, 404)
