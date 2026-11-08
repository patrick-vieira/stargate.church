import re

from django.core.exceptions import ValidationError
from django.core.management import call_command
from django.test import TestCase
from django.urls import reverse

from core.models import Ato, PostImersivo

EFEITOS_MAQUINA_FRIA = {
    "terminal:fala",
    "three:corredor",
    "olho:segue",
    "atmosfera:maquina-fria",
    "atmosfera:guerra-maquinas",
    "atmosfera:ser-humano",
    "atmosfera:escolhas",
}


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
            set(Ato.Efeito.values) - EFEITOS_MAQUINA_FRIA,
        )
        for a in post.atos.all():
            a.full_clean()

    def test_fixture_renderiza(self):
        r = self.client.get(reverse("core:imersivo", args=["demo-provisorio"]))
        self.assertEqual(r.status_code, 200)
        self.assertContains(r, "data-ato", count=6)  # 5 atos + o narrador (STAR-38)
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


class NarradorRiveTests(TestCase):
    """STAR-38: o narrador aparece em todos os posts imersivos, na era certa."""

    POSTS = {
        "a-maquina-fria": ("maquina_fria", 1),
        "o-medo-da-guerra-das-maquinas": ("guerra_maquinas", 2),
        "escolhas-da-maquina": ("escolhas", 5),
        "demo-provisorio": ("imersivo_demo", 6),
    }

    def _raiz(self):
        from pathlib import Path

        return Path(__file__).resolve().parents[2]

    def test_narrador_em_todos_os_posts_com_a_era_certa(self):
        for slug, (fixture, era) in self.POSTS.items():
            call_command("loaddata", fixture, verbosity=0)
            with self.subTest(slug=slug):
                r = self.client.get(reverse("core:imersivo", args=[slug]))
                self.assertEqual(r.status_code, 200)
                self.assertContains(r, 'data-efeito="rive:narrador"', count=1)
                self.assertContains(r, f'data-era="{era}"')
                self.assertContains(r, f"data-parametros='{{\"era\": {era}}}'")
                self.assertContains(r, "rive/narrador.riv")
                self.assertContains(r, "lab/vendor/rive-canvas-2.35.0.js")
                self.assertNotContains(r, "cdn.")

    def test_js_liga_progresso_ao_scroll_e_respeita_reduzido(self):
        raiz = self._raiz()
        js = (raiz / "static/js/imersivo/efeitos/rive-narrador.js").read_text()
        self.assertIn('registar("rive:narrador"', js)
        self.assertIn("progressoPagina(", js)
        self.assertIn("if (reduzido) return;", js)
        self.assertNotIn("http", js)
        motor = (raiz / "static/js/imersivo/motor.js").read_text()
        self.assertIn("progressoPagina(cb)", motor)

    def test_css_48px_a_390_e_sem_captura(self):
        css = (self._raiz() / "static/css/narrador.css").read_text()
        self.assertIn("pointer-events:none", css)
        self.assertIn("max-width:600px", css)
        self.assertIn("width:48px", css)
        self.assertIn("prefers-reduced-motion:reduce", css)

    def test_narrador_sobe_acima_do_controlo_de_pausa(self):
        raiz = self._raiz()
        css = (raiz / "static/css/narrador.css").read_text()
        self.assertIn("bottom:var(--nr-base,16px)", css)
        self.assertIn("bottom:var(--nr-base,8px)", css)
        for nome, minimo in (
            ("atmosfera-maquina-fria", 65),
            ("atmosfera-escolhas", 65),
            ("atmosfera-guerra-maquinas", 65),
        ):
            txt = (raiz / f"static/css/{nome}.css").read_text()
            m = re.search(r"\.nr-narrador\{--nr-base:(\d+)px\}", txt)
            self.assertIsNotNone(m, nome)
            self.assertGreaterEqual(int(m.group(1)), minimo, nome)


