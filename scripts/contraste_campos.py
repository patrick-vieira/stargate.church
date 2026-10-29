"""Razão de contraste (WCAG 1.4.11) da borda dos campos, antes e depois (STAR-29).

Uso: python scripts/contraste_campos.py [cor ...]
Sem argumentos lê --sg-campo-borda de static/css/tokens.css; com cores
(#RRGGBB) mede-as, para escolher o valor.
"""

import re
import sys
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[1]
FUNDOS = {"branco (cartão)": "#FFFFFF", "creme (--sg-creme)": "#FBF5EA"}
ANTES = "#E6DAC4"  # --sg-linha, a borda antiga


def luminancia(hex_cor: str) -> float:
    h = hex_cor.lstrip("#")
    canais = [int(h[i : i + 2], 16) / 255 for i in (0, 2, 4)]
    lin = [c / 12.92 if c <= 0.03928 else ((c + 0.055) / 1.055) ** 2.4 for c in canais]
    return 0.2126 * lin[0] + 0.7152 * lin[1] + 0.0722 * lin[2]


def razao(a: str, b: str) -> float:
    la, lb = sorted((luminancia(a), luminancia(b)), reverse=True)
    return (la + 0.05) / (lb + 0.05)


def token_atual() -> str:
    css = (RAIZ / "static/css/tokens.css").read_text(encoding="utf-8")
    return re.search(r"--sg-campo-borda:\s*(#[0-9A-Fa-f]{6})", css).group(1)


if __name__ == "__main__":
    depois = sys.argv[1:] or [token_atual()]
    for nome, fundo in FUNDOS.items():
        print(f"{nome}: antes {ANTES} {razao(ANTES, fundo):.2f}:1")
        for cor in depois:
            print(f"{nome}: depois {cor} {razao(cor, fundo):.2f}:1")
