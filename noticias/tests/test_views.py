from django.core.management import call_command
from django.test import TestCase
from django.urls import reverse

from noticias.models import Artigo, NumeroDestaque

from .util import criar_artigo, criar_fonte, criar_tema


class HomeTests(TestCase):
    def setUp(self):
        self.futuro = criar_tema("Futuro")
        self.energia = criar_tema("Energia")

    def get(self, **params):
        return self.client.get(reverse("core:home"), params)

    def test_home_200_em_pt_br_com_data_em_minuscula(self):
        resposta = self.get()
        self.assertEqual(resposta.status_code, 200)
        self.assertContains(resposta, 'lang="pt-BR"')
        texto = resposta.content.decode()
        self.assertRegex(texto, r"<span>[a-zç\-]+, \d{1,2} de [a-zç]+ de \d{4}</span>")
        self.assertNotRegex(texto, r"<span>[A-Z][a-z\-]+, \d")

    def test_so_publicados_aparecem(self):
        criar_artigo(titulo="Visível")
        criar_artigo(titulo="Oculto rascunho", estado=Artigo.Estado.RASCUNHO)
        criar_artigo(titulo="Oculto verificado", estado=Artigo.Estado.VERIFICADO)
        resposta = self.get()
        self.assertContains(resposta, "Visível")
        self.assertNotContains(resposta, "Oculto")

    def test_manchete_e_o_artigo_em_destaque(self):
        criar_artigo(titulo="Notícia comum")
        criar_artigo(titulo="Grande destaque", destaque=True, dias_atras=3)
        resposta = self.get()
        self.assertEqual(resposta.context["manchete"].titulo, "Grande destaque")
        self.assertContains(resposta, "<h1>Grande destaque</h1>", html=True)

    def test_limites_e_paginacao(self):
        criar_artigo(titulo="Manchete", destaque=True)
        for d in range(1, 14):
            criar_artigo(dias_atras=d)
        resposta = self.get()
        self.assertEqual(len(resposta.context["futuro_hoje"]), 4)
        self.assertEqual(len(resposta.context["ultimas"]), 6)
        self.assertContains(resposta, "?pagina=2#ultimas")
        # Sem repetir os já exibidos acima.
        mostrados = {a.pk for a in resposta.context["futuro_hoje"]}
        self.assertFalse(mostrados & {a.pk for a in resposta.context["ultimas"]})
        pagina2 = self.get(pagina=2)
        self.assertEqual(pagina2.status_code, 200)
        self.assertEqual(pagina2.context["ultimas"].number, 2)

    def test_numeros_em_destaque_ativos(self):
        NumeroDestaque.objects.create(
            valor="89%",
            texto="de queda",
            fonte_texto="Painel fictício",
            tema=self.energia,
        )
        NumeroDestaque.objects.create(
            valor="0%", texto="inativo", fonte_texto="X", ativo=False
        )
        resposta = self.get()
        self.assertContains(resposta, "Boas notícias em números")
        self.assertContains(resposta, "<strong>89%</strong>", html=True)
        self.assertNotContains(resposta, "inativo")

    def test_newsletter_sem_envio(self):
        resposta = self.get()
        texto = resposta.content.decode()
        self.assertContains(resposta, 'class="sg-news"')
        self.assertIn('<form class="sg-form" action="#assinar">', texto)
        self.assertNotIn("csrfmiddlewaretoken", texto)
        self.assertNotIn("onsubmit", texto)
        self.assertNotIn('type="submit"', texto)
        self.assertIn('type="button" disabled', texto)

    def test_rodape_mantem_aviso_ficticio(self):
        self.assertContains(self.get(), "Todo o conteúdo deste protótipo é fictício")

    def test_fallback_svg_sem_imagem_e_img_com_imagem(self):
        criar_artigo(temas=[self.futuro], destaque=True)
        self.assertContains(self.get(), "<svg", status_code=200)
        Artigo.objects.update(imagem_url="https://exemplo.org/foto.jpg")
        resposta = self.get()
        self.assertContains(resposta, 'src="https://exemplo.org/foto.jpg"')

    def test_home_vazia_nao_quebra(self):
        resposta = self.get()
        self.assertEqual(resposta.status_code, 200)
        self.assertNotContains(resposta, "sg-manchete")

    def test_nav_de_temas_com_links(self):
        resposta = self.get()
        self.assertContains(resposta, reverse("noticias:tema", args=["futuro"]))
        self.assertContains(resposta, reverse("noticias:tema", args=["energia"]))


