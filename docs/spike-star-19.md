# Spike STAR-19 — WebGL, Rive e scroll no Django

Estado: **código completo; medições por correr (script pronto); GPT Astra fora deste card** (cota Codex, decisão do líder; vai para outro card).

## O que está feito
- Rota `/lab/spike/` (`core:lab_spike`), template `core/templates/core/lab_spike.html`, script `static/js/lab-spike.js`.
- Tudo **vendorizado, sem CDN**, em `static/lab/vendor/`: `three-0.160.0.module.js` (import map local) e Rive **2.35.0** (`rive-canvas-2.35.0.js` + `rive-2.35.0.wasm`, de `@rive-app/canvas@2.35.0`).
- Diagrama SVG que se constrói com o progresso do scroll (sem JS aparece completo).
- Modo `prefers-reduced-motion`: sem rotação nem autoplay do Rive; diagrama completo e cena estática.

## Rive: porquê a 2.35.0
O `.riv` (`static/lab/rive/stargate-leitura.riv`, fonte em `scripts/spike/stargate-leitura.scene.rml`) usa **ViewModel** (`Reading`, propriedade numérica `progressoLeitura`, 0–100, convertida em largura da barra). O runtime 2.21.6 não traz a API de ViewModel; a 2.35.0 traz. As 2.21.6 não entram no repo.

Ligação (em `lab-spike.js`): `new rive.Rive({ src, canvas, autoBind: true })`; no `onLoad`, `r.viewModelInstance.number('progressoLeitura').value = progresso * 100`. O `.js` é UMD (carregado por `<script>`, expõe `window.rive`); o `.wasm` é indicado com `rive.RuntimeLoader.setWasmUrl(...)`. Não há state machine com inputs: o scroll só escreve o número do ViewModel.

**Por confirmar no browser:** a ligação do ViewModel com a 2.35.0 só se prova a correr `scripts/spike/medir-lab-spike.js` (o texto `#lab-modo` diz «Rive: ok (ViewModel ligado)» ou o erro cru, e `window.__labEstado` expõe o resultado). Esta cadeira não tem browser.

## Medições (por correr; sem números inventados)
```
python manage.py runserver 127.0.0.1:<porta livre>   # nunca 8170
node scripts/spike/medir-lab-spike.js http://127.0.0.1:<porta> <pasta-de-prints>
```
O script (Playwright, Chromium) mede e imprime JSON:
- **Peso** total e por tipo/URL, sem compressão (o runserver não comprime; o gzip real depende do proxy de produção).
- **FPS** a rolar a página de ponta a ponta em 4 s (rAF: fps médio, p95 e pior frame). Com `--use-gl=swiftshader` o GL é por software: é um piso, não o número do portátil; repetir com GPU.
- **390 px**: `scrollWidth <= innerWidth` (sem scroll horizontal) e prints.
- **Movimento reduzido**: sessão com `reducedMotion: reduce`, texto do modo e prints.
- Erros de página/consola.

Resultados: **por preencher** pelo Hokage depois de correr o script.

## Modo reduzido (`prefers-reduced-motion`)
Cena 3D desenhada uma vez numa pose fixa; Rive sem autoplay; diagrama completo sem transição; nenhum efeito depende do scroll para ser lido.

## Modelo de conteúdo dos «actos»
Um post descreve atos em dados (sem JS para o autor). Cada ato = texto + efeito:

| campo | exemplo | significado |
|---|---|---|
| `titulo` | «O diagrama se constrói» | título do ato |
| `texto` | texto curto | corpo do ato |
| `efeito` | `three:gira` · `rive:estado` · `diagrama:constroi` | escolhido numa lista no admin |
| `parametros` | `{"estado": "aberto"}` | opcional, validado por efeito |
| `reduzido` | `estatico` · `omitir` | alternativa com movimento reduzido |

Na página de prova o ato é o `<article data-ato data-efeito="…">`; o modelo futuro (STAR-17) renderiza esses atributos a partir dos dados. Um efeito novo = um registo novo em `lab-spike.js`, nunca código do autor.

## Fora deste card
GPT Astra no Codex (`codex exec -m …`), 3 variantes de UI, custo e tempo em `vigia/fontes.jsonl`: outro card.
