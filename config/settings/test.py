from .base import *  # noqa: F403

SECRET_KEY = "chave-fictícia-de-teste"
DEBUG = False
ALLOWED_HOSTS = ["testserver", "localhost"]

# Os testes correm sempre em SQLite, em memória.
DATABASES = {"default": {"ENGINE": "django.db.backends.sqlite3", "NAME": ":memory:"}}

TEST_RUNNER = "config.test_runner.RaizDiscoverRunner"

PASSWORD_HASHERS = ["django.contrib.auth.hashers.MD5PasswordHasher"]
