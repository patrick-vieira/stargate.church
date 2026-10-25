import os
import tempfile

from django.test import SimpleTestCase

from noticias.easyon import ClienteEasyON, EasyONIndisponivel

SEGREDO = "segredo-super-secreto-123"


class Falso:
    def __init__(self, resposta=None, erro=None):
        self.resposta, self.erro, self.chamadas = resposta, erro, []

    def __call__(self, metodo, url, cabecalhos, corpo, timeout):
        self.chamadas.append((metodo, url, cabecalhos, corpo, timeout))
        if self.erro:
            raise self.erro
        return self.resposta


class ClienteTests(SimpleTestCase):
    def chave(self, modo=0o600):
        fd, caminho = tempfile.mkstemp()
        self.addCleanup(os.unlink, caminho)
        os.write(fd, SEGREDO.encode())
        os.close(fd)
        os.chmod(caminho, modo)
        return caminho

    def cliente(self, transporte, modo=0o600):
        return ClienteEasyON("https://easyon.test/api/", self.chave(modo), transporte)

    def test_lista_agentes_com_bearer_e_timeout_curto(self):
        falso = Falso([{"slug": "helena", "nome": "Helena", "voz": "v1"}])
        self.assertEqual(self.cliente(falso).agentes()[0]["slug"], "helena")
        metodo, url, cab, _corpo, timeout = falso.chamadas[0]
        self.assertEqual((metodo, url), ("GET", "https://easyon.test/api/agentes/"))
        self.assertEqual(cab["Authorization"], f"Bearer {SEGREDO}")
        self.assertEqual(timeout, 5)

    def test_gerar_audio(self):
        falso = Falso({"url": "https://cdn.test/a.mp3", "cache": False})
        resposta = self.cliente(falso).gerar_audio("helena", "Olá")
        self.assertEqual(resposta["url"], "https://cdn.test/a.mp3")
        self.assertEqual(
            falso.chamadas[0][1], "https://easyon.test/api/agentes/helena/audio/"
        )
        self.assertEqual(falso.chamadas[0][3], {"texto": "Olá"})

    def test_chave_fora_de_600_recusada_sem_vazar(self):
        falso = Falso([])
        with self.assertRaises(EasyONIndisponivel) as ctx:
            self.cliente(falso, modo=0o644).agentes()
        self.assertNotIn(SEGREDO, str(ctx.exception))
        self.assertEqual(falso.chamadas, [])

    def test_erro_de_transporte_nao_vaza_a_chave(self):
        falso = Falso(erro=OSError(f"falhou com Bearer {SEGREDO}"))
        cliente = self.cliente(falso)
        with self.assertRaises(EasyONIndisponivel) as ctx:
            cliente.agentes()
        self.assertNotIn(SEGREDO, str(ctx.exception))
        self.assertNotIn(SEGREDO, repr(ctx.exception))
        self.assertNotIn(SEGREDO, repr(cliente))

    def test_sem_configuracao_e_indisponivel(self):
        with self.assertRaises(EasyONIndisponivel):
            ClienteEasyON("", "", Falso([])).agentes()

    def test_resposta_sem_url_e_indisponivel(self):
        with self.assertRaises(EasyONIndisponivel):
            self.cliente(Falso({"cache": True})).gerar_audio("h", "t")
