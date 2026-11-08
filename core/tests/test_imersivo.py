from django.core.exceptions import ValidationError
from django.core.management import call_command
from django.test import TestCase
from django.urls import reverse

from core.models import Ato, PostImersivo


def ato(efeito, parametros=None, **extra):
    return Ato(
        post=extra.pop("post", None),
        titulo="T",
        texto="x",
        efeito=efeito,
        parametros=parametros or {},
        **extra,
    )


class ValidacaoTests(TestCase):
    def test_efeitos_aceitam_parametros_vazios(self):
        for efeito in Ato.Efeito.values:
            with self.subTest(efeito=efeito):
                ato(efeito).clean()

    def test_parallax_intensidade_0_a_1(self):
        ato("parallax:camadas", {"intensidade": 0.5}).clean()
        for ruim in (1.5, -0.1, "alta", True):
            with self.subTest(valor=ruim), self.assertRaises(ValidationError):
                ato("parallax:camadas", {"intensidade": ruim}).clean()

    def test_rive_propriedade_texto(self):
        ato("rive:estado", {"propriedade": "progressoLeitura"}).clean()
        for ruim in (3, "", None):
            with self.subTest(valor=ruim), self.assertRaises(ValidationError):
                ato("rive:estado", {"propriedade": ruim}).clean()

    def test_chave_desconhecida_falha_em_todos_os_efeitos(self):
        for efeito in Ato.Efeito.values:
            with self.subTest(efeito=efeito), self.assertRaises(ValidationError) as ctx:
                ato(efeito, {"inventada": 1}).clean()
            self.assertIn("inventada", str(ctx.exception))

    def test_parametros_nao_objeto(self):
        with self.assertRaises(ValidationError):
            ato("scroll:revela", [1]).clean()

    def test_chaves_conhecidas_dos_outros_efeitos(self):
        ato("three:gira", {"voltas": 3}).clean()
        ato("scroll:revela", {"atraso": 0.5}).clean()
        ato("diagrama:constroi", {"atraso": 1}).clean()


class RotaTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.post = PostImersivo.objects.create(
            slug="exemplo-ficticio", titulo="Exemplo fictício", publicado=True
        )
        Ato.objects.create(
            post=cls.post,
            ordem=1,
            titulo="Primeiro",
            texto="Texto do primeiro.",
            efeito="parallax:camadas",
            parametros={"intensidade": 0.3},
        )
        Ato.objects.create(
            post=cls.post,
            ordem=2,
            titulo="Segundo",
            texto="Texto do segundo.",
            efeito="three:gira",
            reduzido="omitir",
        )
        cls.rascunho = PostImersivo.objects.create(
            slug="rascunho-ficticio", titulo="Rascunho", publicado=False
        )

    def test_url(self):
        self.assertEqual(
            reverse("core:imersivo", args=["exemplo-ficticio"]),
            "/imersivo/exemplo-ficticio/",
        )

    def test_nao_publicado_da_404(self):
        self.assertEqual(
            self.client.get(
                reverse("core:imersivo", args=["rascunho-ficticio"])
            ).status_code,
            404,
        )

    def test_inexistente_da_404(self):
        self.assertEqual(
            self.client.get(reverse("core:imersivo", args=["nada"])).status_code, 404
        )

    def test_render_dos_data_atributos(self):
        r = self.client.get(reverse("core:imersivo", args=["exemplo-ficticio"]))
        self.assertEqual(r.status_code, 200)
        self.assertTemplateUsed(r, "core/imersivo.html")
        self.assertContains(r, 'data-efeito="parallax:camadas"')
        self.assertContains(r, 'data-efeito="three:gira"')
        self.assertContains(r, "data-parametros=")
        self.assertContains(r, "&quot;intensidade&quot;: 0.3")
        self.assertContains(r, 'data-reduzido="estatico"')
        self.assertContains(r, "<h2>Primeiro</h2>", html=True)
        self.assertContains(r, "<p>Texto do segundo.</p>", html=True)
        self.assertContains(r, 'data-camada="fundo"')
        self.assertContains(r, 'data-camada="meio"')
        self.assertContains(r, 'data-camada="frente"')
        self.assertContains(r, "js/imersivo/motor.js")
        self.assertContains(r, "lab/vendor/three-0.160.0.module.js")
        self.assertNotContains(r, "cdn.")

    def test_reduzido_omitir_marcado(self):
        r = self.client.get(reverse("core:imersivo", args=["exemplo-ficticio"]))
        self.assertContains(r, 'data-reduzido="omitir"')
        self.assertContains(r, "im-ato--omitir")
        self.assertContains(r, "im-ato im-ato--omitir", count=1)

    def test_atos_em_ordem(self):
        r = self.client.get(reverse("core:imersivo", args=["exemplo-ficticio"]))
        html = r.content.decode()
        self.assertLess(html.index("Primeiro"), html.index("Segundo"))


class FixtureDemoTests(TestCase):
    fixtures = ["imersivo_demo"]

    def test_fixture_carrega_cinco_atos_um_por_efeito(self):
        post = PostImersivo.objects.get(slug="demo-provisorio")
        self.assertIn("PROVISÓRIO", post.titulo)
        self.assertEqual(post.atos.count(), 5)
        self.assertEqual(
            set(post.atos.values_list("efeito", flat=True)), set(Ato.Efeito.values)
        )
        for a in post.atos.all():
            a.full_clean()

    def test_fixture_renderiza(self):
        r = self.client.get(reverse("core:imersivo", args=["demo-provisorio"]))
        self.assertEqual(r.status_code, 200)
        self.assertContains(r, "data-ato", count=5)
        self.assertContains(r, "PROVISÓRIO")

    def test_loaddata_pelo_comando(self):
        call_command("loaddata", "imersivo_demo", verbosity=0)
        self.assertEqual(PostImersivo.objects.filter(slug="demo-provisorio").count(), 1)


class CssTests(TestCase):
    def test_css_view_transition_e_reduzido(self):
        from pathlib import Path

        css = (
            Path(__file__).resolve().parents[2] / "static/css/imersivo.css"
        ).read_text()
        self.assertIn("@view-transition", css)
        self.assertIn("@supports", css)
        self.assertIn("prefers-reduced-motion", css)
