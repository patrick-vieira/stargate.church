# Motor imersivo (STAR-38)

Um post imersivo é feito de **atos** guardados em dados (`core.PostImersivo` e `core.Ato`). O autor escolhe o efeito numa lista no admin; nunca escreve JS. Rota: `/imersivo/<slug>/` (`core:imersivo`), 404 se o post não estiver publicado.

## Como funciona
- O template `core/templates/core/imersivo.html` renderiza cada ato como `<article class="im-ato" data-ato data-efeito data-parametros data-reduzido>` com `h2` e `p`. As camadas do parallax, as formas, o diagrama e os canvas são markup inline (formas geométricas; nenhuma imagem).
- `static/js/imersivo/motor.js` (módulo ES) percorre os `[data-ato]` e, quando o ato chega perto do viewport (`IntersectionObserver`, `rootMargin: 100% 0px`; nos efeitos pesados `three:*` e `rive:*` é `0px`, para a lib só baixar quando o ato entra em vista), importa `efeitos/<efeito com : trocado por ->.js` e chama a função registada com `{ el, parametros, reduzido, libs, progresso(cb) }`. `progresso(cb)` chama `cb(0..1)` a cada scroll (via `requestAnimationFrame`).
- O estado fica em `window.__imersivoEstado = { atos: [{ efeito, ok, erro }], reduzido }` (usado por `scripts/spike/medir-imersivo.js`).
- Sem JS o texto fica legível; o diagrama e as formas aparecem completos (o CSS só os esconde com a classe `js`).

## Criar um efeito novo
1. **Registrar**: criar `static/js/imersivo/efeitos/<grupo>-<nome>.js` (ex.: `particulas-nuvem.js` para `particulas:nuvem`) com `registar("particulas:nuvem", (ctx) => { ... })`. Tratar `ctx.reduzido` primeiro: sem animação e sem libs pesadas.
2. **Choices**: acrescentar o valor em `Ato.Efeito` (`core/models.py`) e gerar a migration (`python manage.py makemigrations core`).
3. **Validação**: acrescentar o efeito em `PARAMETROS_POR_EFEITO` (chave, validador, descrição). Chave desconhecida dá `ValidationError`.
4. **Markup**: acrescentar o ramo `{% elif %}` no template com o HTML/SVG/canvas do efeito.
5. **Teste**: `core/tests/test_imersivo.py` (validação do efeito, render dos atributos) e, se mexer na UI, rodar `scripts/spike/medir-imersivo.js`.

## Régua de direitos
- Proibido: imagens, personagens, cartazes, fotogramas e logos de obras.
- Citações: 1 a 2 frases, sempre com fonte.
- Áudio: só original ou de licença livre (com a licença citada).
- Conteúdo de demonstração é inventado, neutro e marcado PROVISÓRIO (`core/fixtures/imersivo_demo.json`).

## Movimento reduzido (`prefers-reduced-motion`)
- Nenhum efeito anima; o estado estático fica legível. Three, Rive, wasm, GSAP e Lenis **não são carregados**.
- `reduzido = omitir` esconde o ato só nesse modo (CSS `.im-ato--omitir`); `estatico` mostra o ato em pose fixa.
- Transições do CSS e View Transitions ficam desligadas.

## Peso
- Meta: **peso inicial <= 1,5 MB** (sem compressão). Three (`three-0.160.0.module.js`), Rive (`rive-canvas-2.35.0.js`) e o wasm só são baixados quando o ato se aproxima do viewport; no 1.º carregamento não vêm.
- A 390 px não pode haver scroll horizontal (`min-width: 0`, `max-width: 100%`, `overflow-x: clip` no palco).
- Medir: `node scripts/spike/medir-imersivo.js http://127.0.0.1:<porta> <pasta-de-prints> [slug]` (porta livre, nunca 8170); falha se o peso inicial passar de 1,5 MB.

## View Transitions entre posts
`static/css/imersivo.css` traz `@view-transition { navigation: auto; }` dentro de `@supports (view-transition-name: none)`: navegadores sem suporte ignoram o bloco. Com `prefers-reduced-motion` as animações `::view-transition-*` são anuladas.