class CssTests(TestCase):
    def test_css_view_transition_e_reduzido(self):
        from pathlib import Path

        css = (
            Path(__file__).resolve().parents[2] / "static/css/imersivo.css"
        ).read_text()
        self.assertIn("@view-transition", css)
        self.assertIn("@supports", css)
        self.assertIn("prefers-reduced-motion", css)


class MaquinaFriaTests(TestCase):
    fixtures = ["maquina_fria_provisorio"]

    def test_terminal_linhas_e_velocidade(self):
        ato("terminal:fala", {"linhas": ["> ok"], "velocidade": 40}).clean()
        for ruim in ([], "texto", [""], [1], ["x" * 81], ["a"] * 13):
            with self.subTest(valor=ruim), self.assertRaises(ValidationError):
                ato("terminal:fala", {"linhas": ruim}).clean()
        with self.assertRaises(ValidationError):
            ato("terminal:fala", {"velocidade": 500}).clean()

    def test_corredor_e_olho_parametros(self):
        ato("three:corredor", {"profundidade": 12, "fixar": True}).clean()
        ato("olho:segue", {"alcance": 0.5, "fixar": False}).clean()
        with self.assertRaises(ValidationError):
            ato("three:corredor", {"profundidade": 2}).clean()
        with self.assertRaises(ValidationError):
            ato("olho:segue", {"alcance": 2}).clean()

    def test_fixture_valida_e_renderiza(self):
        post = PostImersivo.objects.get(slug="efeitos-maquina-fria-provisorio")
        self.assertIn("PROVISÓRIO", post.titulo)
        for a in post.atos.all():
            a.full_clean()
        r = self.client.get(
            reverse("core:imersivo", args=["efeitos-maquina-fria-provisorio"])
        )
        self.assertEqual(r.status_code, 200)
        self.assertTemplateUsed(r, "core/imersivo.html")
        self.assertContains(r, "data-terminal")
        self.assertContains(r, "&gt; status do sistema: tudo normal.")
        self.assertContains(r, 'data-efeito="three:corredor"')
        self.assertContains(r, "data-pupila")
        self.assertContains(r, 'data-reduzido="omitir"', count=1)

    def test_efeitos_js_existem_e_respeitam_reduzido(self):
        from pathlib import Path

        base = Path(__file__).resolve().parents[2] / "static/js/imersivo/efeitos"
        for nome in ("terminal-fala", "three-corredor", "olho-segue"):
            js = (base / f"{nome}.js").read_text()
            self.assertIn("reduzido", js)
            self.assertIn("registar(", js)
            self.assertNotIn("http", js)
        olho = (base / "olho-segue.js").read_text()
        self.assertIn("pointermove", olho)
        self.assertIn("progresso(", olho)
        corredor = (base / "three-corredor.js").read_text()
        self.assertIn('await import("three")', corredor)


