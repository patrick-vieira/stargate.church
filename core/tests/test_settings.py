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

    def test_apps_do_projecto_instaladas(self):
        self.assertIn("core", settings.INSTALLED_APPS)
        self.assertIn("noticias", settings.INSTALLED_APPS)
