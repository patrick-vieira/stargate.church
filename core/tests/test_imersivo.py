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
    "atmosfera:ia-afetiva",
    "atmosfera:leis-robos-livros",
    "atmosfera:placar",
    "atmosfera:quase-presente",
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
        # a base da luz: o CSS vem do base.html, o luz.js não corre no imersivo
        self.assertContains(r, "css/luz.css")
        self.assertNotContains(r, "js/luz.js")
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
            set(Ato.Efeito.values)
            - EFEITOS_MAQUINA_FRIA
            - {"linha-tempo:decadas", "filtro:chips", "grelha:posts"},
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

    def test_narrador_no_post_3_ser_humano_fora_da_raiz(self):
        call_command("loaddata", "ser_humano", verbosity=0)
        r = self.client.get(reverse("core:imersivo", args=["o-que-e-ser-humano"]))
        self.assertEqual(r.status_code, 200)
        self.assertContains(r, 'data-efeito="rive:narrador"', count=1)
        self.assertContains(r, 'data-era="3"')
        html = r.content.decode()
        self.assertLess(html.index("rive:narrador"), html.index('class="sh-raiz"'))

    def test_narrador_no_post_4_ia_afetiva_fora_da_raiz(self):
        call_command("loaddata", "ia_afetiva", verbosity=0)
        r = self.client.get(reverse("core:imersivo", args=["a-ia-afetiva"]))
        self.assertEqual(r.status_code, 200)
        self.assertContains(r, 'data-efeito="rive:narrador"', count=1)
        self.assertContains(r, 'data-era="5"')
        html = r.content.decode()
        self.assertLess(html.index("rive:narrador"), html.index('class="aa-raiz"'))

    def test_js_liga_progresso_ao_scroll_e_respeita_reduzido(self):
        raiz = self._raiz()
        js = (raiz / "static/js/imersivo/efeitos/rive-narrador.js").read_text()
        self.assertIn('registar("rive:narrador"', js)
        self.assertIn("progressoPagina(", js)
        self.assertIn("if (reduzido) return;", js)
        self.assertNotIn("http", js)
        motor = (raiz / "static/js/imersivo/motor.js").read_text()
        self.assertIn("progressoPagina(cb)", motor)

    def test_runtime_rive_fora_da_carga_inicial(self):
        """STAR-60: o HTML dos posts não puxa o runtime Rive (js/wasm); só o
        rive-narrador.js o carrega, depois de load + interação."""
        posts = {
            "a-maquina-fria": "maquina_fria",
            "o-medo-da-guerra-das-maquinas": "guerra_maquinas",
            "o-que-e-ser-humano": "ser_humano",
            "a-ia-afetiva": "ia_afetiva",
            "escolhas-da-maquina": "escolhas",
        }
        for slug, fixture in posts.items():
            call_command("loaddata", fixture, verbosity=0)
            with self.subTest(slug=slug):
                r = self.client.get(reverse("core:imersivo", args=[slug]))
                self.assertEqual(r.status_code, 200)
                html = r.content.decode()
                for tag in re.findall(r"<(?:script|link)\b[^>]*>", html):
                    self.assertNotRegex(tag, r"rive", tag)
                self.assertNotIn("modulepreload", html)
        js = (self._raiz() / "static/js/imersivo/efeitos/rive-narrador.js").read_text()
        self.assertIn("aposCargaEInteracao", js)
        self.assertLess(
            js.index("await aposCargaEInteracao()"), js.index("await carregarScript(")
        )
        for ev in ("scroll", "pointerdown", "keydown"):
            self.assertIn(f'"{ev}"', js)
        self.assertNotIn("IntersectionObserver", js)

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
            ("atmosfera-ser-humano", 65),
            ("atmosfera-ia-afetiva", 65),
        ):
            txt = (raiz / f"static/css/{nome}.css").read_text()
            m = re.search(
                r"(?:\.nr-narrador|body:has\(\.(?:sh|aa)-raiz\))\{--nr-base:(\d+)px\}",
                txt,
            )
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


ESTACAO = {"decada": 1960, "titulo": "A máquina fria"}


