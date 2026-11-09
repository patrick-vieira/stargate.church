import importlib.util
import os
import sys

from django.test import SimpleTestCase


class TestVerificarMensagens(SimpleTestCase):
    """Testes para a função linhas_proibidas do script de verificação."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        caminho_script = os.path.join(
            os.path.dirname(__file__), "../../scripts/verificar_mensagens.py"
        )
        spec = importlib.util.spec_from_file_location(
            "verificar_mensagens", caminho_script
        )
        modulo = importlib.util.module_from_spec(spec)
        sys.modules["verificar_mensagens"] = modulo
        spec.loader.exec_module(modulo)
        cls.linhas_proibidas = staticmethod(modulo.linhas_proibidas)

    def test_mensagem_limpa_retorna_lista_vazia(self):
        mensagem = "Commit normal sem trailers especiais"
        resultado = self.linhas_proibidas(mensagem)
        self.assertEqual(resultado, [])

    def test_co_author_by_minusculo_com_espacos(self):
        mensagem = "Mensagem de commit\n\nco-authored-by: X <x@exemplo.com>"
        resultado = self.linhas_proibidas(mensagem)
        self.assertEqual(resultado, ["co-authored-by: X <x@exemplo.com>"])

    def test_co_author_by_maiusculo_com_espacos(self):
        mensagem = "Mensagem de commit\n\nCo-Authored-By: X <x@exemplo.com>"
        resultado = self.linhas_proibidas(mensagem)
        self.assertEqual(resultado, ["Co-Authored-By: X <x@exemplo.com>"])

    def test_co_author_by_com_espacos_a_esquerda(self):
        mensagem = "Mensagem de commit\n\n  co-authored-by: X <x@exemplo.com>"
        resultado = self.linhas_proibidas(mensagem)
        self.assertEqual(resultado, ["  co-authored-by: X <x@exemplo.com>"])

    def test_multiplas_linhas_proibidas(self):
        mensagem = (
            "Mensagem\n\nco-authored-by: X <x@exemplo.com>\n"
            "co-authored-by: Y <y@exemplo.com>"
        )
        resultado = self.linhas_proibidas(mensagem)
        self.assertEqual(
            resultado,
            ["co-authored-by: X <x@exemplo.com>", "co-authored-by: Y <y@exemplo.com>"],
        )

    def test_texto_que_so_contem_co_author_by_nao_conta(self):
        mensagem = "Este commit foi co-authored-by alguém mas não é trailer"
        resultado = self.linhas_proibidas(mensagem)
        self.assertEqual(resultado, [])

    def test_coautor_noreply_e_aceite(self):
        mensagem = "Msg\n\nCo-Authored-By: Assistente <noreply@exemplo.com>"
        self.assertEqual(self.linhas_proibidas(mensagem), [])
