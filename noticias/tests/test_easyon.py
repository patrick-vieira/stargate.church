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

    def test_url_final_com_ou_sem_barra(self):
        falso1 = Falso([])
        ClienteEasyON("https://easyon.test/api/", self.chave(), falso1).agentes()
        self.assertEqual(falso1.chamadas[0][1], "https://easyon.test/api/agentes/")

        falso2 = Falso([])
        ClienteEasyON("https://easyon.test/api", self.chave(), falso2).agentes()
        self.assertEqual(falso2.chamadas[0][1], "https://easyon.test/api/agentes/")

    def test_gerar_audio_metodo_post(self):
        falso = Falso({"url": "https://cdn.test/a.mp3", "cache": False})
        self.cliente(falso).gerar_audio("helena", "Olá")
        self.assertEqual(falso.chamadas[0][0], "POST")
        self.assertEqual(
            falso.chamadas[0][1], "https://easyon.test/api/agentes/helena/audio/"
        )
        self.assertEqual(falso.chamadas[0][3], {"texto": "Olá"})

    def test_resposta_nao_dict_e_indisponivel(self):
        for resposta in [[], None, "string"]:
            with self.subTest(resposta=resposta):
                with self.assertRaises(EasyONIndisponivel):
                    self.cliente(Falso(resposta)).gerar_audio("h", "t")

    def test_ficheiro_chave_invalido_recusado_sem_vazar(self):
        # 400
        falso = Falso([])
        with self.assertRaises(EasyONIndisponivel) as ctx:
            self.cliente(falso, modo=0o400).agentes()
        self.assertNotIn(SEGREDO, str(ctx.exception))

        # vazio
        vazio = tempfile.mktemp()
        open(vazio, "w").close()
        os.chmod(vazio, 0o600)
        self.addCleanup(os.unlink, vazio)
        with self.assertRaises(EasyONIndisponivel) as ctx:
            ClienteEasyON("https://a/", vazio, falso).agentes()
        self.assertNotIn(SEGREDO, str(ctx.exception))

        # inexistente
        inexistente = tempfile.mktemp()
        with self.assertRaises(EasyONIndisponivel) as ctx:
            ClienteEasyON("https://a/", inexistente, falso).agentes()
        self.assertNotIn(SEGREDO, str(ctx.exception))

    def test_repr_nao_contem_chave_nem_caminho(self):
        caminho = self.chave()
        cliente = ClienteEasyON("https://a/", caminho, Falso([]))
        representacao = repr(cliente)
        self.assertNotIn(SEGREDO, representacao)
        self.assertNotIn(caminho, representacao)

    def test_erro_de_transporte_cause_none(self):
        falso = Falso(erro=OSError(f"falhou com Bearer {SEGREDO}"))
        cliente = self.cliente(falso)
        with self.assertRaises(EasyONIndisponivel) as ctx:
            cliente.agentes()
        self.assertNotIn(SEGREDO, str(ctx.exception))
        self.assertIsNone(ctx.exception.__cause__)
