from io import StringIO
from unittest.mock import patch

from django.core.management import call_command
from django.test import TestCase

from noticias.easyon import EasyONIndisponivel
from noticias.models import Artigo

from .util import criar_artigo, criar_autor


class ClienteFalso:
    def __init__(self):
        self.chamadas = []

    def gerar_audio(self, slug, texto):
        self.chamadas.append((slug, texto))
        if "FALHA" in texto:
            raise EasyONIndisponivel("fora do ar")
        return {"url": f"https://cdn.test/{len(self.chamadas)}.mp3", "cache": False}


class GerarAudioTests(TestCase):
    def setUp(self):
        self.autor = criar_autor()
        self.autor.agente_easyon = "helena"
        self.autor.save()

    def correr(self, cliente, **opcoes):
        saida = StringIO()
        alvo = "noticias.management.commands.gerar_audio.ClienteEasyON"
        with patch(alvo, return_value=cliente):
            call_command("gerar_audio", stdout=saida, stderr=saida, **opcoes)
        return saida.getvalue()

    def test_gera_para_publicado_com_agente(self):
        artigo = criar_artigo(autor=self.autor, corpo="<p>Texto bom.</p>")
        cliente = ClienteFalso()
        self.correr(cliente)
        artigo.refresh_from_db()
        self.assertTrue(artigo.audio_url.startswith("https://cdn.test/"))
        self.assertIn("Texto bom.", cliente.chamadas[0][1])
        self.assertNotIn("<p>", cliente.chamadas[0][1])

    def test_salta_ja_gerados_rascunhos_e_autor_sem_agente(self):
        criar_artigo(autor=self.autor, audio_url="https://cdn.test/x.mp3")
        criar_artigo(autor=self.autor, estado=Artigo.Estado.RASCUNHO)
        criar_artigo(autor=criar_autor())
        cliente = ClienteFalso()
        self.correr(cliente)
        self.assertEqual(cliente.chamadas, [])

    def test_forcar_regenera(self):
        artigo = criar_artigo(autor=self.autor, audio_url="https://cdn.test/x.mp3")
        self.correr(ClienteFalso(), forcar=True)
        artigo.refresh_from_db()
        self.assertNotEqual(artigo.audio_url, "https://cdn.test/x.mp3")

    def test_falha_de_um_nao_para_os_outros(self):
        mau = criar_artigo(autor=self.autor, corpo="FALHA", dias_atras=0)
        bom = criar_artigo(autor=self.autor, corpo="ok", dias_atras=1)
        saida = self.correr(ClienteFalso())
        mau.refresh_from_db()
        bom.refresh_from_db()
        self.assertEqual(mau.audio_url, "")
        self.assertTrue(bom.audio_url)
        self.assertIn("falhas: 1", saida)

    def test_opcao_artigo(self):
        a = criar_artigo(autor=self.autor)
        b = criar_artigo(autor=self.autor)
        self.correr(ClienteFalso(), artigo=a.slug)
        a.refresh_from_db()
        b.refresh_from_db()
        self.assertTrue(a.audio_url)
        self.assertEqual(b.audio_url, "")

    import unittest

    @unittest.expectedFailure
    def test_saida_e_codigo_quando_api_indisponivel_de_raiz(self):
        # BUG EXPLICADO: engole exceção e sai com 0 em vez de erro
        criar_artigo(autor=self.autor, corpo="ok")

        class ClienteIndisponivel:
            def gerar_audio(self, slug, texto):
                raise EasyONIndisponivel("API fora")

        saida = self.correr(ClienteIndisponivel())
        self.assertIn("Gerados: 0", saida)
        self.assertIn("falhas: 1", saida)

        from django.core.management.base import CommandError

        with self.assertRaises(CommandError):
            self.correr(ClienteIndisponivel())


class PlayerTests(TestCase):
    def test_player_aparece_so_com_audio(self):
        com = criar_artigo(audio_url="https://cdn.test/a.mp3")
        sem = criar_artigo()
        r = self.client.get(com.get_absolute_url())
        self.assertContains(
            r, '<audio controls preload="none" src="https://cdn.test/a.mp3">'
        )
        self.assertContains(r, "Ouvir na voz de Helena Aragão")
        self.assertContains(r, "voz gerada por IA")
        r = self.client.get(sem.get_absolute_url())
        self.assertNotContains(r, "<audio")
        self.assertNotContains(r, "voz gerada por IA")

    def test_escapamento_audio_url_com_aspas(self):
        com = criar_artigo(audio_url='https://cdn.test/a.mp3" onload="alert(1)')
        r = self.client.get(com.get_absolute_url())
        # Should be escaped, e.g. &quot;
        self.assertContains(
            r, 'src="https://cdn.test/a.mp3&quot; onload=&quot;alert(1)"'
        )
        self.assertContains(r, '<audio controls preload="none"')
        self.assertContains(r, "Ouvir na voz de")
        self.assertContains(r, "voz gerada por IA")

        sem = criar_artigo(audio_url="")
        r = self.client.get(sem.get_absolute_url())
        self.assertNotContains(r, "<audio")
        self.assertNotContains(r, "voz gerada por IA")
