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
    "leis_robos_livros",
    "serie_ia_na_ficcao",
]


class SerieFixtureTests(TestCase):
    fixtures = FIXTURES

    def test_episodios_0_a_8(self):
        serie = Serie.objects.get(slug="ia-na-ficcao")
        self.assertEqual(
            list(serie.episodios.values_list("numero", flat=True)), list(range(9))
        )

    def test_episodio_zero_e_o_hub(self):
        serie = Serie.objects.get(slug="ia-na-ficcao")
        self.assertEqual(serie.episodios.get(numero=0).post, serie.hub)


class RotasTests(TestCase):
    fixtures = FIXTURES

    def test_serie_200_renderiza_o_hub(self):
        r = self.client.get("/series/ia-na-ficcao/")
        self.assertEqual(r.status_code, 200)
        self.assertContains(r, 'data-efeito="linha-tempo:decadas"')

    def test_hub_liga_aos_episodios_novos(self):
        r = self.client.get("/series/ia-na-ficcao/")
        self.assertContains(r, 'href="/series/ia-na-ficcao/a-maquina-fria/"')
        self.assertContains(r, 'href="/series/ia-na-ficcao/escolhas-da-maquina/"')
        self.assertNotContains(r, 'href="/imersivo/')
        self.assertNotContains(r, "/series/ia-na-ficcao/o-placar/")

    def test_hub_post_5_entrou_com_link(self):
        r = self.client.get("/series/ia-na-ficcao/")
        self.assertContains(r, 'href="/series/ia-na-ficcao/leis-robos-e-livros/"')

    def test_hub_estacoes_sem_destino_dizem_em_breve(self):
        r = self.client.get("/series/ia-na-ficcao/")
        # R.U.R., Asimov e Turing, O quase-presente, O placar.
        self.assertContains(r, 'class="im-breve">em breve</span>', count=4)

    def test_hub_svg_sem_virgula_decimal(self):
        import re

        from django.utils import translation

        with translation.override("pt-br"):
            html = self.client.get("/series/ia-na-ficcao/").content.decode()
        self.assertIsNone(re.search(r'\b(cx|cy|x)="\d+,\d', html))

    def test_hub_contagem_bate_com_a_grelha(self):
        import re

        html = self.client.get("/series/ia-na-ficcao/").content.decode()
        n = int(re.search(r"Série · (\d+) posts", html).group(1))
        grelha = html.split('class="im-grelha"')[1].split("</ol>")[0]
        self.assertEqual(n, grelha.count("<li "))

    def test_hub_cartao_do_post_1_leva_a_capa(self):
        html = self.client.get("/series/ia-na-ficcao/").content.decode()
        self.assertEqual(html.count("im-post--capa-1"), 1)
        r = self.client.get("/series/ia-na-ficcao/a-maquina-fria/")
        self.assertContains(r, "view-transition-name:capa-post-1", count=1)

    def test_hub_sobrolho_e_h1_da_serie(self):
        r = self.client.get("/series/ia-na-ficcao/")
        self.assertContains(r, "Série · 8 posts · 1920 → 2026")
        self.assertNotContains(r, "Post imersivo")
        self.assertContains(r, '<h1 class="im-titulo-hub">')

    def test_hub_arte_distinta_por_estacao(self):
        from core.models import Ato

        ato = Ato.objects.get(pk=401)
        formas = [(e["forma"], e["variante"]) for e in ato.estacoes]
        self.assertEqual(len(set(formas)), len(formas))

    def test_episodios_200(self):
        for slug, tpl in [
            ("a-maquina-fria", "core/imersivo_maquina_fria.html"),
            ("o-medo-da-guerra-das-maquinas", "core/imersivo_guerra_maquinas.html"),
            ("o-que-e-ser-humano", "core/imersivo_ser_humano.html"),
            ("a-ia-afetiva", "core/imersivo_ia_afetiva.html"),
            ("escolhas-da-maquina", "core/imersivo_escolhas.html"),
        ]:
            with self.subTest(slug=slug):
                r = self.client.get(f"/series/ia-na-ficcao/{slug}/")
                self.assertEqual(r.status_code, 200)
                self.assertTemplateUsed(r, tpl)

    def test_navegacao_entre_posts_usa_rota_nova(self):
        r = self.client.get("/series/ia-na-ficcao/o-medo-da-guerra-das-maquinas/")
        self.assertContains(r, 'href="/series/ia-na-ficcao/o-que-e-ser-humano/"')
        self.assertNotContains(r, "/imersivo/o-que-e-ser-humano/")

    def test_episodio_zero_redireciona_para_a_serie(self):
        r = self.client.get("/series/ia-na-ficcao/a-serie/")
        self.assertRedirects(
            r, "/series/ia-na-ficcao/", status_code=301, fetch_redirect_response=False
        )

    def test_301_do_imersivo_para_episodio(self):
        r = self.client.get("/imersivo/a-maquina-fria/")
        self.assertEqual(r.status_code, 301)
        self.assertEqual(r["Location"], "/series/ia-na-ficcao/a-maquina-fria/")

    def test_301_do_hub_para_a_serie(self):
        r = self.client.get("/imersivo/ia-na-ficcao/")
        self.assertEqual(r.status_code, 301)
        self.assertEqual(r["Location"], "/series/ia-na-ficcao/")

    def test_404_serie_inexistente(self):
        self.assertEqual(self.client.get("/series/nada/").status_code, 404)
        self.assertEqual(self.client.get("/series/nada/x/").status_code, 404)

    def test_404_episodio_inexistente(self):
        self.assertEqual(self.client.get("/series/ia-na-ficcao/x/").status_code, 404)

    def test_404_episodio_sem_post_ou_nao_publicado(self):
        r = self.client.get("/series/ia-na-ficcao/o-placar/")
        self.assertEqual(r.status_code, 404)

    def test_404_episodio_com_post_rascunho(self):
        PostImersivo.objects.filter(slug="a-maquina-fria").update(publicado=False)
        r = self.client.get("/series/ia-na-ficcao/a-maquina-fria/")
        self.assertEqual(r.status_code, 404)

    def test_404_serie_nao_publicada(self):
        Serie.objects.update(publicado=False)
        self.assertEqual(self.client.get("/series/ia-na-ficcao/").status_code, 404)
        self.assertEqual(
            self.client.get("/series/ia-na-ficcao/a-maquina-fria/").status_code, 404
        )

    def test_imersivo_sem_serie_continua_a_servir(self):
        Serie.objects.update(publicado=False)
        r = self.client.get(reverse("core:imersivo", args=["a-maquina-fria"]))
        self.assertEqual(r.status_code, 200)

    def test_imersivo_inexistente_404(self):
        self.assertEqual(self.client.get("/imersivo/nada/").status_code, 404)

    def test_episodio_nao_publicado_nao_redireciona(self):
        Episodio.objects.filter(slug="a-maquina-fria").update(publicado=False)
        r = self.client.get("/imersivo/a-maquina-fria/")
        self.assertEqual(r.status_code, 200)
