from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

from noticias.models import Artigo, Autor, Fonte, NumeroDestaque, Tema
from noticias.tests import util


class AdminTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        User = get_user_model()
        cls.admin_user = User.objects.create_superuser(
            username="admin", email="admin@example.com", password="password"
        )

    def test_anonymous_redirected_to_login(self):
        urls = [
            reverse("admin:noticias_tema_changelist"),
            reverse("admin:noticias_fonte_changelist"),
            reverse("admin:noticias_autor_changelist"),
            reverse("admin:noticias_artigo_changelist"),
            reverse("admin:noticias_numerodestaque_changelist"),
        ]
        for url in urls:
            with self.subTest(url=url):
                response = self.client.get(url)
                self.assertEqual(response.status_code, 302)
                self.assertTrue(response.url.startswith(reverse("admin:login")))

    def test_changelists_empty_and_populated(self):
        self.client.force_login(self.admin_user)

        # Test empty
        urls_and_models = [
            (reverse("admin:noticias_tema_changelist"), Tema),
            (reverse("admin:noticias_fonte_changelist"), Fonte),
            (reverse("admin:noticias_autor_changelist"), Autor),
            (reverse("admin:noticias_artigo_changelist"), Artigo),
            (reverse("admin:noticias_numerodestaque_changelist"), NumeroDestaque),
        ]

        for url, _model in urls_and_models:
            with self.subTest(url=url, state="empty"):
                response = self.client.get(url)
                self.assertEqual(response.status_code, 200)

        # Populate with data
        tema = util.criar_tema("Tema Teste")
        util.criar_fonte("Fonte Teste")
        autor = util.criar_autor("Autor Teste")
        util.criar_artigo("Artigo Teste", autor=autor, temas=[tema], fontes=1)
        NumeroDestaque.objects.create(
            valor="100", texto="Testes", fonte_texto="Fonte", tema=tema
        )

        for url, _model in urls_and_models:
            with self.subTest(url=url, state="populated"):
                response = self.client.get(url)
                self.assertEqual(response.status_code, 200)

    def test_changelists_list_display_columns(self):
        self.client.force_login(self.admin_user)

        # Populando para garantir que as colunas apareçam (tabela HTML renderizada)
        tema = util.criar_tema("Tema Colunas")
        util.criar_fonte("Fonte Colunas")
        autor = util.criar_autor("Autor Colunas")
        util.criar_artigo("Artigo Colunas", autor=autor, temas=[tema], fontes=1)
        NumeroDestaque.objects.create(
            valor="200", texto="Cols", fonte_texto="Fonte", tema=tema
        )

        # Tema
        response = self.client.get(reverse("admin:noticias_tema_changelist"))
        self.assertContains(response, "column-nome")
        self.assertContains(response, "column-slug")

        # Fonte
        response = self.client.get(reverse("admin:noticias_fonte_changelist"))
        self.assertContains(response, "column-nome")
        self.assertContains(response, "column-url")
        self.assertContains(response, "column-descricao")
        self.assertContains(response, "column-confiavel")

        # Autor
        response = self.client.get(reverse("admin:noticias_autor_changelist"))
        self.assertContains(response, "column-nome")
        self.assertContains(response, "column-slug")
        self.assertContains(response, "column-funcao")
        self.assertContains(response, "column-ativo")

        # Artigo
        response = self.client.get(reverse("admin:noticias_artigo_changelist"))
        self.assertContains(response, "column-titulo")
        self.assertContains(response, "column-autor")
        self.assertContains(response, "column-estado")
        self.assertContains(response, "column-destaque")
        self.assertContains(response, "column-criado_em")
        self.assertContains(response, "column-publicado_em")

        # NumeroDestaque
        response = self.client.get(reverse("admin:noticias_numerodestaque_changelist"))
        self.assertContains(response, "column-valor")
        self.assertContains(response, "column-texto")
        self.assertContains(response, "column-tema")
        self.assertContains(response, "column-ordem")
        self.assertContains(response, "column-ativo")

    def test_filters(self):
        self.client.force_login(self.admin_user)

        # Filters:
        # ArtigoAdmin: estado, destaque, temas
        # FonteAdmin: confiavel
        # AutorAdmin: ativo
        # NumeroDestaqueAdmin: ativo, tema

        # Test just the GET requests with filter parameters to ensure they don't crash

        tema1 = util.criar_tema("Tema F1")
        util.criar_fonte("Fonte F1", confiavel=True)
        autor1 = util.criar_autor("Autor F1")
        util.criar_artigo(
            "Artigo F1",
            autor=autor1,
            temas=[tema1],
            fontes=1,
            estado=Artigo.Estado.PUBLICADO,
        )
        NumeroDestaque.objects.create(
            valor="300", texto="Filtro", fonte_texto="F", tema=tema1, ativo=True
        )

        # Artigo filters
        response = self.client.get(
            reverse("admin:noticias_artigo_changelist"), {"estado__exact": "publicado"}
        )
        self.assertEqual(response.status_code, 200)
        response = self.client.get(
            reverse("admin:noticias_artigo_changelist"), {"destaque__exact": "1"}
        )
        self.assertEqual(response.status_code, 200)
        response = self.client.get(
            reverse("admin:noticias_artigo_changelist"), {"temas__id__exact": tema1.pk}
        )
        self.assertEqual(response.status_code, 200)

        # Fonte filter
        response = self.client.get(
            reverse("admin:noticias_fonte_changelist"), {"confiavel__exact": "1"}
        )
        self.assertEqual(response.status_code, 200)

        # Autor filter
        response = self.client.get(
            reverse("admin:noticias_autor_changelist"), {"ativo__exact": "1"}
        )
        self.assertEqual(response.status_code, 200)

        # NumeroDestaque filters
        response = self.client.get(
            reverse("admin:noticias_numerodestaque_changelist"), {"ativo__exact": "1"}
        )
        self.assertEqual(response.status_code, 200)
        response = self.client.get(
            reverse("admin:noticias_numerodestaque_changelist"),
            {"tema__id__exact": tema1.pk},
        )
        self.assertEqual(response.status_code, 200)

    def test_search(self):
        self.client.force_login(self.admin_user)

        # Search fields:
        # Tema: nome, slug
        # Fonte: nome, url
        # Autor: nome, slug
        # Artigo: titulo, slug, resumo

        tema2 = util.criar_tema("BuscaTema")
        util.criar_fonte("BuscaFonte")
        autor2 = util.criar_autor("BuscaAutor")
        artigo2 = util.criar_artigo(
            "BuscaArtigo", autor=autor2, temas=[tema2], fontes=1
        )
        artigo2.resumo = "Resumo busca"
        artigo2.save()

        # Tema search
        response = self.client.get(
            reverse("admin:noticias_tema_changelist"), {"q": "BuscaTema"}
        )
        self.assertContains(response, "BuscaTema")

        # Fonte search
        response = self.client.get(
            reverse("admin:noticias_fonte_changelist"), {"q": "BuscaFonte"}
        )
        self.assertContains(response, "BuscaFonte")

        # Autor search
        response = self.client.get(
            reverse("admin:noticias_autor_changelist"), {"q": "BuscaAutor"}
        )
        self.assertContains(response, "BuscaAutor")

        # Artigo search
        response = self.client.get(
            reverse("admin:noticias_artigo_changelist"), {"q": "BuscaArtigo"}
        )
        self.assertContains(response, "BuscaArtigo")
        response = self.client.get(
            reverse("admin:noticias_artigo_changelist"), {"q": "Resumo busca"}
        )
        self.assertContains(response, "BuscaArtigo")

    def test_action_verificar_artigos_success(self):
        self.client.force_login(self.admin_user)
        artigo1 = util.criar_artigo("Artigo Rascunho 1", estado=Artigo.Estado.RASCUNHO)
        artigo2 = util.criar_artigo("Artigo Rascunho 2", estado=Artigo.Estado.RASCUNHO)

        response = self.client.post(
            reverse("admin:noticias_artigo_changelist"),
            {
                "action": "verificar_artigos",
                "_selected_action": [artigo1.pk, artigo2.pk],
            },
            follow=True,
        )

        self.assertContains(response, "2 artigo(s) verificado(s).")
        artigo1.refresh_from_db()
        artigo2.refresh_from_db()
        self.assertEqual(artigo1.estado, Artigo.Estado.VERIFICADO)
        self.assertEqual(artigo2.estado, Artigo.Estado.VERIFICADO)

    def test_action_verificar_artigos_mixed(self):
        self.client.force_login(self.admin_user)
        artigo1 = util.criar_artigo("Artigo Rascunho", estado=Artigo.Estado.RASCUNHO)
        artigo2 = util.criar_artigo("Artigo Publicado", estado=Artigo.Estado.PUBLICADO)

        response = self.client.post(
            reverse("admin:noticias_artigo_changelist"),
            {
                "action": "verificar_artigos",
                "_selected_action": [artigo1.pk, artigo2.pk],
            },
            follow=True,
        )

        self.assertContains(response, "1 artigo(s) verificado(s).")
        self.assertContains(
            response, "Artigo Publicado: Só é possível verificar um artigo em rascunho"
        )

        artigo1.refresh_from_db()
        artigo2.refresh_from_db()
        self.assertEqual(artigo1.estado, Artigo.Estado.VERIFICADO)
        self.assertEqual(artigo2.estado, Artigo.Estado.PUBLICADO)

    def test_action_publicar_artigos_success(self):
        self.client.force_login(self.admin_user)
        artigo1 = util.criar_artigo(
            "Artigo Verificado", estado=Artigo.Estado.VERIFICADO, fontes=1
        )

        response = self.client.post(
            reverse("admin:noticias_artigo_changelist"),
            {
                "action": "publicar_artigos",
                "_selected_action": [artigo1.pk],
            },
            follow=True,
        )

        self.assertContains(response, "1 artigo(s) publicado(s).")
        artigo1.refresh_from_db()
        self.assertEqual(artigo1.estado, Artigo.Estado.PUBLICADO)

    def test_action_publicar_artigos_mixed(self):
        self.client.force_login(self.admin_user)
        artigo1 = util.criar_artigo(
            "Artigo Verificado", estado=Artigo.Estado.VERIFICADO, fontes=1
        )
        artigo2 = util.criar_artigo(
            "Artigo Sem Fonte", estado=Artigo.Estado.VERIFICADO, fontes=0
        )

        response = self.client.post(
            reverse("admin:noticias_artigo_changelist"),
            {
                "action": "publicar_artigos",
                "_selected_action": [artigo1.pk, artigo2.pk],
            },
            follow=True,
        )

        self.assertContains(response, "1 artigo(s) publicado(s).")
        self.assertContains(
            response, "Artigo Sem Fonte: Publicar exige ao menos uma fonte."
        )

        artigo1.refresh_from_db()
        artigo2.refresh_from_db()
        self.assertEqual(artigo1.estado, Artigo.Estado.PUBLICADO)
        self.assertEqual(artigo2.estado, Artigo.Estado.VERIFICADO)

    def test_numero_destaque_list_editable(self):
        self.client.force_login(self.admin_user)
        tema = util.criar_tema("Tema Num")
        num1 = NumeroDestaque.objects.create(
            valor="1", texto="T1", fonte_texto="F1", tema=tema, ordem=1, ativo=True
        )
        num2 = NumeroDestaque.objects.create(
            valor="2", texto="T2", fonte_texto="F2", tema=tema, ordem=2, ativo=False
        )

        # We need to simulate the changelist form submission for list_editable
        response = self.client.post(
            reverse("admin:noticias_numerodestaque_changelist"),
            {
                "form-TOTAL_FORMS": "2",
                "form-INITIAL_FORMS": "2",
                "form-MIN_NUM_FORMS": "0",
                "form-MAX_NUM_FORMS": "1000",
                "form-0-id": str(num1.pk),
                "form-0-ordem": "10",
                # no ativo for form-0 means unchecked
                "form-1-id": str(num2.pk),
                "form-1-ordem": "20",
                "form-1-ativo": "on",
                "_save": "Salvar",
            },
            follow=True,
        )

        self.assertEqual(response.status_code, 200)
        num1.refresh_from_db()
        num2.refresh_from_db()
        self.assertEqual(num1.ordem, 10)
        self.assertFalse(num1.ativo)
        self.assertEqual(num2.ordem, 20)
        self.assertTrue(num2.ativo)