class TemaTests(TestCase):
    def test_lista_so_publicados_do_tema_com_aria_current(self):
        clima, ia = criar_tema("Clima"), criar_tema("IA")
        criar_artigo(titulo="Do clima", temas=[clima])
        criar_artigo(titulo="Da IA", temas=[ia])
        criar_artigo(
            titulo="Clima oculto", temas=[clima], estado=Artigo.Estado.RASCUNHO
        )
        resposta = self.client.get(reverse("noticias:tema", args=["clima"]))
        self.assertContains(resposta, "Do clima")
        self.assertNotContains(resposta, "Da IA")
        self.assertNotContains(resposta, "Clima oculto")
        self.assertContains(resposta, 'aria-current="page">Clima</a>')

    def test_tema_inexistente_404(self):
        resposta = self.client.get(reverse("noticias:tema", args=["nada"]))
        self.assertEqual(resposta.status_code, 404)


class ArtigoTests(TestCase):
    def setUp(self):
        self.energia = criar_tema("Energia")
        self.saude = criar_tema("Saúde")
        self.artigo = criar_artigo(
            titulo="Rede do amanhã",
            temas=[self.energia],
            fontes=3,
            corpo=(
                "<p>Abertura.</p><h2>Primeira parte</h2><p>a</p>"
                "<h2>Segunda parte</h2><p>b</p>"
            ),
            porque_boa_noticia="<p>Porque sim.</p>",
        )

    def get(self, artigo=None):
        return self.client.get((artigo or self.artigo).get_absolute_url())

    def test_artigo_200_com_autor_e_funcao(self):
        resposta = self.get()
        self.assertEqual(resposta.status_code, 200)
        self.assertContains(resposta, "<h1>Rede do amanhã</h1>", html=True)
        self.assertContains(resposta, "Helena Aragão")
        self.assertContains(resposta, ", repórter de energia")
        self.assertContains(resposta, "5 min de leitura")

    def test_nao_publicado_da_404(self):
        for estado in (Artigo.Estado.RASCUNHO, Artigo.Estado.VERIFICADO):
            outro = criar_artigo(estado=estado)
            self.assertEqual(self.get(outro).status_code, 404)
        resposta = self.client.get(reverse("noticias:artigo", args=["inexistente"]))
        self.assertEqual(resposta.status_code, 404)

    def test_selo_com_contagem_e_ancora_para_validacao(self):
        resposta = self.get()
        self.assertContains(resposta, 'href="#validacao-de-fatos"')
        self.assertContains(resposta, "Verificado · 3 fontes")
        self.assertContains(resposta, 'id="validacao-de-fatos"')

    def test_selo_no_singular_e_abaixo_da_linha_do_autor(self):
        unico = criar_artigo(fontes=1)
        texto = self.get(unico).content.decode()
        self.assertIn("Verificado · 1 fonte<", texto)
        self.assertLess(texto.index('class="sg-autor"'), texto.index("sg-selo-link"))

    def test_indice_gerado_dos_h2(self):
        resposta = self.get()
        self.assertContains(
            resposta, '<h2 id="primeira-parte">Primeira parte</h2>', html=True
        )
        self.assertContains(resposta, 'href="#segunda-parte"')
        self.assertEqual(
            resposta.context["indice"],
            [("primeira-parte", "Primeira parte"), ("segunda-parte", "Segunda parte")],
        )

    def test_fontes_e_validacao_de_fatos(self):
        resposta = self.get()
        for fonte in self.artigo.fontes.all():
            self.assertContains(resposta, f'href="{fonte.url}"', count=2)
            self.assertContains(resposta, fonte.descricao)
        self.assertContains(resposta, "Fontes verificadas")
        self.assertContains(resposta, "Validação de fatos")
        self.assertContains(resposta, "verificado</span>", count=3)

    def test_so_fontes_confiaveis_contam_e_aparecem(self):
        misto = criar_artigo(fontes=2)
        intrusa = criar_fonte(
            nome="Fonte duvidosa", descricao="Sem lastro.", confiavel=False
        )
        misto.fontes.add(intrusa)
        resposta = self.get(misto)
        self.assertContains(resposta, "Verificado · 2 fontes")
        self.assertNotContains(resposta, "Fonte duvidosa")
        self.assertNotContains(resposta, intrusa.url)
        self.assertContains(resposta, "verificado</span>", count=2)

    def test_sem_fonte_confiavel_sem_selo_nem_quadro(self):
        so_duvidosa = criar_artigo(fontes=0)
        so_duvidosa.fontes.add(criar_fonte(confiavel=False))
        resposta = self.get(so_duvidosa)
        self.assertNotContains(resposta, "Verificado")
        self.assertNotContains(resposta, "Fontes verificadas")
        self.assertNotContains(resposta, "Validação de fatos")

    def test_porque_boa_noticia_so_com_texto(self):
        self.assertContains(self.get(), "Porque sim.")
        sem = criar_artigo(fontes=1)
        self.assertNotContains(self.get(sem), "Por que isto é uma boa notícia")

    def test_continue_lendo_so_do_mesmo_tema_e_sem_o_proprio(self):
        mesmo = criar_artigo(titulo="Mesmo tema", temas=[self.energia], dias_atras=1)
        criar_artigo(titulo="Outro tema", temas=[self.saude], dias_atras=1)
        resposta = self.get()
        self.assertContains(resposta, "Continue lendo")
        self.assertEqual(resposta.context["relacionados"], [mesmo])
        self.assertNotContains(resposta, "Outro tema")
        self.assertContains(resposta, reverse("noticias:artigo", args=[mesmo.slug]))

    def test_data_em_minuscula_e_por_extenso(self):
        texto = self.get().content.decode()
        self.assertIn("domingo, 18 de outubro de 2026", texto)

    def test_aria_current_no_tema_do_artigo(self):
        self.assertContains(self.get(), 'aria-current="page">Energia</a>')

    def test_fallback_svg_sem_imagem(self):
        resposta = self.get()
        self.assertContains(resposta, '<svg viewBox="0 0 1000 600"')
        self.assertContains(resposta, "Ilustração abstrata do tema energia")

    def test_imagem_url_substitui_o_svg(self):
        Artigo.objects.filter(pk=self.artigo.pk).update(
            imagem_url="https://exemplo.org/a.jpg"
        )
        resposta = self.get()
        self.assertContains(resposta, 'src="https://exemplo.org/a.jpg"')
        self.assertNotContains(resposta, "Ilustração abstrata do tema energia")

    def test_artigo_sem_newsletter_e_com_script_do_indice(self):
        resposta = self.get()
        self.assertNotContains(resposta, 'class="sg-news"')
        self.assertContains(resposta, "sg-indice details")


