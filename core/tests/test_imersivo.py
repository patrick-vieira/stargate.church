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
            set(post.atos.values_list("efeito", flat=True)),
            set(Ato.Efeito.values) - {"atmosfera:ia-afetiva"},
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


class FixarTests(TestCase):
    def test_fixar_booleano_nos_tres_efeitos(self):
        for efeito in ("parallax:camadas", "three:gira", "rive:estado"):
            with self.subTest(efeito=efeito):
                ato(efeito, {"fixar": True}).clean()
                ato(efeito, {"fixar": False}).clean()
                for ruim in (1, "sim", None, 0.5):
                    with self.assertRaises(ValidationError):
                        ato(efeito, {"fixar": ruim}).clean()

    def test_fixar_nao_aceito_nos_outros(self):
        for efeito in ("scroll:revela", "diagrama:constroi"):
            with self.subTest(efeito=efeito), self.assertRaises(ValidationError):
                ato(efeito, {"fixar": True}).clean()

    def test_classe_fixo_no_render(self):
        post = PostImersivo.objects.create(
            slug="fixo-ficticio", titulo="F", publicado=True
        )
        Ato.objects.create(
            post=post,
            ordem=1,
            titulo="A",
            texto="a",
            efeito="three:gira",
            parametros={"fixar": True},
        )
        Ato.objects.create(
            post=post,
            ordem=2,
            titulo="B",
            texto="b",
            efeito="parallax:camadas",
            parametros={"fixar": False, "intensidade": 0.3},
        )
        Ato.objects.create(
            post=post, ordem=3, titulo="C", texto="c", efeito="rive:estado"
        )
        r = self.client.get(reverse("core:imersivo", args=["fixo-ficticio"]))
        self.assertContains(r, "im-ato--fixo", count=1)
        self.assertContains(r, 'style="--im-int:0.3"')

    def test_css_sticky_e_reduzido_nao_fixa(self):
        css = _css()
        self.assertIn(".im-ato--fixo .im-cena{position:sticky", css)
        reduzido = css[css.index("@media (prefers-reduced-motion:reduce)") :]
        self.assertIn(".im-ato--fixo .im-cena{position:static}", reduzido)


def _css():
    from pathlib import Path

    return (Path(__file__).resolve().parents[2] / "static/css/imersivo.css").read_text()


class ScrollDrivenTests(TestCase):
    def test_css_scroll_driven_sob_supports(self):
        css = _css()
        self.assertIn("@supports (animation-timeline:view())", css)
        self.assertIn("animation-timeline:view()", css)
        self.assertIn("@keyframes im-par", css)
        self.assertIn("@keyframes im-rev", css)

    def test_js_so_sem_suporte(self):
        from pathlib import Path

        base = Path(__file__).resolve().parents[2] / "static/js/imersivo"
        self.assertIn("animation-timeline: view()", (base / "motor.js").read_text())
        for nome in ("parallax-camadas", "scroll-revela"):
            self.assertIn(
                "if (cssScroll) return", (base / "efeitos" / f"{nome}.js").read_text()
            )

    def test_libs_opcionais_caminhos_versionados(self):
        from core.imersivo import LIBS_OPCIONAIS

        self.assertEqual(LIBS_OPCIONAIS["gsap"], "lab/vendor/gsap-3.12.x/gsap.min.js")
        self.assertEqual(LIBS_OPCIONAIS["lenis"], "lab/vendor/lenis-1.x/lenis.mjs")


class CssTests(TestCase):
    def test_css_view_transition_e_reduzido(self):
        from pathlib import Path

        css = (
            Path(__file__).resolve().parents[2] / "static/css/imersivo.css"
        ).read_text()
        self.assertIn("@view-transition", css)
        self.assertIn("@supports", css)
        self.assertIn("prefers-reduced-motion", css)


class AtmosferaIaAfetivaTests(TestCase):
    fixtures = ["ia_afetiva"]

    def _raiz(self):
        from pathlib import Path

        return Path(__file__).resolve().parents[2]

    def test_efeito_sem_parametros(self):
        ato("atmosfera:ia-afetiva").clean()
        with self.assertRaises(ValidationError):
            ato("atmosfera:ia-afetiva", {"fixar": True}).clean()

    def test_fixture_valida(self):
        post = PostImersivo.objects.get(slug="a-ia-afetiva")
        self.assertNotIn("PROVISÓRIO", post.titulo)
        for a in post.atos.all():
            a.full_clean()

    def test_renderiza_o_template_da_atmosfera(self):
        r = self.client.get(reverse("core:imersivo", args=["a-ia-afetiva"]))
        self.assertEqual(r.status_code, 200)
        self.assertTemplateUsed(r, "core/imersivo_ia_afetiva.html")
        self.assertContains(r, 'data-efeito="atmosfera:ia-afetiva"')
        self.assertContains(r, "css/atmosfera-ia-afetiva.css")
        self.assertContains(r, "js/imersivo/motor.js")
        self.assertContains(r, 'id="aa-chat"')
        self.assertContains(r, 'role="log"')
        self.assertContains(r, 'id="aa-limites"')
        self.assertContains(r, "Comparação entre a ficção e os assistentes de 2026")
        self.assertContains(r, "som (em breve)")
        self.assertContains(r, "diálogo inventado")
        self.assertNotContains(r, "Georgia")
        self.assertNotContains(r, "cdn.")
        self.assertNotContains(r, "http://")

    def test_outro_post_continua_no_template_generico(self):
        PostImersivo.objects.create(slug="outro", titulo="Outro", publicado=True)
        r = self.client.get(reverse("core:imersivo", args=["outro"]))
        self.assertTemplateUsed(r, "core/imersivo.html")
        self.assertTemplateNotUsed(r, "core/imersivo_ia_afetiva.html")

    def test_fonte_fraunces_e_licenca_em_static(self):
        raiz = self._raiz()
        css = (raiz / "static/css/atmosfera-ia-afetiva.css").read_text()
        self.assertIn("fraunces-latin-600-normal.woff2", css)
        self.assertIn("--serif:var(--sg-serif)", css)
        self.assertNotIn("Georgia", css)
        pasta = raiz / "static/fonts/fraunces"
        self.assertTrue((pasta / "fraunces-latin-600-normal.woff2").is_file())
        self.assertTrue((pasta / "Fraunces-OFL.txt").is_file())

    def test_css_escopado_e_reduzido(self):
        import re

        css = (self._raiz() / "static/css/atmosfera-ia-afetiva.css").read_text()
        reduzido = css[css.index("@media (prefers-reduced-motion:reduce)") :]
        self.assertIn(".aa-janela::before{animation:none}", reduzido)
        # nenhum seletor solto fora do prefixo aa-
        corpo = re.sub(r"@font-face\{[^}]*\}|/\*.*?\*/", "", css, flags=re.S)
        for seletor in re.findall(r"(?:^|\})\s*([^{}@]+)\{", corpo):
            for parte in seletor.split(","):
                parte = parte.strip()
                if parte and not parte.startswith(("from", "to", "50%")):
                    self.assertIn("aa-", parte, parte)

    def test_js_sem_rede_e_com_reduzido(self):
        js = (
            self._raiz() / "static/js/imersivo/efeitos/atmosfera-ia-afetiva.js"
        ).read_text()
        self.assertIn('registar("atmosfera:ia-afetiva"', js)
        self.assertIn("if (reduzido) bt.disabled = true;", js)
        self.assertIn("reduzido", js)
        self.assertNotIn("http", js)
        self.assertNotIn('import("three")', js)
