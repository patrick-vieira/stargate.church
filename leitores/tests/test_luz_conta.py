from pathlib import Path

from django.conf import settings
from django.test import TestCase
from django.urls import reverse


class LuzContaTests(TestCase):
    def test_entrar_tem_marcacao_da_luz(self):
        html = self.client.get(reverse("leitores:entrar")).content.decode()
        self.assertIn('class="sg-cartao-conta" data-luz="nevoa"', html)
        self.assertEqual(html.count('<span class="luz-campo" data-luz="campo">'), 2)
        self.assertIn('type="submit" data-luz="botao"', html)
        self.assertIn("luz-servidor.js", html)

    def test_criar_tem_marcacao_da_luz(self):
        html = self.client.get(reverse("leitores:criar")).content.decode()
        self.assertIn('class="sg-cartao-conta" data-luz="nevoa"', html)
        self.assertEqual(html.count('<span class="luz-campo" data-luz="campo">'), 2)
        self.assertIn('type="submit" data-luz="botao"', html)

    def test_erro_mantem_ids_e_describedby(self):
        r = self.client.post(reverse("leitores:criar"), {"email": "", "senha": ""})
        html = r.content.decode()
        self.assertIn('id="erro-email"', html)
        self.assertIn('id="erro-senha"', html)
        self.assertIn('role="alert"', html)
        self.assertIn('aria-describedby="erro-email"', html)

    def test_entrar_com_erro_non_field_marca_os_dois_campos(self):
        r = self.client.post(
            reverse("leitores:entrar"), {"username": "x@y.org", "password": "errada"}
        )
        html = r.content.decode()
        self.assertIn('id="erro-geral"', html)
        self.assertEqual(html.count('aria-invalid="true"'), 2)
        self.assertEqual(html.count('aria-describedby="erro-geral"'), 2)

    def test_newsletter_nao_aparece_nas_paginas_de_conta(self):
        for nome in ("leitores:entrar", "leitores:criar"):
            self.assertNotContains(self.client.get(reverse(nome)), 'id="assinar"')

    def test_cola_servidor_existe_e_nao_e_inline(self):
        raiz = Path(settings.BASE_DIR) / "static" / "js" / "luz-servidor.js"
        self.assertTrue(raiz.exists())
        self.assertIn("aria-invalid", raiz.read_text())

    def test_borda_dos_campos_de_conta_com_contraste(self):
        css = (Path(settings.BASE_DIR) / "static" / "css" / "stargate.css").read_text()
        linha = next(
            ln for ln in css.splitlines() if ln.startswith(".sg-form--conta input:not")
        )
        self.assertIn("border:1px solid var(--sg-campo-borda)", linha)
