# Spike STAR-19 — WebGL, Rive e scroll no Django

Estado: **parcial — faltam medições e o GPT Astra.**

## O que está feito
- Rota `/lab/spike/` (`core:lab_spike`), template `core/templates/core/lab_spike.html`, script `static/js/lab-spike.js`.
- `three@0.160.0` e `@rive-app/canvas@2.21.6` por CDN (jsDelivr), versão fixa atrás de import map.
- Diagrama SVG que se constrói com o progresso do scroll (sem JS aparece completo).
- Modo `prefers-reduced-motion`: sem rotação nem autoplay do Rive; diagrama completo e cena estática.

## Ponto de ligação do Rive
O `.riv` **não foi inventado**. Caminho esperado: `static/lab/exemplo.riv`, com a state machine `Scroll` e um input numérico `progresso` (0–100). Sem o ficheiro, o Rive falha com graça e a página mostra o estado do carregamento.

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

## Por medir (sem números inventados)
- Peso gzip (HTML, JS próprio, three, Rive): **por medir**.
- FPS num portátil: **por medir**.
- Comportamento a 390 px (sem scroll horizontal): **por medir**.
- GPT Astra no Codex (`codex exec -m …`), 3 variantes de UI vs. protótipo do Hagoromo, custo e tempo em `vigia/fontes.jsonl`: **por medir**.

Motivo: exige rede, browser e codex, que a cadeira do executor não tem. As versões das bibliotecas também não foram confirmadas contra o registo npm.