class EstacoesTests(TestCase):
    def test_validas(self):
        ato("linha-tempo:decadas", {"intensidade": 0.5, "estacoes": [ESTACAO]}).clean()
        ato(
            "linha-tempo:decadas",
            {"estacoes": [{**ESTACAO, "slug": "a-maquina-fria", "texto": "x"}]},
        ).clean()

    def test_invalidas(self):
        ruins = [
            [],
            "texto",
            [1],
            [{"titulo": "sem década"}],
            [{"decada": 1900, "titulo": "t"}],
            [{"decada": 2030, "titulo": "t"}],
            [{"decada": "1960", "titulo": "t"}],
            [{"decada": True, "titulo": "t"}],
            [{"decada": 1960, "titulo": " "}],
            [{"decada": 1960}],
            [{**ESTACAO, "slug": "com espaço"}],
            [{**ESTACAO, "texto": 3}],
            [{**ESTACAO, "extra": 1}],
        ]
        for ruim in ruins:
            with self.subTest(valor=ruim), self.assertRaises(ValidationError):
                ato("linha-tempo:decadas", {"estacoes": ruim}).clean()

    def test_intensidade_fora_da_faixa(self):
        with self.assertRaises(ValidationError):
            ato("linha-tempo:decadas", {"intensidade": 2}).clean()


class HubTests(TestCase):
    fixtures = ["imersivo_hub"]

    def setUp(self):
        from core.models import Episodio, Serie

        fria = PostImersivo.objects.create(
            slug="a-maquina-fria", titulo="A", publicado=True
        )
        placar = PostImersivo.objects.create(
            slug="o-placar", titulo="P", publicado=False
        )
        serie = Serie.objects.create(
            slug="ia-na-ficcao",
            titulo="S",
            publicado=True,
            hub=PostImersivo.objects.get(slug="ia-na-ficcao"),
        )
        Episodio.objects.create(
            serie=serie, numero=1, slug="a-maquina-fria", post=fria, publicado=True
        )
        Episodio.objects.create(
            serie=serie, numero=8, slug="o-placar", post=placar, publicado=True
        )
        self.r = self.client.get("/series/ia-na-ficcao/")
        self.html = self.r.content.decode()

    def test_fixture_valida(self):
        post = PostImersivo.objects.get(slug="ia-na-ficcao")
        self.assertTrue(post.publicado)
        self.assertEqual(post.atos.count(), 3)
        for a in post.atos.all():
            a.full_clean()
            self.assertEqual(a.reduzido, "estatico")

    def test_lista_e_atributos(self):
        self.assertEqual(self.r.status_code, 200)
        self.assertContains(self.r, '<ol class="im-linha">')
        self.assertContains(self.r, 'data-efeito="linha-tempo:decadas"')
        self.assertContains(self.r, 'tabindex="0" role="region" aria-label=')
        self.assertContains(self.r, '<li class="im-estacao', count=10)

    def test_ordem_das_decadas(self):
        import re

        decadas = [int(d) for d in re.findall(r'data-decada="(\d+)"', self.html)]
        self.assertEqual(len(decadas), 10)
        self.assertEqual(decadas, sorted(decadas))
        self.assertEqual(decadas[0], 1920)

    def test_link_so_para_publicado(self):
        self.assertContains(self.r, 'href="/series/ia-na-ficcao/a-maquina-fria/"')
        self.assertNotContains(self.r, 'href="/imersivo/')
        self.assertNotContains(self.r, 'href="/series/ia-na-ficcao/o-placar/"')
        self.assertNotContains(self.r, 'href="/series/ia-na-ficcao/o-quase-presente/"')
        self.assertContains(self.r, "O placar")

    def test_sem_imagens(self):
        self.assertNotIn("<img", self.html)

    def test_peso_do_efeito(self):
        from pathlib import Path

        raiz = Path(__file__).resolve().parents[2] / "static"
        total = (raiz / "js/imersivo/efeitos/linha-tempo-decadas.js").stat().st_size
        total += (raiz / "css/imersivo.css").stat().st_size
        self.assertLess(total, 50 * 1024)

    def test_cinco_chips(self):
        self.assertContains(self.r, 'class="im-chip"', count=5)
        self.assertContains(self.r, 'aria-pressed="false"', count=5)
        for rotulo in ("Quem manda?", "Quem luta?", "Quem sente?", "Quem cuida?"):
            self.assertContains(self.r, rotulo)
        self.assertContains(self.r, "Quem vê tudo?")
        self.assertContains(self.r, 'aria-live="polite"')
        self.assertContains(self.r, 'data-slugs="a-ia-afetiva o-que-e-ser-humano"')

    def test_data_slug_nas_estacoes(self):
        self.assertEqual(self.html.count('<li class="im-estacao'), 10)
        self.assertEqual(self.html.count('data-slug=""'), 2)
        self.assertContains(self.r, 'data-slug="a-maquina-fria"')

    def test_sem_formas_de_demonstracao(self):
        self.assertNotIn("im-forma", self.html)
        self.assertNotIn("im-passo", self.html)
        self.assertNotIn("/serie/fichas/", self.html)
        self.assertNotContains(self.r, 'data-efeito="scroll:revela"')
        self.assertNotContains(self.r, 'data-efeito="diagrama:constroi"')

    def test_grelha_links_e_em_breve(self):
        grelha = self.html.split('class="im-grelha"')[1].split("</ol>")[0]
        self.assertEqual(grelha.count("<li "), 2)
        self.assertIn('href="/series/ia-na-ficcao/a-maquina-fria/"', grelha)
        self.assertNotIn("o-placar", grelha)
        self.assertEqual(grelha.count("em breve"), 1)
        self.assertEqual(grelha.count("<a "), 1)

    def test_grelha_sem_o_hub_nem_noveno(self):
        grelha = self.html.split('class="im-grelha"')[1].split("</ol>")[0]
        self.assertNotIn('class="im-post-num">0<', grelha)
        self.assertNotIn('class="im-post-num">9<', grelha)

    def test_comecar_pelo_post_1(self):
        self.assertContains(
            self.r,
            '<a class="im-comecar" href="/series/ia-na-ficcao/a-maquina-fria/">'
            "Começar pelo post 1 →</a>",
        )

    def test_previa_svg_acessivel(self):
        self.assertContains(self.r, 'role="img" aria-labelledby="im-previa-t-403"')
        self.assertContains(self.r, '<title id="im-previa-t-403">', count=1)
        svg = self.html.split('aria-labelledby="im-previa-t-403"')[1].split("</svg>")[0]
        self.assertEqual(svg.count("<circle"), 3)
        self.assertContains(self.r, "no post 8")

    def test_tabelas_acessiveis(self):
        self.assertContains(self.r, "<caption>", count=2)
        self.assertContains(self.r, 'scope="col"', count=6)
        self.assertContains(self.r, "disponível")
        # A fixture do hub aponta para obras do placar (ids), não para pontos à mão.
        self.assertContains(self.r, "R.U.R. (Rossum")

    def test_css_hub(self):
        from pathlib import Path

        css = (
            Path(__file__).resolve().parents[2] / "static/css/imersivo.css"
        ).read_text()
        self.assertIn("im-estacao--fora", css)
        self.assertRegex(
            css,
            r"prefers-reduced-motion:no-preference\)\{\s*@supports[^{]*\{\s*"
            r"@view-transition",
        )


