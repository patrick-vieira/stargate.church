from django.contrib.auth import get_user_model
from django.test import TestCase

from leitores.forms import CriarContaForm

User = get_user_model()


class CriarContaFormTests(TestCase):
    def test_email_normalizado(self):
        form = CriarContaForm(
            data={"email": "  Leitor@Exemplo.com  ", "senha": "Uma-senha-forte-91"}
        )
        self.assertTrue(form.is_valid())
        self.assertEqual(form.cleaned_data["email"], "leitor@exemplo.com")

    def test_email_duplicado_mesma_grafia_rejeitado(self):
        User.objects.create_user(
            username="leitor@exemplo.com",
            email="leitor@exemplo.com",
            password="uma-senha-forte-91",
        )
        form = CriarContaForm(
            data={"email": "leitor@exemplo.com", "senha": "outra-senha-forte"}
        )
        self.assertFalse(form.is_valid())
        self.assertIn("email", form.errors)
        self.assertEqual(form.errors["email"], ["Já existe uma conta com este e-mail."])

    def test_email_duplicado_outra_grafia_rejeitado(self):
        User.objects.create_user(
            username="leitor@exemplo.com",
            email="leitor@exemplo.com",
            password="uma-senha-forte-91",
        )
        form = CriarContaForm(
            data={"email": "  LEITOR@exemplo.com ", "senha": "outra-senha-forte"}
        )
        self.assertFalse(form.is_valid())
        self.assertIn("email", form.errors)
        self.assertEqual(form.errors["email"], ["Já existe uma conta com este e-mail."])

    def test_senha_curta_ou_fraca(self):
        form = CriarContaForm(data={"email": "leitor@exemplo.com", "senha": "123"})
        self.assertFalse(form.is_valid())
        self.assertIn("senha", form.errors)

    def test_senha_igual_ao_email(self):
        form = CriarContaForm(
            data={"email": "leitor@exemplo.com", "senha": "leitor@exemplo.com"}
        )
        self.assertFalse(form.is_valid())
        self.assertIn("senha", form.errors)

    def test_guardar_cria_utilizador(self):
        form = CriarContaForm(
            data={"email": "leitor@exemplo.com", "senha": "Uma-senha-forte-91"}
        )
        self.assertTrue(form.is_valid())
        user = form.guardar()
        self.assertEqual(user.username, "leitor@exemplo.com")
        self.assertEqual(user.email, "leitor@exemplo.com")
        self.assertTrue(user.check_password("Uma-senha-forte-91"))
