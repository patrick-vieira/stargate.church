import os
import runpy
from pathlib import Path
from unittest import mock

from django.conf import settings
from django.test import SimpleTestCase


class SettingsTests(SimpleTestCase):
    def test_localizacao_pt_br(self):
        self.assertEqual(settings.LANGUAGE_CODE, "pt-br")
        self.assertEqual(settings.TIME_ZONE, "America/Sao_Paulo")

    def test_testes_correm_em_sqlite(self):
        self.assertEqual(
            settings.DATABASES["default"]["ENGINE"], "django.db.backends.sqlite3"
        )

    def test_static_root_default_e_variavel(self):
        caminho = Path(settings.BASE_DIR) / "config" / "settings" / "base.py"
        sem_variavel = {k: v for k, v in os.environ.items() if k != "STATIC_ROOT"}
        with mock.patch.dict(os.environ, sem_variavel, clear=True):
            padrao = runpy.run_path(str(caminho))["STATIC_ROOT"]
        self.assertEqual(padrao, Path(settings.BASE_DIR) / "staticfiles")
        with mock.patch.dict(os.environ, {"STATIC_ROOT": "/tmp/estaticos-x"}):
            mudado = runpy.run_path(str(caminho))["STATIC_ROOT"]
        self.assertEqual(mudado, Path("/tmp/estaticos-x"))

    def test_apps_do_projecto_instaladas(self):
        self.assertIn("core", settings.INSTALLED_APPS)
        self.assertIn("noticias", settings.INSTALLED_APPS)