class HubSemEpisodiosTests(TestCase):
    fixtures = ["imersivo_hub"]

    def test_grelha_vazia_sem_link_de_comecar(self):
        from core.models import Serie

        Serie.objects.create(
            slug="ia-na-ficcao",
            titulo="S",
            publicado=True,
            hub=PostImersivo.objects.get(slug="ia-na-ficcao"),
        )
        r = self.client.get("/series/ia-na-ficcao/")
        self.assertEqual(r.status_code, 200)
        self.assertNotContains(r, "Começar pelo post 1")
        self.assertNotContains(r, 'class="im-grelha"')


PERGUNTA = {"id": "manda", "rotulo": "Quem manda?", "slugs": ["a-maquina-fria"]}
PONTO = {"obra": "R.U.R. (1920)", "x": 25, "y": 70}


class FiltroChipsValidacaoTests(TestCase):
    def test_validas(self):
        ato("filtro:chips", {"perguntas": [PERGUNTA]}).clean()
        ato("filtro:chips", {"perguntas": [{**PERGUNTA, "slugs": []}]}).clean()

    def test_invalidas(self):
        ruins = [
            [],
            "texto",
            [1],
            [{**PERGUNTA, "id": "com espaço"}],
            [{**PERGUNTA, "rotulo": " "}],
            [{**PERGUNTA, "rotulo": "x" * 41}],
            [{**PERGUNTA, "slugs": "a-maquina-fria"}],
            [{**PERGUNTA, "slugs": ["com espaço"]}],
            [{**PERGUNTA, "extra": 1}],
            [{"id": "a", "rotulo": "A"}],
            [PERGUNTA, PERGUNTA],
            [{**PERGUNTA, "id": str(i)} for i in range(9)],
        ]
        for ruim in ruins:
            with self.subTest(valor=ruim), self.assertRaises(ValidationError):
                ato("filtro:chips", {"perguntas": ruim}).clean()

    def test_chave_desconhecida(self):
        with self.assertRaises(ValidationError):
            ato("filtro:chips", {"intensidade": 1}).clean()


