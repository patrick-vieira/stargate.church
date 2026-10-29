"""Prints antes/depois dos campos de formulário a 1920 e 390 px (STAR-29).

Uso: python scripts/prova_campos.py <pasta-de-saída>
"Antes" = CSS de origin/main; "depois" = CSS do ramo. Página estática com o
mesmo markup do cartão de conta e da newsletter; sem servidor, sem porta.
"""

import subprocess
import sys
from pathlib import Path

from playwright.sync_api import sync_playwright

RAIZ = Path(__file__).resolve().parents[1]
CSS = ("static/css/tokens.css", "static/css/stargate.css")
HTML = """<!doctype html><html lang="pt"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<style>{css}</style></head>
<body><main><section class="sg-sec"><div class="sg-wrap">
<div class="sg-cartao-conta">
<span class="sg-sobrolho">Conta do leitor</span><h1>Entrar</h1>
<form class="sg-form sg-form--conta"><label>E-mail
<input type="email" value="leitor@exemplo.com"></label><label>Senha
<input type="password" value="segredo12"></label>
<button class="sg-btn sg-btn--coral" type="button">Entrar</button>
</form></div></div></section>
<section class="sg-sec"><div class="sg-wrap"><div class="sg-news">
<div><h2>Newsletter</h2></div>
<div><form class="sg-form">
<input type="email" placeholder="seu@email.com" aria-label="E-mail">
<button class="sg-btn sg-btn--coral" type="button">Quero receber</button>
</form></div></div></div></section>
</main></body></html>"""


def css_antes() -> str:
    return "".join(
        subprocess.run(
            ["git", "-C", str(RAIZ), "show", f"origin/main:{f}"],
            capture_output=True,
            text=True,
            check=True,
        ).stdout
        for f in CSS
    )


def css_depois() -> str:
    return "".join((RAIZ / f).read_text(encoding="utf-8") for f in CSS)


def main(saida: Path) -> None:
    saida.mkdir(parents=True, exist_ok=True)
    versoes = {"antes": css_antes(), "depois": css_depois()}
    with sync_playwright() as p:
        browser = p.chromium.launch()
        for largura, altura in ((1920, 1000), (390, 900)):
            for nome, css in versoes.items():
                css = css.replace("@import url(", "/*@import url(", 1).replace(
                    ");", ");*/", 1
                )
                page = browser.new_page(viewport={"width": largura, "height": altura})
                page.set_content(HTML.format(css=css))
                destino = saida / f"{nome}-{largura}.png"
                page.screenshot(path=str(destino), full_page=True)
                page.close()
                print(destino)
        browser.close()


if __name__ == "__main__":
    main(Path(sys.argv[1]))
