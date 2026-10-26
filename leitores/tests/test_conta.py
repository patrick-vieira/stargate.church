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
        self.assertContains(r, 'for="id_email"')
        self.assertContains(r, 'aria-describedby="erro-email"')

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
        self.assertContains(r, 'for="id_username"')

    def test_cabecalho_muda_com_o_login(self):
        self.assertContains(self.client.get(reverse("core:home")), "Entrar")
        User.objects.create_user("a@b.com", "a@b.com", "uma-senha-forte-91")
        self.client.login(username="a@b.com", password="uma-senha-forte-91")
        r = self.client.get(reverse("core:home"))
        self.assertContains(r, "a@b.com")
        self.assertContains(r, "Sair")