class GrelhaPostsValidacaoTests(TestCase):
    def test_validas(self):
        ato("grelha:posts", {"previa": [PONTO, {**PONTO, "x": 0, "y": 100}]}).clean()

    def test_invalidas(self):
        ruins = [
            [],
            "texto",
            [1],
            [{**PONTO, "x": 101}],
            [{**PONTO, "y": -1}],
            [{**PONTO, "x": "25"}],
            [{**PONTO, "x": True}],
            [{**PONTO, "obra": ""}],
            [{**PONTO, "extra": 1}],
            [{"obra": "A", "x": 1}],
            [PONTO] * 7,
        ]
        for ruim in ruins:
            with self.subTest(valor=ruim), self.assertRaises(ValidationError):
                ato("grelha:posts", {"previa": ruim}).clean()

    def test_pontos_em_coordenadas_do_svg(self):
        pontos = ato(
            "grelha:posts", {"previa": [PONTO, {**PONTO, "x": 100}]}
        ).previa_pontos
        self.assertEqual(pontos[0]["ancora"], "start")
        self.assertEqual(pontos[1]["ancora"], "end")
        self.assertTrue(
            all(50 <= p["cx"] <= 380 and 20 <= p["cy"] <= 210 for p in pontos)
        )


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
        self.assertContains(r, "Salvar meu caminho neste aparelho")
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


