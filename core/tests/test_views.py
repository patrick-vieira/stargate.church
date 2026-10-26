from django.test import TestCase
from django.urls import reverse


class HomeTests(TestCase):
    def test_home_responde_200_em_portugues(self):
        resposta = self.client.get(reverse("core:home"))
        self.assertEqual(resposta.status_code, 200)
        self.assertContains(resposta, 'lang="pt-BR"')


class SaudeTests(TestCase):
    def test_saude_responde_200_com_status_ok(self):
        resposta = self.client.get("/saude/")
        self.assertEqual(resposta.status_code, 200)
        self.assertEqual(resposta.json(), {"status": "ok"})
