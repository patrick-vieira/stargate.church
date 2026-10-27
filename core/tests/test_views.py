from django.test import TestCase
from django.urls import reverse


class HomeTests(TestCase):
    def test_home_responde_200_em_portugues(self):
        resposta = self.client.get(reverse("core:home"))
        self.assertEqual(resposta.status_code, 200)
        self.assertContains(resposta, 'lang="pt-BR"')

    def test_home_devolve_o_mesmo_que_noticias_home(self):
        # Usamos o cliente de teste para não ignorar os middlewares
        resposta = self.client.get(reverse("core:home"))
        self.assertEqual(resposta.status_code, 200)
        self.assertTemplateUsed(resposta, "noticias/home.html")
        # Garante que as vars de contexto adicionadas pela view de notícias estão lá
        self.assertIn("manchete", resposta.context)
        self.assertIn("futuro_hoje", resposta.context)
        self.assertIn("ultimas", resposta.context)
        self.assertIn("numeros", resposta.context)


class SaudeTests(TestCase):
    def test_saude_responde_200_com_status_ok(self):
        # A test runner já cria um banco vazio.
        # Verifica-se se a API de saúde funciona sem banco
        resposta = self.client.get("/saude/")
        self.assertEqual(resposta.status_code, 200)
        self.assertEqual(resposta.json(), {"status": "ok"})