class AtmosferaPlacarTests(TestCase):
    fixtures = ["placar_post"]

    def _raiz(self):
        from pathlib import Path

        return Path(__file__).resolve().parents[2]

    def test_efeito_sem_parametros(self):
        ato("atmosfera:placar").clean()
        with self.assertRaises(ValidationError):
            ato("atmosfera:placar", {"fixar": True}).clean()

    def test_fixture_valida(self):
        post = PostImersivo.objects.get(slug="o-placar")
        self.assertEqual(post.pk, 9)
        self.assertTrue(post.publicado)
        for a in post.atos.all():
            self.assertEqual(a.pk, 20)
            self.assertEqual(a.reduzido, "estatico")
            a.full_clean()

    def test_renderiza_o_template_da_atmosfera(self):
        r = self.client.get(reverse("core:imersivo", args=["o-placar"]))
        self.assertEqual(r.status_code, 200)
        self.assertTemplateUsed(r, "core/imersivo_placar.html")
        self.assertTemplateNotUsed(r, "core/imersivo_escolhas.html")
        self.assertContains(r, 'data-efeito="atmosfera:placar"')
        self.assertContains(r, "css/atmosfera-placar.css")
        self.assertContains(r, "js/imersivo/motor.js")
        self.assertContains(r, 'class="pl-raiz"')
        self.assertContains(r, "Ficção · 8")
        self.assertContains(r, "Perto ou longe de 2026? E quanto preocupar?")
        self.assertContains(r, "Se aproximaram")
        self.assertNotContains(r, "Aproximaram-se")
        self.assertNotContains(r, "cdn.")
        self.assertNotContains(r, "Georgia")
        self.assertNotContains(r, "simulad")
        self.assertNotContains(r, "<img")

    def test_dados_30_obras(self):
        from core import placar

        obras = placar.obras()
        self.assertEqual(len(obras), 30)
        self.assertEqual(len({o["id"] for o in obras}), 30)
        for o in obras:
            with self.subTest(id=o["id"]):
                self.assertIn(o["midia"], placar.GRUPOS)
                for k in ("proximidade", "preocupacao"):
                    self.assertIsInstance(o[k], int)
                    self.assertTrue(0 <= o[k] <= 5)
                self.assertTrue(o["titulo"] and o["justificativa"])
        self.assertIn("be-right-back-2013", {o["id"] for o in obras})
        self.assertNotIn("black-mirror-be-right-back-2013", {o["id"] for o in obras})
        # Os destaques por fase do JS apontam para obras que existem.
        js = (
            self._raiz() / "static/js/imersivo/efeitos/atmosfera-placar.js"
        ).read_text()
        for id_ in re.findall(r"'([a-z0-9-]+-\d{4})'", js):
            self.assertIn(id_, {o["id"] for o in obras})

    def test_dados_no_json_script(self):
        r = self.client.get(reverse("core:imersivo", args=["o-placar"]))
        self.assertContains(r, '<script id="pl-dados" type="application/json">')
        self.assertEqual(len(r.context["placar_dados"]["obras"]), 30)

    def test_tabela_no_html(self):
        r = self.client.get(reverse("core:imersivo", args=["o-placar"]))
        html = r.content.decode()
        tbody = html.split("<tbody>")[1].split("</tbody>")[0]
        self.assertEqual(tbody.count("<tr "), 30)
        self.assertEqual(tbody.count('<th scope="row"'), 30)
        self.assertIn("Black Mirror: Be Right Back", tbody)
        self.assertIn("R.U.R.", tbody)
        # Sem JS a tabela está visível: não vem com o atributo hidden.
        self.assertNotRegex(html, r'<section[^>]*id="pl-tab-sec"[^>]*hidden')

    def test_css_escopado_e_reduzido(self):
        css = (self._raiz() / "static/css/atmosfera-placar.css").read_text()
        self.assertIn("--serif:var(--sg-serif)", css)
        self.assertNotIn("Georgia", css)
        self.assertNotIn(":root", css)
        # Sem imagens: o único url() é o da fonte Fraunces.
        for u in re.findall(r"url\(([^)]*)\)", css):
            self.assertIn("fraunces", u)
        self.assertIn("overflow-x:clip", css)
        self.assertNotIn("overflow-x:hidden", css)
        self.assertIn("prefers-reduced-motion:reduce", css)
        self.assertIn(".pl-estatico", css)
        self.assertIn(".pl-tab-sec[hidden]{display:block}", css)
        # Todo seletor fora de @font-face/@media vive em .pl-raiz.
        for seletor in re.findall(r"(?m)^\s*([^@{}/\s][^{}]*)\{", css):
            for parte in seletor.split(","):
                with self.subTest(seletor=parte.strip()):
                    self.assertTrue(parte.strip().startswith(".pl-raiz"))

    def test_js_dados_do_servidor_e_so_o_voto_na_rede(self):
        js = (
            self._raiz() / "static/js/imersivo/efeitos/atmosfera-placar.js"
        ).read_text()
        self.assertIn('registar("atmosfera:placar"', js)
        self.assertIn("reduzido", js)
        self.assertIn("JSON.parse($('#pl-dados').textContent)", js)
        # Exceção só deste ficheiro: o POST do voto usa fetch( (uma única chamada,
        # para o voto_url que o servidor entrega no json_script). Os dados das
        # obras nunca são pedidos por rede; continuam proibidos http, import( e
        # XMLHttpRequest.
        self.assertEqual(js.count("fetch("), 1)
        self.assertIn("fetch(DADOS.voto_url", js)
        self.assertIn("X-CSRFToken", js)
        self.assertNotIn("XMLHttpRequest", js)
        self.assertNotIn("http", js)
        self.assertNotIn("import(", js)
        self.assertNotIn("localStorage", js)
        # Escape e cliques escopados à raiz, sem listeners globais em document.
        self.assertIn("root.addEventListener('keydown'", js)
        self.assertNotIn("document.addEventListener", js)


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


