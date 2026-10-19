from django.test import TestCase

from noticias import servicos
from noticias.models import Artigo

from .util import criar_artigo, criar_tema


class ProcessarCorpoTests(TestCase):
    def test_gera_id_para_h2_sem_id(self):
        html, indice = servicos.processar_corpo("<p>a</p><h2>O que mudou</h2><p>b</p>")
        self.assertIn('<h2 id="o-que-mudou">O que mudou</h2>', html)
        self.assertEqual(indice, [("o-que-mudou", "O que mudou")])

    def test_preserva_id_existente(self):
        html, indice = servicos.processar_corpo('<h2 id="a1">Início</h2>')
        self.assertIn('<h2 id="a1">Início</h2>', html)
        self.assertEqual(indice, [("a1", "Início")])

    def test_ids_repetidos_ganham_sufixo(self):
        _, indice = servicos.processar_corpo("<h2>Etapa</h2><h2>Etapa</h2>")
        self.assertEqual([i for i, _ in indice], ["etapa", "etapa-2"])

    def test_texto_do_indice_sem_marcacao(self):
        _, indice = servicos.processar_corpo("<h2>Baterias <em>e</em> rede</h2>")
        self.assertEqual(indice[0], ("baterias-e-rede", "Baterias e rede"))

    def test_corpo_vazio(self):
        html, indice = servicos.processar_corpo("")
        self.assertEqual((html, indice), ("", []))


class SelecaoDeArtigosTests(TestCase):
    def test_publicados_exclui_rascunho_e_verificado(self):
        publicado = criar_artigo()
        criar_artigo(estado=Artigo.Estado.RASCUNHO)
        criar_artigo(estado=Artigo.Estado.VERIFICADO)
        self.assertEqual(list(servicos.artigos_publicados()), [publicado])

    def test_manchete_e_o_destaque_mais_recente(self):
        criar_artigo(titulo="Recente comum")
        criar_artigo(titulo="Destaque antigo", destaque=True, dias_atras=5)
        novo = criar_artigo(titulo="Destaque novo", destaque=True, dias_atras=2)
        self.assertEqual(servicos.manchete(), novo)

    def test_destaque_em_rascunho_nao_vira_manchete(self):
        criar_artigo(destaque=True, estado=Artigo.Estado.RASCUNHO)
        recente = criar_artigo()
        self.assertEqual(servicos.manchete(), recente)

    def test_sem_destaque_a_manchete_e_o_mais_recente(self):
        criar_artigo(dias_atras=3)
        recente = criar_artigo(dias_atras=1)
        self.assertEqual(servicos.manchete(), recente)

    def test_sem_artigos_nao_ha_manchete(self):
        self.assertIsNone(servicos.manchete())

    def test_futuro_hoje_tem_quatro_e_exclui_a_manchete(self):
        destaque = criar_artigo(destaque=True, dias_atras=0)
        for dias in range(1, 8):
            criar_artigo(dias_atras=dias)
        lista = servicos.futuro_hoje(destaque)
        self.assertEqual(len(lista), 4)
        self.assertNotIn(destaque, lista)

    def test_ultimas_tem_seis_por_pagina_e_pagina_seguinte(self):
        artigos = [criar_artigo(dias_atras=d) for d in range(8)]
        pagina1 = servicos.ultimas([artigos[0]], None)
        self.assertEqual(len(pagina1), 6)
        self.assertNotIn(artigos[0], pagina1)
        pagina2 = servicos.ultimas([artigos[0]], 2)
        self.assertEqual(len(pagina2), 1)

    def test_pagina_invalida_cai_na_ultima_ou_primeira(self):
        for d in range(3):
            criar_artigo(dias_atras=d)
        self.assertEqual(servicos.ultimas([], "abc").number, 1)
        self.assertEqual(servicos.ultimas([], 99).number, 1)

    def test_relacionados_so_do_mesmo_tema_e_sem_o_proprio(self):
        energia, saude = criar_tema("Energia"), criar_tema("Saúde")
        base = criar_artigo(temas=[energia])
        mesmo = criar_artigo(temas=[energia], dias_atras=1)
        criar_artigo(temas=[saude], dias_atras=1)
        criar_artigo(temas=[energia], estado=Artigo.Estado.RASCUNHO)
        self.assertEqual(servicos.relacionados(base), [mesmo])

    def test_relacionados_limita_a_tres(self):
        tema = criar_tema("Clima")
        base = criar_artigo(temas=[tema])
        for d in range(1, 6):
            criar_artigo(temas=[tema], dias_atras=d)
        self.assertEqual(len(servicos.relacionados(base)), 3)
