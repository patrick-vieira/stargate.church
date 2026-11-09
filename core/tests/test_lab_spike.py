from django.test import TestCase
from django.urls import reverse


class LabSpikeTests(TestCase):
    def setUp(self):
        self.resposta = self.client.get(reverse("core:lab_spike"))

    def test_rota_responde_200(self):
        self.assertEqual(reverse("core:lab_spike"), "/lab/spike/")
        self.assertEqual(self.resposta.status_code, 200)
        self.assertTemplateUsed(self.resposta, "core/lab_spike.html")

    def test_import_map_local_do_three(self):
        self.assertContains(self.resposta, 'type="importmap"')
        self.assertContains(self.resposta, "lab/vendor/three-0.160.0.module.js")
        self.assertNotContains(self.resposta, "cdn.jsdelivr.net")

    def test_modo_reduzido_e_atos_presentes(self):
        self.assertContains(self.resposta, "prefers-reduced-motion")
        self.assertContains(self.resposta, 'data-efeito="three:gira"')
        self.assertContains(self.resposta, 'data-efeito="rive:estado"')
        self.assertContains(self.resposta, 'data-efeito="diagrama:constroi"')

    def test_diagrama_svg(self):
        self.assertContains(self.resposta, '<svg viewBox="0 0 400 120"')

    def test_rive_local_2_35_0_com_viewmodel(self):
        self.assertContains(self.resposta, "lab/rive/stargate-leitura.riv")
        self.assertContains(self.resposta, "lab/vendor/rive-canvas-2.35.0.js")
        self.assertContains(self.resposta, "lab/vendor/rive-2.35.0.wasm")
        self.assertContains(self.resposta, 'data-riv-prop="progressoLeitura"')
