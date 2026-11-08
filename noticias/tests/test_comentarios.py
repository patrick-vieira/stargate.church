from django.contrib.auth import get_user_model
from django.template import Context, Template
from django.test import Client, TestCase, override_settings
from django.urls import reverse

from leitores.models import UsoDiario
from noticias.forms import ComentarioForm
from noticias.models import Artigo, Comentario
from noticias.tests.util import criar_artigo

User = get_user_model()
SENHA = "uma-senha-forte-91"
EMAIL = "leitor@exemplo.org"


@override_settings(STARGATE_TECTO_COMENTARIO=2)
class ComentarViewTests(TestCase):
    def setUp(self):
        self.artigo = criar_artigo()
        self.url = reverse("noticias:comentar", args=[self.artigo.slug])
        self.user = User.objects.create_user(EMAIL, EMAIL, SENHA)
        self.dados = {"nome": "Maria", "texto": "Ótima matéria."}

    def test_anonimo_vai_para_login(self):
        res = self.client.post(self.url, self.dados)
        self.assertEqual(res.status_code, 302)
        self.assertIn(reverse("leitores:entrar"), res.url)
        self.assertEqual(Comentario.objects.count(), 0)

    def test_get_nao_permitido(self):
        self.client.force_login(self.user)
        self.assertEqual(self.client.get(self.url).status_code, 405)

    def test_csrf_exigido(self):
        cliente = Client(enforce_csrf_checks=True)
        cliente.force_login(self.user)
        self.assertEqual(cliente.post(self.url, self.dados).status_code, 403)

    def test_cria_pendente_com_nome_sem_email(self):
        self.client.force_login(self.user)
        res = self.client.post(self.url, self.dados)
        self.assertRedirects(res, self.artigo.get_absolute_url())
        c = Comentario.objects.get()
        self.assertEqual(c.estado, Comentario.Estado.PENDENTE)
        self.assertEqual(c.nome, "Maria")
        self.assertEqual(c.autor, self.user)
        self.assertNotIn(EMAIL, c.nome + c.texto)

    def test_xss_escapado_na_saida(self):
        self.client.force_login(self.user)
        self.client.post(self.url, {"nome": "x", "texto": "<script>alert(1)</script>"})
        c = Comentario.objects.get()
        html = Template("{{ c.texto }}").render(Context({"c": c}))
        self.assertNotIn("<script>", html)
        self.assertIn("&lt;script&gt;", html)

    def test_form_invalido_nao_gasta_tecto(self):
        self.client.force_login(self.user)
        self.client.post(self.url, {"nome": "  ", "texto": ""})
        self.assertEqual(Comentario.objects.count(), 0)
        self.assertEqual(UsoDiario.objects.count(), 0)

    def test_tecto_devolve_429(self):
        self.client.force_login(self.user)
        codigos = [self.client.post(self.url, self.dados).status_code for _ in range(3)]
        self.assertEqual(codigos, [302, 302, 429])
        self.assertEqual(Comentario.objects.count(), 2)

    def test_artigo_nao_publicado_404(self):
        rascunho = criar_artigo(estado=Artigo.Estado.RASCUNHO)
        self.client.force_login(self.user)
        url = reverse("noticias:comentar", args=[rascunho.slug])
        self.assertEqual(self.client.post(url, self.dados).status_code, 404)


class ComentarioFormTests(TestCase):
    def test_limites_e_espacos(self):
        self.assertFalse(ComentarioForm({"nome": "a", "texto": "x" * 1001}).is_valid())
        self.assertFalse(ComentarioForm({"nome": "   ", "texto": "oi"}).is_valid())
        f = ComentarioForm({"nome": " Ana ", "texto": " oi "})
        self.assertTrue(f.is_valid())
        self.assertEqual(f.cleaned_data, {"nome": "Ana", "texto": "oi"})


class ComentarioAdminTests(TestCase):
    def test_acoes_publicar_e_ocultar(self):
        artigo = criar_artigo()
        user = User.objects.create_user("l@exemplo.org", "l@exemplo.org", SENHA)
        c = Comentario.objects.create(artigo=artigo, autor=user, nome="N", texto="t")
        self.assertEqual(c.estado, Comentario.Estado.PENDENTE)
        adm = User.objects.create_superuser("adm", "adm@exemplo.org", SENHA)
        self.client.force_login(adm)
        url = reverse("admin:noticias_comentario_changelist")
        self.client.post(url, {"action": "publicar", "_selected_action": [c.pk]})
        c.refresh_from_db()
        self.assertEqual(c.estado, Comentario.Estado.PUBLICADO)
        self.client.post(url, {"action": "ocultar", "_selected_action": [c.pk]})
        c.refresh_from_db()
        self.assertEqual(c.estado, Comentario.Estado.OCULTO)