class AtmosferaMaquinaFriaTests(TestCase):
    fixtures = ["maquina_fria"]

    def _raiz(self):
        from pathlib import Path

        return Path(__file__).resolve().parents[2]

    def test_efeito_sem_parametros(self):
        ato("atmosfera:maquina-fria").clean()
        with self.assertRaises(ValidationError):
            ato("atmosfera:maquina-fria", {"fixar": True}).clean()

    def test_fixture_valida(self):
        post = PostImersivo.objects.get(slug="a-maquina-fria")
        self.assertNotIn("PROVISÓRIO", post.titulo)
        for a in post.atos.all():
            a.full_clean()

    def test_renderiza_o_template_da_atmosfera(self):
        r = self.client.get(reverse("core:imersivo", args=["a-maquina-fria"]))
        self.assertEqual(r.status_code, 200)
        self.assertTemplateUsed(r, "core/imersivo_maquina_fria.html")
        self.assertContains(r, 'data-efeito="atmosfera:maquina-fria"')
        self.assertContains(r, "css/atmosfera-maquina-fria.css")
        self.assertContains(r, "js/imersivo/motor.js")
        self.assertContains(
            r, "Console 7, sessão aberta. Ação recomendada: prosseguir."
        )
        self.assertContains(r, "Auditoria da decisão: indisponível.")
        self.assertContains(r, "Interrupção humana: não configurada.")
        self.assertContains(r, 'id="am-corredor"')
        self.assertContains(r, 'id="am-g-valor"')
        self.assertNotContains(r, "Georgia")
        self.assertNotContains(r, "cdn.")

    def test_fonte_fraunces_e_licenca_em_static(self):
        raiz = self._raiz()
        css = (raiz / "static/css/atmosfera-maquina-fria.css").read_text()
        self.assertIn("fraunces-latin-600-normal.woff2", css)
        self.assertIn("--serif:var(--sg-serif)", css)
        self.assertNotIn("Georgia", css)
        pasta = raiz / "static/fonts/fraunces"
        self.assertTrue((pasta / "fraunces-latin-600-normal.woff2").is_file())
        self.assertTrue((pasta / "Fraunces-OFL.txt").is_file())

    def test_css_oculta_canvas_em_movimento_reduzido(self):
        css = (self._raiz() / "static/css/atmosfera-maquina-fria.css").read_text()
        reduzido = css[css.index("@media (prefers-reduced-motion:reduce)") :]
        self.assertIn(".am-poeira,.am-corredor{display:none!important}", reduzido)

    def test_js_lazy_three_e_reduzido(self):
        js = (
            self._raiz() / "static/js/imersivo/efeitos/atmosfera-maquina-fria.js"
        ).read_text()
        self.assertIn('registar("atmosfera:maquina-fria"', js)
        self.assertIn('await import("three")', js)
        self.assertIn("if (reduzido) return;", js)
        self.assertNotIn("http", js)


class AtmosferaGuerraMaquinasTests(TestCase):
    fixtures = ["guerra_maquinas"]

    def _raiz(self):
        from pathlib import Path

        return Path(__file__).resolve().parents[2]

    def test_efeito_sem_parametros(self):
        ato("atmosfera:guerra-maquinas").clean()
        with self.assertRaises(ValidationError):
            ato("atmosfera:guerra-maquinas", {"fixar": True}).clean()

    def test_fixture_valida(self):
        post = PostImersivo.objects.get(slug="o-medo-da-guerra-das-maquinas")
        self.assertEqual(post.pk, 4)
        for a in post.atos.all():
            a.full_clean()

    def test_renderiza_o_template_da_atmosfera(self):
        r = self.client.get(
            reverse("core:imersivo", args=["o-medo-da-guerra-das-maquinas"])
        )
        self.assertEqual(r.status_code, 200)
        self.assertTemplateUsed(r, "core/imersivo_guerra_maquinas.html")
        self.assertTemplateNotUsed(r, "core/imersivo_maquina_fria.html")
        self.assertContains(r, 'data-efeito="atmosfera:guerra-maquinas"')
        self.assertContains(r, "css/atmosfera-guerra-maquinas.css")
        self.assertContains(r, "js/imersivo/motor.js")
        self.assertContains(r, 'id="ag-hud"')
        self.assertContains(r, 'id="ag-supervisao"')
        self.assertContains(r, "Interromper o sistema")
        self.assertContains(r, "Ficção · 2")
        self.assertNotContains(r, "cdn.")
        self.assertNotContains(r, "Georgia")

    def test_maquina_fria_continua_no_seu_template(self):
        from django.core.management import call_command

        call_command("loaddata", "maquina_fria", verbosity=0)
        r = self.client.get(reverse("core:imersivo", args=["a-maquina-fria"]))
        self.assertTemplateUsed(r, "core/imersivo_maquina_fria.html")

    def test_css_escopado_e_reduzido(self):
        css = (self._raiz() / "static/css/atmosfera-guerra-maquinas.css").read_text()
        self.assertIn("--serif:var(--sg-serif)", css)
        self.assertNotIn("Georgia", css)
        self.assertNotIn(":root", css)
        self.assertIn("prefers-reduced-motion:reduce", css)
        self.assertIn(".ag-raiz.ag-estatico", css)
        self.assertIn("white-space:nowrap", css)  # retoque 4: sobrolho numa linha
        self.assertIn("font:600 12px/1.6 var(--mono)", css)  # retoque 3: entrelinha

    def test_js_registra_e_respeita_reduzido(self):
        js = (
            self._raiz() / "static/js/imersivo/efeitos/atmosfera-guerra-maquinas.js"
        ).read_text()
        self.assertIn('registar("atmosfera:guerra-maquinas"', js)
        self.assertIn("reduzido", js)
        self.assertNotIn("http", js)
        self.assertNotIn("import(", js)

    def test_imagens_webp_leves(self):
        pasta = self._raiz() / "static/img/guerra-maquinas"
        arquivos = sorted(pasta.glob("*.webp"))
        self.assertTrue(arquivos)
        for f in arquivos:
            with self.subTest(f=f.name):
                self.assertLessEqual(f.stat().st_size, 70 * 1024)


