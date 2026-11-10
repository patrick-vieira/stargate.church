from pathlib import Path

from django.test import TestCase, override_settings
from django.urls import reverse

RAIZ = Path(__file__).resolve().parents[2]


class PaginaNaoEncontradaTests(TestCase):
    @override_settings(DEBUG=False, ALLOWED_HOSTS=["testserver"])
    def test_404_autonoma_com_caminho_de_volta(self):
        self.client.raise_request_exception = False
        r = self.client.get("/isto-nao-existe/")
        self.assertEqual(r.status_code, 404)
        self.assertContains(r, "sinal", status_code=404)
        self.assertContains(r, f'href="{reverse("core:home")}"', status_code=404)
        self.assertContains(r, f'href="{reverse("core:home")}#temas"', status_code=404)
        self.assertTemplateUsed(r, "404.html")
        self.assertTemplateNotUsed(r, "noticias/base.html")
        self.assertNotContains(r, "http://", status_code=404)
        self.assertNotContains(r, "https://", status_code=404)


class TransicaoTests(TestCase):
    def test_base_com_clima_fundo_e_ancora_dos_temas(self):
        r = self.client.get(reverse("core:home"))
        self.assertContains(
            r, '<html lang="pt-BR" data-clima="padrao" data-envelope="base"'
        )
        self.assertContains(r, "html{background:#FBF5EA;--vt-fundo:#FBF5EA}")
        self.assertContains(r, 'id="temas" aria-label="Temas"')
        self.assertContains(r, "css/transicao.css")
        html = r.content.decode()
        self.assertIn('js/transicao.js"></script>', html)  # síncrono, sem defer

    def test_imersivos_sobrepoem_o_clima(self):
        t = {
            "core/imersivo_guerra_maquinas.html": ('data-clima="glitch"', "#07090D"),
            "core/imersivo_maquina_fria.html": ('data-clima="padrao"', "#0B0C0E"),
            "core/imersivo_escolhas.html": ('data-clima="padrao"', "#0D1022"),
        }
        for nome, (clima, cor) in t.items():
            src = (RAIZ / "core/templates" / nome).read_text()
            self.assertIn("{% block clima %}" + clima.split('"')[1], src)
            self.assertIn(f"--vt-fundo:{cor}", src)

    def test_cenas_pesadas_tem_esqueleto(self):
        src = (RAIZ / "core/templates/core/imersivo.html").read_text()
        self.assertEqual(src.count('data-carrega="three"'), 2)
        self.assertEqual(src.count('data-carrega="rive"'), 1)
        self.assertEqual(src.count("car-esq__txt"), 3)

    def test_efeitos_avisam_o_carregando(self):
        for nome in ("three-corredor", "three-gira", "rive-estado"):
            js = (RAIZ / f"static/js/imersivo/efeitos/{nome}.js").read_text()
            self.assertIn("window.Carregando", js)
            self.assertIn('carrega("pronto")', js)
            self.assertIn('carrega("erro")', js)

    def test_transicao_sem_ganchos_de_prova_nem_important_global(self):
        css = (RAIZ / "static/css/transicao.css").read_text()
        js = (RAIZ / "static/js/transicao.js").read_text()
        for txt in (css, js):
            self.assertNotIn("vt-registro", txt)
            self.assertNotIn("vt-k", txt)
        self.assertNotIn("*,*::before,*::after", css)

    def test_onda6_contraste_burger_desativados_e_link_sublinhado(self):
        css = (RAIZ / "static/css/luz.css").read_text()
        self.assertIn(".sg-burger{border-color:var(--sg-tinta-3)}", css)
        self.assertIn(".sg-btn[disabled]{opacity:1;", css)
        self.assertIn(".sg-form input[disabled]{opacity:1;", css)
        self.assertIn(".sg-cartao-conta .sg-meta a{", css)
        self.assertIn("text-decoration:underline", css)

    def test_assets_novos_sem_rede_externa(self):
        for rel in (
            "static/css/transicao.css",
            "static/css/carregando.css",
            "static/js/transicao.js",
            "static/js/carregando.js",
            "core/templates/404.html",
        ):
            txt = (RAIZ / rel).read_text()
            self.assertNotIn("http:", txt, rel)
            self.assertNotIn("https:", txt, rel)