class AtmosferaLeisRobosLivrosTests(TestCase):
    fixtures = ["leis_robos_livros"]

    def _raiz(self):
        from pathlib import Path

        return Path(__file__).resolve().parents[2]

    def test_efeito_sem_parametros(self):
        ato("atmosfera:leis-robos-livros").clean()
        with self.assertRaises(ValidationError):
            ato("atmosfera:leis-robos-livros", {"fixar": True}).clean()

    def test_fixture_valida(self):
        post = PostImersivo.objects.get(slug="leis-robos-e-livros")
        self.assertEqual(post.pk, 7)
        self.assertEqual(post.atos.count(), 1)
        for a in post.atos.all():
            self.assertEqual(a.pk, 18)
            self.assertEqual(a.reduzido, "estatico")
            a.full_clean()

    def test_renderiza_o_template_da_atmosfera(self):
        r = self.client.get(reverse("core:imersivo", args=["leis-robos-e-livros"]))
        self.assertEqual(r.status_code, 200)
        self.assertTemplateUsed(r, "core/imersivo_leis_robos_livros.html")
        self.assertTemplateNotUsed(r, "core/imersivo_escolhas.html")
        self.assertContains(r, 'data-efeito="atmosfera:leis-robos-livros"')
        self.assertContains(r, "css/atmosfera-leis-robos-livros.css")
        self.assertContains(r, "js/imersivo/motor.js")
        self.assertContains(r, 'id="lr-pista"')
        self.assertContains(r, 'id="lr-regra"')
        self.assertContains(r, "A IA na ficção · 5")
        self.assertContains(r, 'lr-curto">Post 5<')
        self.assertContains(r, "A IA na ficção · 5")
        self.assertContains(r, "Regras desta série · não as leis do livro")
        self.assertContains(r, "Conferir a regra")
        self.assertContains(r, "pausar movimento")
        self.assertContains(r, reverse("core:imersivo", args=["escolhas-da-maquina"]))
        self.assertNotContains(r, "cdn.")
        self.assertNotContains(r, "Georgia")
        self.assertNotContains(r, "http://")

    def test_narrador_na_era_0_de_1920(self):
        r = self.client.get(reverse("core:imersivo", args=["leis-robos-e-livros"]))
        self.assertContains(r, 'data-era="0"')
        self.assertContains(r, "data-parametros='{\"era\": 0}'")

    def test_sem_gravacao_no_servidor(self):
        r = self.client.get(reverse("core:imersivo", args=["leis-robos-e-livros"]))
        self.assertNotContains(r, "csrfmiddlewaretoken")
        self.assertNotContains(r, "action=")

    def test_css_escopado_e_reduzido(self):
        css = (self._raiz() / "static/css/atmosfera-leis-robos-livros.css").read_text()
        self.assertIn("--serif:var(--sg-serif)", css)
        self.assertNotIn("Georgia", css)
        self.assertNotIn(":root", css)
        self.assertNotIn("overflow-x:hidden", css)
        self.assertIn("overflow-x:clip", css)
        self.assertIn("prefers-reduced-motion:reduce", css)
        self.assertIn(".lr-raiz.lr-linear", css)
        self.assertIn(".lr-estatico", css)
        self.assertIn("top:76px", css)
        self.assertIn(".lr-fecho p.lr-fontes", css)

    def test_js_reduzido_e_sem_rede(self):
        js = (
            self._raiz() / "static/js/imersivo/efeitos/atmosfera-leis-robos-livros.js"
        ).read_text()
        self.assertIn('registar("atmosfera:leis-robos-livros"', js)
        self.assertIn("reduzido", js)
        self.assertEqual(
            js.count("if(reduzido){ alinha(1); reescreve(1); desenhaRede(1); return }"),
            2,
        )
        self.assertIn("pausar movimento", js)
        self.assertNotIn("fetch(", js)
        self.assertNotIn("XMLHttpRequest", js)
        self.assertNotIn("http", js)
        self.assertNotIn("import(", js)

    def test_sem_imagens_de_obras(self):
        pasta = self._raiz() / "static/img/leis-robos-livros"
        self.assertFalse(pasta.exists() and list(pasta.glob("*")))


