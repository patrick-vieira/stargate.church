from django.core.exceptions import ValidationError
from django.db import IntegrityError, transaction
from django.test import TestCase

from noticias.models import Artigo, Autor, Fonte, Tema


class ArtigoTestBase(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.autor = Autor.objects.create(nome="Ana IA", slug="ana-ia")
        cls.fonte = Fonte.objects.create(nome="Agência", url="https://exemplo.org/a")

    def novo_artigo(self, slug="um-artigo", **kwargs):
        return Artigo.objects.create(
            titulo="Um artigo", slug=slug, autor=self.autor, **kwargs
        )


class TransicoesTests(ArtigoTestBase):
    def test_estado_inicial_e_rascunho(self):
        artigo = self.novo_artigo()
        self.assertEqual(artigo.estado, Artigo.Estado.RASCUNHO)
        self.assertIsNone(artigo.publicado_em)

    def test_verificar_e_publicar(self):
        artigo = self.novo_artigo()
        artigo.fontes.add(self.fonte)
        artigo.verificar()
        artigo.refresh_from_db()
        self.assertEqual(artigo.estado, Artigo.Estado.VERIFICADO)
        artigo.publicar()
        artigo.refresh_from_db()
        self.assertEqual(artigo.estado, Artigo.Estado.PUBLICADO)
        self.assertIsNotNone(artigo.publicado_em)

    def test_publicar_rascunho_falha(self):
        artigo = self.novo_artigo()
        artigo.fontes.add(self.fonte)
        with self.assertRaises(ValidationError):
            artigo.publicar()
        artigo.refresh_from_db()
        self.assertEqual(artigo.estado, Artigo.Estado.RASCUNHO)

    def test_verificar_duas_vezes_falha(self):
        artigo = self.novo_artigo()
        artigo.verificar()
        with self.assertRaises(ValidationError):
            artigo.verificar()

    def test_verificar_publicado_falha(self):
        artigo = self.novo_artigo()
        artigo.fontes.add(self.fonte)
        artigo.verificar()
        artigo.publicar()
        with self.assertRaises(ValidationError):
            artigo.verificar()
        with self.assertRaises(ValidationError):
            artigo.publicar()

    def test_publicar_sem_fonte_falha(self):
        artigo = self.novo_artigo()
        artigo.verificar()
        with self.assertRaises(ValidationError):
            artigo.publicar()
        artigo.refresh_from_db()
        self.assertEqual(artigo.estado, Artigo.Estado.VERIFICADO)
        self.assertIsNone(artigo.publicado_em)


class UnicidadeTests(ArtigoTestBase):
    def test_slug_unico_artigo(self):
        self.novo_artigo(slug="repetido")
        with self.assertRaises(IntegrityError), transaction.atomic():
            self.novo_artigo(slug="repetido")

    def test_slug_unico_tema(self):
        Tema.objects.create(nome="Fé", slug="fe")
        with self.assertRaises(IntegrityError), transaction.atomic():
            Tema.objects.create(nome="Fé 2", slug="fe")

    def test_url_unica_fonte(self):
        with self.assertRaises(IntegrityError), transaction.atomic():
            Fonte.objects.create(nome="Outra", url=self.fonte.url)


class StrTests(ArtigoTestBase):
    def test_str(self):
        self.assertEqual(str(self.autor), "Ana IA")
        self.assertEqual(str(self.fonte), "Agência")
        self.assertEqual(str(Tema(nome="Fé", slug="fe")), "Fé")
        self.assertEqual(str(self.novo_artigo()), "Um artigo")
