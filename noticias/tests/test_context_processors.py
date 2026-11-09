import unittest

from django.test import RequestFactory, TestCase

from noticias import servicos
from noticias.context_processors import portal
from noticias.models import Tema

from .util import criar_tema


class ContextProcessorTests(TestCase):
    def test_portal_retorna_hoje_e_temas_menu(self):
        req = RequestFactory().get("/")
        resultado = portal(req)
        self.assertIn("hoje", resultado)
        self.assertIn("temas_menu", resultado)
        self.assertEqual(resultado["hoje"], servicos.hoje())
        self.assertEqual(resultado["temas_menu"], servicos.temas_do_menu())

    def test_temas_menu_reflete_temas_criados(self):
        tema_a = criar_tema("Tema A")
        tema_b = criar_tema("Tema B")
        req = RequestFactory().get("/")
        resultado = portal(req)
        self.assertEqual(resultado["temas_menu"], [tema_a, tema_b])

    def test_temas_menu_vazio_sem_erro(self):
        Tema.objects.all().delete()
        req = RequestFactory().get("/")
        resultado = portal(req)
        self.assertEqual(resultado["temas_menu"], [])

    def test_portal_registado_nas_settings_e_contexto(self):
        tema = criar_tema("Tema")
        resposta = self.client.get("/")
        self.assertIn("hoje", resposta.context)
        self.assertIn("temas_menu", resposta.context)
        self.assertEqual(resposta.context["hoje"], servicos.hoje())
        self.assertEqual(resposta.context["temas_menu"], [tema])

    @unittest.expectedFailure
    def test_numero_de_queries(self):
        # A query é executada de imediato com o list() em servicos.temas_do_menu(),
        # causando 1 query extra em todas as páginas, mesmo que não seja usada.
        criar_tema("A")
        criar_tema("B")
        req = RequestFactory().get("/")
        with self.assertNumQueries(0):
            portal(req)