class AtmosferaQuasePresenteTests(TestCase):
    fixtures = ["quase_presente"]

    def _raiz(self):
        from pathlib import Path

        return Path(__file__).resolve().parents[2]

    def test_efeito_sem_parametros(self):
        ato("atmosfera:quase-presente").clean()
        with self.assertRaises(ValidationError):
            ato("atmosfera:quase-presente", {"fixar": True}).clean()

    def test_fixture_valida(self):
        post = PostImersivo.objects.get(slug="o-quase-presente")
        self.assertEqual(post.pk, 8)
        self.assertEqual(post.atos.count(), 1)
        for a in post.atos.all():
            self.assertEqual(a.pk, 19)
            self.assertEqual(a.reduzido, "estatico")
            self.assertEqual(a.parametros, {})
            a.full_clean()

    def test_renderiza_o_template_da_atmosfera(self):
        r = self.client.get(reverse("core:imersivo", args=["o-quase-presente"]))
        self.assertEqual(r.status_code, 200)
        self.assertTemplateUsed(r, "core/imersivo_quase_presente.html")
        self.assertContains(r, 'data-efeito="atmosfera:quase-presente"')
        self.assertContains(r, "css/atmosfera-quase-presente.css")
        self.assertContains(r, "js/imersivo/motor.js")
        self.assertContains(r, "Ficção · 7")
        self.assertContains(r, "A IA na ficção · 7")
        self.assertContains(r, 'id="qp-rachas"')
        self.assertContains(r, 'href="#qp-rachas"')
        self.assertContains(r, 'id="qp-pausa"')
        url_placar = reverse("core:imersivo", args=["o-placar"])
        self.assertContains(
            r,
            f'href="{url_placar}">Próxima estação: <em>O placar</em>',
        )
        self.assertContains(r, 'href="/series/ia-na-ficcao/">← Voltar ao hub da série')
        self.assertNotContains(r, "nesta onda")
        self.assertNotContains(r, "cdn.")
        self.assertNotContains(r, "Georgia")
        self.assertNotContains(r, "http://")

    def test_sem_gravacao_no_servidor(self):
        r = self.client.get(reverse("core:imersivo", args=["o-quase-presente"]))
        self.assertNotContains(r, "csrfmiddlewaretoken")
        self.assertNotContains(r, "action=")

    def test_template_sem_sinks(self):
        html = (
            self._raiz() / "core/templates/core/imersivo_quase_presente.html"
        ).read_text()
        self.assertNotIn("|safe", html)
        self.assertNotIn("mark_safe", html)
        self.assertNotIn("javascript:", html)
        self.assertNotRegex(html, r"\son[a-z]+\s*=")

    def test_css_escopado_e_reduzido(self):
        css = (self._raiz() / "static/css/atmosfera-quase-presente.css").read_text()
        self.assertIn("--serif:var(--sg-serif)", css)
        self.assertNotIn("Georgia", css)
        self.assertNotIn(":root", css)
        self.assertNotIn("overflow-x:hidden", css)
        self.assertIn("overflow-x:clip", css)
        self.assertIn("prefers-reduced-motion:reduce", css)
        self.assertIn(".qp-estatico", css)
        self.assertIn("top:76px", css)
        self.assertIn("top:96px", css)
        self.assertIn("scale(.6)", css)
        self.assertIn(".qp-fecho p.qp-fontes", css)
        self.assertNotRegex(css, r"(?m)^(html|body)\b")

    def test_js_local_sem_rede_nem_sinks(self):
        js = (
            self._raiz() / "static/js/imersivo/efeitos/atmosfera-quase-presente.js"
        ).read_text()
        self.assertIn('registar("atmosfera:quase-presente"', js)
        for proibido in (
            "fetch(",
            "XMLHttpRequest",
            "http",
            "import(",
            "innerHTML",
            "insertAdjacentHTML",
            "document.documentElement",
            "localStorage",
        ):
            with self.subTest(proibido=proibido):
                self.assertNotIn(proibido, js)
        self.assertIn("aria-pressed", js)
        self.assertIn("reduzido", js)
        self.assertIn("qp-estatico", js)

    def test_peso_do_efeito(self):
        raiz = self._raiz() / "static"
        js = raiz / "js/imersivo/efeitos/atmosfera-quase-presente.js"
        total = js.stat().st_size
        total += (raiz / "css/atmosfera-quase-presente.css").stat().st_size
        self.assertLess(total, 60 * 1024)


class NavegacaoEntrePostsTests(TestCase):
    """STAR-47: fechos 6→7→8, 8→7 e «Voltar» ao hub da série."""

    fixtures = [
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

    def _passo(self, origem, destino):
        r = self.client.get(f"/series/ia-na-ficcao/{origem}/")
        self.assertEqual(r.status_code, 200)
        self.assertContains(r, f'href="/series/ia-na-ficcao/{destino}/"')
        self.assertContains(r, 'href="/series/ia-na-ficcao/">')
        self.assertNotContains(r, "Voltar à página inicial")
        self.assertEqual(
            self.client.get(f"/series/ia-na-ficcao/{destino}/").status_code, 200
        )
        return r

    def test_6_para_7(self):
        self._passo("escolhas-da-maquina", "o-quase-presente")

    def test_7_para_8(self):
        self._passo("o-quase-presente", "o-placar")

    def test_8_para_7_e_indice(self):
        r = self._passo("o-placar", "o-quase-presente")
        self.assertContains(r, 'aria-label="Os 9 pontos da série"')
        self.assertContains(r, "A máquina fria")
        self.assertContains(
            r,
            'href="/series/ia-na-ficcao/o-quase-presente/">O quase-presente</a></li>',
        )
