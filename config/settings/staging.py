from .prod import *  # noqa: F403
from .prod import env

# Staging corre em http na LAN, atrás do proxy: SSL e cookies seguros desligados.
SECURE_SSL_REDIRECT = env.bool("DJANGO_SECURE_SSL_REDIRECT", default=False)
SESSION_COOKIE_SECURE = env.bool("DJANGO_SESSION_COOKIE_SECURE", default=False)
CSRF_COOKIE_SECURE = env.bool("DJANGO_CSRF_COOKIE_SECURE", default=False)
# HSTS seco em http: o browser ignoraria o cabeçalho e ficaria uma falsa garantia.
SECURE_HSTS_SECONDS = env.int("DJANGO_SECURE_HSTS_SECONDS", default=0)
