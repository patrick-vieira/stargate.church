# Motor imersivo (STAR-38)

Um post imersivo é feito de **atos** guardados em dados (`core.PostImersivo` e `core.Ato`). O autor escolhe o efeito numa lista no admin; nunca escreve JS. Rota: `/imersivo/<slug>/` (`core:imersivo`), 404 se o post não estiver publicado.

## Como funciona
- O template `core/templates/core/imersivo.html` renderiza cada ato como `<article class="im-ato" data-ato data-efeito data-parametros data-reduzido>` com `h2` e `p`. As camadas do parallax, as formas, o diagrama e os canvas são markup inline (formas geométricas; nenhuma imagem).
- `static/js/imersivo/motor.js` (módulo ES) percorre os `[data-ato]` e, quando o ato chega perto do viewport (`IntersectionObserver`, `rootMargin: 100% 0px`), importa `efeitos/<efeito com : trocado por ->.js` e chama a função registada com `{ el, parametros, reduzido, libs, progresso(cb) }`. `progresso(cb)` chama `cb(0..1)` a cada scroll (via `requestAnimationFrame`).
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

## GSAP + ScrollTrigger e Lenis: PENDENTE
Vendorização barrada por falta de rede. Colocar em `static/lab/vendor/` (`gsap.min.js`, `lenis.mjs`) com a licença ao lado e citar versão + licença aqui. Enquanto não existirem, o motor não os pede (o servidor só os indica se os ficheiros existirem, ver `core/imersivo.py`) e usa o fallback nativo (`scroll` + `requestAnimationFrame` + `IntersectionObserver`), sem erro de consola.