class FixtureDemoTests(TestCase):
    def setUp(self):
        call_command("loaddata", "stargate_demo", verbosity=0)

    def test_fixture_carrega_com_rascunho_e_numeros(self):
        self.assertGreaterEqual(Artigo.objects.filter(estado="publicado").count(), 9)
        self.assertTrue(Artigo.objects.filter(estado="rascunho").exists())
        self.assertEqual(NumeroDestaque.objects.count(), 4)

    def test_home_com_a_fixture(self):
        resposta = self.client.get(reverse("core:home"))
        self.assertEqual(resposta.status_code, 200)
        self.assertEqual(
            resposta.context["manchete"].titulo,
            "A rede elétrica do amanhã já está acendendo",
        )
        self.assertEqual(len(resposta.context["futuro_hoje"]), 4)
        self.assertEqual(len(resposta.context["ultimas"]), 6)
        self.assertNotContains(resposta, "ainda não foi verificada")

    def test_artigo_destaque_renderiza(self):
        destaque = Artigo.objects.get(destaque=True, estado="publicado")
        resposta = self.client.get(destaque.get_absolute_url())
        self.assertEqual(resposta.status_code, 200)
        self.assertContains(resposta, "Verificado · 3 fontes")
        self.assertContains(resposta, '<h2 id="a1">O que mudou</h2>', html=True)
        self.assertContains(resposta, "<blockquote>")
        self.assertEqual(len(resposta.context["indice"]), 4)

    def test_rascunho_da_fixture_da_404(self):
        rascunho = Artigo.objects.get(estado="rascunho")
        self.assertEqual(self.client.get(rascunho.get_absolute_url()).status_code, 404)
