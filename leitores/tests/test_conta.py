from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

User = get_user_model()


class ContaTests(TestCase):
    def test_criar_conta_entra_logo(self):
        r = self.client.post(
            reverse("leitores:criar"),
            {"email": "Ana@Exemplo.com", "senha": "uma-senha-forte-91"},
        )
        self.assertRedirects(r, reverse("core:home"), fetch_redirect_response=False)
        user = User.objects.get(email="ana@exemplo.com")
        self.assertEqual(int(self.client.session["_auth_user_id"]), user.pk)

    def test_criar_recusa_senha_fraca_e_email_repetido(self):
        r = self.client.post(
            reverse("leitores:criar"), {"email": "a@b.com", "senha": "12345678"}
        )
        self.assertEqual(r.status_code, 200)
        self.assertFalse(User.objects.exists())
        User.objects.create_user("a@b.com", "a@b.com", "uma-senha-forte-91")
        r = self.client.post(
            reverse("leitores:criar"),
            {"email": "A@b.com", "senha": "outra-senha-forte-7"},
        )
        self.assertContains(r, "Já existe uma conta")

    def test_entrar_e_sair(self):
        User.objects.create_user("a@b.com", "a@b.com", "uma-senha-forte-91")
        r = self.client.post(
            reverse("leitores:entrar"),
            {"username": "a@b.com", "password": "uma-senha-forte-91"},
        )
        self.assertRedirects(r, reverse("core:home"), fetch_redirect_response=False)
        self.assertIn("_auth_user_id", self.client.session)
        self.assertEqual(self.client.get(reverse("leitores:sair")).status_code, 405)
        self.client.post(reverse("leitores:sair"))
        self.assertNotIn("_auth_user_id", self.client.session)

    def test_entrar_com_senha_errada(self):
        User.objects.create_user("a@b.com", "a@b.com", "uma-senha-forte-91")
        r = self.client.post(
            reverse("leitores:entrar"), {"username": "a@b.com", "password": "errada"}
        )
        self.assertEqual(r.status_code, 200)
        self.assertNotIn("_auth_user_id", self.client.session)

    def test_cabecalho_muda_com_o_login(self):
        self.assertContains(self.client.get(reverse("core:home")), "Entrar")
        User.objects.create_user("a@b.com", "a@b.com", "uma-senha-forte-91")
        self.client.login(username="a@b.com", password="uma-senha-forte-91")
        r = self.client.get(reverse("core:home"))
        self.assertContains(r, "a@b.com")
        self.assertContains(r, "Sair")

    def test_entrar_com_next_interno(self):
        User.objects.create_user(
            "leitor@example.com", "leitor@example.com", "senha-forte-123"
        )
        r = self.client.post(
            f"{reverse('leitores:entrar')}?next=/saude/",
            {"username": "leitor@example.com", "password": "senha-forte-123"},
        )
        self.assertRedirects(r, "/saude/", fetch_redirect_response=False)

    def test_entrar_com_next_externo_ignorado(self):
        User.objects.create_user(
            "leitor@example.com", "leitor@example.com", "senha-forte-123"
        )
        r = self.client.post(
            f"{reverse('leitores:entrar')}?next=http://malicioso.com",
            {"username": "leitor@example.com", "password": "senha-forte-123"},
        )
        self.assertRedirects(r, reverse("core:home"), fetch_redirect_response=False)

    def test_entrar_sendo_autenticado_redireciona(self):
        """Autenticado deve ser redirecionado ao acessar /conta/entrar/."""
        User.objects.create_user(
            "leitor@example.com", "leitor@example.com", "senha-forte-123"
        )
        self.client.login(username="leitor@example.com", password="senha-forte-123")
        r = self.client.get(reverse("leitores:entrar"))
        self.assertRedirects(r, reverse("core:home"), fetch_redirect_response=False)

    def test_criar_sendo_autenticado_redireciona(self):
        User.objects.create_user(
            "leitor@example.com", "leitor@example.com", "senha-forte-123"
        )
        self.client.login(username="leitor@example.com", password="senha-forte-123")
        r = self.client.get(reverse("leitores:criar"))
        self.assertRedirects(r, reverse("core:home"), fetch_redirect_response=False)

    def test_sair_por_get_nao_termina_sessao(self):
        User.objects.create_user(
            "leitor@example.com", "leitor@example.com", "senha-forte-123"
        )
        self.client.login(username="leitor@example.com", password="senha-forte-123")
        r = self.client.get(reverse("leitores:sair"))
        self.assertEqual(r.status_code, 405)
        self.assertIn("_auth_user_id", self.client.session)

    def test_criar_com_post_valido_autentica_e_vai_a_home(self):
        """Um POST válido deve criar a conta e redireccionar para core:home."""
        r = self.client.post(
            reverse("leitores:criar"),
            {"email": "novo.leitor@example.com", "senha": "Senha-forte-1234"},
        )
        self.assertRedirects(r, reverse("core:home"), fetch_redirect_response=False)
        self.assertTrue(User.objects.filter(email="novo.leitor@example.com").exists())
        self.assertIn("_auth_user_id", self.client.session)

    def test_csrf_sem_token_no_post_de_criar(self):
        from django.test import Client

        cliente_com_csrf = Client(enforce_csrf_checks=True)
        r = cliente_com_csrf.post(
            reverse("leitores:criar"),
            {"email": "leitor@example.com", "senha": "senha-forte-123"},
        )
        self.assertEqual(r.status_code, 403)
