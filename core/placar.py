"""Dados do placar (STAR-48): uma só fonte, core/dados/placar.json.

O JSON alimenta a tabela e o json_script da página do post 8 e a prévia do hub.
As notas editoriais vão de 0 a 5; a prévia do hub usa a escala 0..100.
"""

import json
from functools import lru_cache
from pathlib import Path

CAMINHO = Path(__file__).resolve().parent / "dados" / "placar.json"

# Mídias do JSON → grupo de cor e forma do gráfico (cor + forma, nunca só cor).
GRUPOS = {
    "filme": "filme",
    "TV": "tv",
    "jogo": "jogo",
    "peça": "pag",
    "contos": "pag",
    "romance": "pag",
    "mangá": "pag",
}


@lru_cache(maxsize=1)
def _carregar():
    with CAMINHO.open(encoding="utf-8") as f:
        return tuple({**o, "grupo": GRUPOS[o["midia"]]} for o in json.load(f))


def obras():
    """As 30 obras, na ordem do ficheiro (cópias: o chamador pode alterá-las)."""
    return [dict(o) for o in _carregar()]


def obra(id_):
    for o in _carregar():
        if o["id"] == id_:
            return dict(o)
    return None


def ids():
    return {o["id"] for o in _carregar()}


def ponto_previa(id_):
    """Ponto {obra, x, y} (0..100) da prévia do hub para uma obra do placar."""
    o = obra(id_)
    if o is None:
        return None
    return {
        "obra": o["titulo"],
        "x": round(o["proximidade"] / 5 * 100),
        "y": round(o["preocupacao"] / 5 * 100),
    }


def medias():
    """Média real dos leitores por obra: {id: {proximidade, preocupacao, n}} (n ≥ 1)."""
    from django.db.models import Avg, Count

    from .models import VotoPlacar

    linhas = VotoPlacar.objects.values("obra").annotate(
        p=Avg("proximidade"), c=Avg("preocupacao"), n=Count("pk")
    )
    return {
        linha["obra"]: {
            "proximidade": round(float(linha["p"]), 2),
            "preocupacao": round(float(linha["c"]), 2),
            "n": linha["n"],
        }
        for linha in linhas
        if linha["obra"] in ids()
    }


def media_da_obra(id_):
    """Média e contagem de uma obra; n = 0 (e médias None) se ninguém votou."""
    from django.db.models import Avg, Count

    from .models import VotoPlacar

    r = VotoPlacar.objects.filter(obra=id_).aggregate(
        p=Avg("proximidade"), c=Avg("preocupacao"), n=Count("pk")
    )
    if not r["n"]:
        return {"proximidade": None, "preocupacao": None, "n": 0}
    return {
        "proximidade": round(float(r["p"]), 2),
        "preocupacao": round(float(r["c"]), 2),
        "n": r["n"],
    }