## Versões vendorizadas (em `static/lab/vendor/`)
| lib | versão | licença |
|---|---|---|
| three | 0.160.0 | MIT |
| Rive (`@rive-app/canvas`) | 2.35.0 | MIT |

## Sem GSAP: sticky + animation-timeline
Decisão do Patrick: o motor fica **sem GSAP e sem Lenis** (e sem rede). Ordem de preferência:
1. **CSS scroll-driven primeiro.** `parallax:camadas` e `scroll:revela` animam por CSS em `@supports (animation-timeline: view())` (keyframes `im-par` e `im-rev`, `animation-range`). A intensidade do parallax vai para `--im-int` no `<article>`. O JS (scroll + `requestAnimationFrame` + `IntersectionObserver`) só entra quando não há suporte (`cssScroll` em `motor.js`).
2. **Pin sem GSAP.** O parâmetro `fixar` (booleano, validado em `parallax:camadas`, `three:gira` e `rive:estado`) põe a classe `im-ato--fixo` no ato: `position: sticky` na `.im-cena` e o ato ganha altura (150vh). Sem JS.
3. Em `prefers-reduced-motion` nada anima e **não fixa** (a cena volta a `position: static`). A 390 px não há scroll horizontal (o palco mantém `overflow-x: clip`, que não quebra o sticky).

**Rive** é o motor de animação de primeira linha (pedido do Patrick): efeitos com estado e interação usam `rive:estado`; CSS cobre o scroll simples.

## GSAP + ScrollTrigger e Lenis: PENDENTES
Decisão: ficam fora por agora. Se um dia entrarem, vão para `static/lab/vendor/gsap-3.12.x/gsap.min.js` e `static/lab/vendor/lenis-1.x/lenis.mjs` (caminhos esperados em `core/imersivo.py`), com a licença ao lado e versão + licença citadas aqui. Enquanto não existirem, o motor não os pede (o servidor só os indica se os ficheiros existirem, ver `core/imersivo.py`) e usa o fallback nativo (`scroll` + `requestAnimationFrame` + `IntersectionObserver`), sem erro de consola.

## Atmosfera «Máquina fria» (`atmosfera:maquina-fria`, STAR-41)
Efeito de página inteira (protótipo aprovado no STAR-51). Se o post tiver um ato com este efeito, `core/views.py` renderiza o template próprio `core/templates/core/imersivo_maquina_fria.html` em vez do genérico.
- **Peças**: lâmpada que segue o cursor, console que escreve ao rolar (Console 7), corredor 3D (three) com camadas e medidor de risco. Tudo escopado em `.am-raiz`.
- **Ficheiros**: `static/js/imersivo/efeitos/atmosfera-maquina-fria.js`, `static/css/atmosfera-maquina-fria.css`, fixtures `core/fixtures/maquina_fria.json` (slug `a-maquina-fria`) e `maquina_fria_provisorio.json`.
- **Parâmetros**: nenhum (`PARAMETROS_POR_EFEITO["atmosfera:maquina-fria"] = {}`).
- **Fonte**: títulos em Fraunces 600 local (`static/fonts/fraunces/`), via `--serif: var(--sg-serif)`; nada vem de CDN.
- **three**: só baixa quando o corredor entra em vista; no 1.º carregamento não vem.
- **Movimento reduzido**: `reduzido` põe `.am-estatico` (sem poeira, sem grão animado, sem three); o botão «pausar movimento» pausa o resto.
- **Acessibilidade**: contraste AA medido no browser a 1920 e 390 px: 23 seletores de texto, 0 falhas; o mais baixo é `p.am-n` com 4,98:1 (mínimo 4,5). Terminal e corredor são `aria-hidden`; o texto do console vai num `.am-sr`.
- **Desempenho**: fps medido com WebGL por software (swiftshader); com a máquina carregada vale a paridade com o protótipo (ver o registo no STAR-41).
