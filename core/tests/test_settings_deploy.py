import importlib
import os
from unittest import mock

from django.core.exceptions import ImproperlyConfigured
from django.test import SimpleTestCase

ENV_MINIMO = {
    "DJANGO_SECRET_KEY": "chave-ficticia-de-teste",
    "DJANGO_ALLOWED_HOSTS": "exemplo.test",
}
VARIAVEIS = (
    "DJANGO_SECURE_SSL_REDIRECT",
    "DJANGO_SESSION_COOKIE_SECURE",
    "DJANGO_CSRF_COOKIE_SECURE",
    "DJANGO_CSRF_TRUSTED_ORIGINS",
    "DJANGO_SECURE_HSTS_SECONDS",
    "DJANGO_SECURE_HSTS_INCLUDE_SUBDOMAINS",
    "DJANGO_SECURE_HSTS_PRELOAD",
)


def carregar(modulo, **extra):
    """Importa (recarregando) prod ou staging com um env controlado."""
    with mock.patch.dict(os.environ, {**ENV_MINIMO, **extra}):
        for nome in VARIAVEIS:
            if nome not in extra:
                os.environ.pop(nome, None)
        prod = importlib.reload(importlib.import_module("config.settings.prod"))
        if modulo == "prod":
            return prod
        return importlib.reload(importlib.import_module("config.settings.staging"))


class SettingsDeployTests(SimpleTestCase):
    def test_prod_seguro_por_defeito(self):
        s = carregar("prod")
        self.assertTrue(s.SECURE_SSL_REDIRECT)
        self.assertTrue(s.SESSION_COOKIE_SECURE)
        self.assertTrue(s.CSRF_COOKIE_SECURE)
        self.assertFalse(s.DEBUG)

    def test_staging_desliga_ssl_por_defeito(self):
        s = carregar("staging")
        self.assertFalse(s.SECURE_SSL_REDIRECT)
        self.assertFalse(s.SESSION_COOKIE_SECURE)
        self.assertFalse(s.CSRF_COOKIE_SECURE)

    def test_staging_liga_ssl_por_variavel(self):
        s = carregar("staging", DJANGO_SECURE_SSL_REDIRECT="1")
        self.assertTrue(s.SECURE_SSL_REDIRECT)

    def test_hosts_e_csrf_por_env(self):
        s = carregar(
            "staging", DJANGO_CSRF_TRUSTED_ORIGINS="http://a.test,http://b.test"
        )
        self.assertEqual(s.ALLOWED_HOSTS, ["exemplo.test"])
        self.assertEqual(s.CSRF_TRUSTED_ORIGINS, ["http://a.test", "http://b.test"])

    def test_csrf_origens_vazio_por_defeito(self):
        self.assertEqual(carregar("prod").CSRF_TRUSTED_ORIGINS, [])

    def test_prod_sem_secret_key_falha(self):
        with mock.patch.dict(os.environ, {"DJANGO_ALLOWED_HOSTS": "x.test"}):
            os.environ.pop("DJANGO_SECRET_KEY", None)
            prod = importlib.import_module("config.settings.prod")
            with self.assertRaises(ImproperlyConfigured):
                importlib.reload(prod)

    def test_whitenoise_logo_apos_security_middleware(self):
        mw = carregar("prod").MIDDLEWARE
        i = mw.index("django.middleware.security.SecurityMiddleware")
        self.assertEqual(mw[i + 1], "whitenoise.middleware.WhiteNoiseMiddleware")

    def test_static_root_definido(self):
        self.assertEqual(carregar("prod").STATIC_ROOT.name, "staticfiles")

    def test_prod_hsts_por_defeito(self):
        s = carregar("prod")
        self.assertEqual(s.SECURE_HSTS_SECONDS, 31536000)
        self.assertFalse(s.SECURE_HSTS_INCLUDE_SUBDOMAINS)
        self.assertFalse(s.SECURE_HSTS_PRELOAD)

    def test_prod_hsts_por_env(self):
        s = carregar(
            "prod",
            DJANGO_SECURE_HSTS_SECONDS="600",
            DJANGO_SECURE_HSTS_INCLUDE_SUBDOMAINS="1",
            DJANGO_SECURE_HSTS_PRELOAD="1",
        )
        self.assertEqual(s.SECURE_HSTS_SECONDS, 600)
        self.assertTrue(s.SECURE_HSTS_INCLUDE_SUBDOMAINS)
        self.assertTrue(s.SECURE_HSTS_PRELOAD)

    def test_staging_hsts_a_zero_por_defeito(self):
        self.assertEqual(carregar("staging").SECURE_HSTS_SECONDS, 0)

    def test_staging_hsts_por_variavel(self):
        s = carregar("staging", DJANGO_SECURE_HSTS_SECONDS="300")
        self.assertEqual(s.SECURE_HSTS_SECONDS, 300)
