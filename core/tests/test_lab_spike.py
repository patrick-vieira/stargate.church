from django.test import TestCase
from django.urls import reverse


class LabSpikeTests(TestCase):
    def setUp(self):
        self.resposta = self.client.get(reverse("core:lab_spike"))

    def test_rota_responde_200(self):
        self.assertEqual(reverse("core:lab_spike"), "/lab/spike/")
        self.assertEqual(self.resposta.status_code, 200)
        self.assertTemplateUsed(self.resposta, "core/lab_spike.html")

    def test_import_map_com_versoes_fixas(self):
        self.assertContains(self.resposta, 'type="importmap"')
        self.assertContains(self.resposta, "three@0.160.0")
        self.assertContains(self.resposta, "@rive-app/canvas@2.21.6")

    def test_modo_reduzido_e_atos_presentes(self):
        self.assertContains(self.resposta, "prefers-reduced-motion")
        self.assertContains(self.resposta, 'data-efeito="three:gira"')
        self.assertContains(self.resposta, 'data-efeito="rive:estado"')
        self.assertContains(self.resposta, 'data-efeito="diagrama:constroi"')

    def test_diagrama_svg_e_ponto_de_ligacao_do_rive(self):
        self.assertContains(self.resposta, '<svg viewBox="0 0 400 120"')
        self.assertContains(self.resposta, "lab/exemplo.riv")
