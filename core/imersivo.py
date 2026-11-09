"""Apoio ao motor imersivo: detecta libs opcionais vendorizadas (GSAP, Lenis)."""

import json

from django.contrib.staticfiles import finders
from django.templatetags.static import static

LIBS_OPCIONAIS = {
    "gsap": "lab/vendor/gsap-3.12.x/gsap.min.js",
    "lenis": "lab/vendor/lenis-1.x/lenis.mjs",
}


def libs_opcionais():
    """JSON nome -> url ou null; só aponta para o que existe, sem 404 na consola."""
    achadas = {
        nome: (static(caminho) if finders.find(caminho) else None)
        for nome, caminho in LIBS_OPCIONAIS.items()
    }
    return json.dumps(achadas)
