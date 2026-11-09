"""STAR-54: retoques do pós-merge 2 (posts 2 e 4 a 390, PT-BR, comentário, 404)."""

from pathlib import Path

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

from leitores.forms import CriarContaForm, EntrarForm
from noticias.tests.util import criar_artigo

RAIZ = Path(__file__).resolve().parents[2]
User = get_user_model()
SENHA = "uma-senha-forte-91"


class RetoquesCssJsTests(TestCase):
    def test_pausa_do_post4_vira_barra_de_baixo_a_390(self):
        css = (RAIZ / "static/css/atmosfera-ia-afetiva.css").read_text()
        self.assertIn(
            "@media (max-width:600px){\n  .aa-btn-pausa{left:0;right:0;bottom:0", css
        )
        self.assertIn(".aa-raiz{padding-bottom:44px}", css)

    def test_narrador_do_post2_deixa_margem_direita_a_390(self):
        css = (RAIZ / "static/css/atmosfera-guerra-maquinas.css").read_text()
        self.assertIn("@media (max-width:600px){.ag-raiz{padding-right:36px}}", css)

    def test_ver_os_temas_abre_o_menu_a_390(self):
        html = self.client.get(reverse("core:home")).content.decode()
        self.assertIn('location.hash==="#temas"', html)
        self.assertIn("sg-menu-aberto", html)

    def test_esqueleto_em_reduzido_chama_pronto(self):
        js = (RAIZ / "static/js/carregando.js").read_text()
        self.assertIn("prefers-reduced-motion: reduce", js)
        self.assertIn("pronto(el);\n      return;", js)


class MensagensPtBrTests(TestCase):
    def test_login_errado_diz_email_ou_senha(self):
        User.objects.create_user("a@b.com", "a@b.com", SENHA)
        form = EntrarForm(data={"username": "a@b.com", "password": "errada"})
        self.assertFalse(form.is_valid())
        self.assertEqual(form.non_field_errors(), ["E-mail ou senha incorretos."])

    def test_cadastro_email_invalido_usa_e_mail(self):
        form = CriarContaForm(data={"email": "nao-e-email", "senha": SENHA})
        self.assertFalse(form.is_valid())
        self.assertEqual(form.errors["email"], ["Informe um e-mail válido."])


class AvisoDoComentarioTests(TestCase):
    def test_aviso_enviado_recebe_foco_e_scroll(self):
        user = User.objects.create_user(
            "leitor@exemplo.org", "leitor@exemplo.org", SENHA
        )
        artigo = criar_artigo()
        self.client.force_login(user)
        res = self.client.post(
            reverse("noticias:comentar", args=[artigo.slug]),
            {"nome": "Maria", "texto": "Ótima matéria."},
            follow=True,
        )
        self.assertContains(res, 'id="avisos-comentario"')
        self.assertContains(res, "scrollIntoView")