class AtmosferaSerHumanoTests(TestCase):
    fixtures = ["ser_humano"]

    def _raiz(self):
        from pathlib import Path

        return Path(__file__).resolve().parents[2]

    def test_efeito_sem_parametros(self):
        ato("atmosfera:ser-humano").clean()
        with self.assertRaises(ValidationError):
            ato("atmosfera:ser-humano", {"fixar": True}).clean()

    def test_fixture_valida(self):
        post = PostImersivo.objects.get(slug="o-que-e-ser-humano")
        self.assertEqual(post.pk, 5)
        for a in post.atos.all():
            self.assertEqual(a.pk, 16)
            a.full_clean()

    def test_renderiza_o_template_da_atmosfera(self):
        r = self.client.get(reverse("core:imersivo", args=["o-que-e-ser-humano"]))
        self.assertEqual(r.status_code, 200)
        self.assertTemplateUsed(r, "core/imersivo_ser_humano.html")
        self.assertTemplateNotUsed(r, "core/imersivo_guerra_maquinas.html")
        self.assertContains(r, 'data-efeito="atmosfera:ser-humano"')
        self.assertContains(r, "css/atmosfera-ser-humano.css")
        self.assertContains(r, "js/imersivo/motor.js")
        self.assertContains(r, 'id="sh-teste"')
        self.assertContains(r, "Teste sobre a confiança de quem observa")
        self.assertContains(r, "Ficção · 3")
        self.assertContains(r, "Em todos os casos, direitos de pessoas reais")
        self.assertNotContains(r, "cdn.")
        self.assertNotContains(r, "Georgia")

    def test_rodape_sem_temas_nao_mostra_o_titulo_temas(self):
        r = self.client.get(reverse("core:imersivo", args=["o-que-e-ser-humano"]))
        self.assertNotContains(r, "<h4>Temas</h4>")
        self.assertContains(r, "<h4>Mais</h4>")

    def test_post_2_liga_para_o_post_3(self):
        from django.core.management import call_command

        call_command("loaddata", "guerra_maquinas", verbosity=0)
        r = self.client.get(
            reverse("core:imersivo", args=["o-medo-da-guerra-das-maquinas"])
        )
        self.assertTemplateUsed(r, "core/imersivo_guerra_maquinas.html")
        destino = reverse("core:imersivo", args=["o-que-e-ser-humano"])
        self.assertContains(r, f'href="{destino}"')

    def test_css_escopado_e_reduzido(self):
        css = (self._raiz() / "static/css/atmosfera-ser-humano.css").read_text()
        self.assertIn("--serif:var(--sg-serif)", css)
        self.assertNotIn("Georgia", css)
        self.assertNotIn(":root", css)
        self.assertIn("prefers-reduced-motion:reduce", css)
        self.assertIn(".sh-raiz.sh-estatico", css)
        self.assertIn("font:600 12px/1.6 var(--mono)", css)  # retoque 3: entrelinha
        self.assertIn("white-space:nowrap", css)

    def test_js_registra_e_respeita_reduzido(self):
        js = (
            self._raiz() / "static/js/imersivo/efeitos/atmosfera-ser-humano.js"
        ).read_text()
        self.assertIn('registar("atmosfera:ser-humano"', js)
        self.assertIn("reduzido", js)
        self.assertNotIn("http", js)
        self.assertNotIn("import(", js)

    def test_imagens_webp_leves_e_so_fundos(self):
        pasta = self._raiz() / "static/img/ser-humano"
        arquivos = sorted(pasta.glob("*.webp"))
        self.assertEqual(
            [f.name for f in arquivos], ["fundo-1920.webp", "fundo-780.webp"]
        )
        for f in arquivos:
            with self.subTest(f=f.name):
                self.assertLessEqual(f.stat().st_size, 70 * 1024)


class AtmosferaEscolhasTests(TestCase):
    fixtures = ["escolhas"]

    def _raiz(self):
        from pathlib import Path

        return Path(__file__).resolve().parents[2]

    def test_efeito_sem_parametros(self):
        ato("atmosfera:escolhas").clean()
        with self.assertRaises(ValidationError):
            ato("atmosfera:escolhas", {"fixar": True}).clean()

    def test_fixture_valida(self):
        post = PostImersivo.objects.get(slug="escolhas-da-maquina")
        self.assertEqual(post.pk, 6)
        for a in post.atos.all():
            self.assertEqual(a.pk, 17)
            a.full_clean()

    def test_renderiza_o_template_da_atmosfera(self):
        r = self.client.get(reverse("core:imersivo", args=["escolhas-da-maquina"]))
        self.assertEqual(r.status_code, 200)
        self.assertTemplateUsed(r, "core/imersivo_escolhas.html")
        self.assertTemplateNotUsed(r, "core/imersivo_guerra_maquinas.html")
        self.assertContains(r, 'data-efeito="atmosfera:escolhas"')
        self.assertContains(r, "css/atmosfera-escolhas.css")
        self.assertContains(r, "js/imersivo/motor.js")
        self.assertContains(r, 'id="em-p-esc1"')
        self.assertContains(r, "Ficção · 6")
        for f in ("A1", "A2", "B1", "B2"):
            self.assertContains(r, f'data-f="{f}"')
        self.assertContains(r, "Limpar caminho")
        self.assertContains(r, "Guardar meu caminho neste aparelho")
        self.assertNotContains(r, "cdn.")
        self.assertNotContains(r, "Georgia")

    def test_sem_gravacao_no_servidor(self):
        r = self.client.get(reverse("core:imersivo", args=["escolhas-da-maquina"]))
        self.assertNotContains(r, "csrfmiddlewaretoken")
        self.assertNotContains(r, "action=")

    def test_css_escopado_e_reduzido(self):
        css = (self._raiz() / "static/css/atmosfera-escolhas.css").read_text()
        self.assertIn("--serif:var(--sg-serif)", css)
        self.assertNotIn("Georgia", css)
        self.assertNotIn(":root", css)
        self.assertIn("prefers-reduced-motion:reduce", css)
        self.assertIn(".em-raiz.em-linear", css)
        self.assertIn(".em-estatico", css)

    def test_js_estado_no_cliente_e_reduzido(self):
        js = (
            self._raiz() / "static/js/imersivo/efeitos/atmosfera-escolhas.js"
        ).read_text()
        self.assertIn('registar("atmosfera:escolhas"', js)
        self.assertIn("reduzido", js)
        self.assertIn("localStorage", js)
        self.assertIn("try{", js)
        self.assertNotIn("fetch(", js)
        self.assertNotIn("XMLHttpRequest", js)
        self.assertNotIn("http", js)
        self.assertNotIn("import(", js)

    def test_imagens_webp_leves_e_so_fundos(self):
        pasta = self._raiz() / "static/img/escolhas"
        arquivos = sorted(pasta.glob("*.webp"))
        self.assertEqual(
            [f.name for f in arquivos], ["fundo-1920.webp", "fundo-780.webp"]
        )
        for f in arquivos:
            with self.subTest(f=f.name):
                self.assertLessEqual(f.stat().st_size, 70 * 1024)
