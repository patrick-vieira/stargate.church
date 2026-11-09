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

## Efeito `linha-tempo:decadas` (STAR-40, hub «Do Golem ao ChatGPT»)
- Parâmetros: `intensidade` (0–1) e `estacoes`, lista não vazia de `{decada: 1920..2020, titulo, slug?, texto?}` (validador `_estacoes`; décadas em ordem cronológica, não precisam ser únicas).
- Markup: `<ol class="im-linha">` dentro de `.im-trilho` (`tabindex=0`, `role=region`, `aria-label`). Cada `li.im-estacao[data-decada]` traz camadas SVG geométricas (papel, válvulas, fósforo, pixels, vidro, conforme a época; `Ato.estacoes` calcula a forma). O título só vira link `core:imersivo` se o slug estiver em `publicados` (contexto da view).
- CSS/JS: sem JS ou com movimento reduzido a lista é vertical e cronológica. Com JS, trilho horizontal com `scroll-snap`, parallax por variável `--d` (scroll do trilho + progresso vertical da página) e classe `.on` na estação visível (`IntersectionObserver`). Sem GSAP/Lenis, Three ou Rive.
- STAR-64 (retoques): a luz (`data-luz`) segue a estação mais próxima de um ponto que vai da borda esquerda (scroll 0) à direita (fim do trilho), por isso a 1920 aparecem sépia, âmbar, verde, magenta e azul. «Pausar movimento» vive no fluxo do palco, nunca sobre a navbar. A lista (reduzido/sem JS) é grelha de 2–3 colunas. Estações sem destino levam `.im-estacao--breve` e o rótulo «em breve»; ganham link quando o episódio é publicado. `Ato.estacoes` devolve `forma` (papel, válvulas, transistor, fósforo, pixels, vidro, rede) e `variante` (posição na década) para arte distinta por estação. O h1 do hub usa `.im-titulo-hub` (Fraunces 600) e o sobrolho «Série · N posts · 1920 → 2026».
- Fixture do hub: `core/fixtures/imersivo_hub.json` (`ia-na-ficcao`; textos originais, sem imagens de obras).

## Efeitos `filtro:chips` e `grelha:posts` (STAR-63, atos 2 e 3 do hub)
- `filtro:chips`: `parametros.perguntas`, lista de 1 a 8 `{id, rotulo, slugs: [slugs de estações]}` (validador `_perguntas`; ids únicos). Cada pergunta vira um `<button class="im-chip" aria-pressed>`. O JS (`efeitos/filtro-chips.js`) atenua com `.im-estacao--fora` (opacity .35, sem esconder) as `.im-estacao[data-slug]` da página cujo slug não casa (estação sem slug fica atenuada com filtro activo); clicar no chip activo limpa. A contagem «N estações» vai num `aria-live="polite"`. Sem JS os chips ficam como lista de perguntas; com movimento reduzido o filtro é o mesmo, sem transição. Cada `li.im-estacao` do trilho leva `data-slug` (vazio se não houver).
- `grelha:posts`: `parametros.previa`, lista de 1 a 6 `{obra, x, y}` (0–100; `Ato.previa_pontos` converte para coordenadas do SVG). Mostra a prévia estática do placar em SVG (`role=img` + `<title>`), a grelha dos episódios da série (a view junta `ato.episodios_serie` = `{numero, titulo, slug, url|None}`, sem o número 0; os não publicados levam «em breve» e nenhum `<a>`; funciona com N itens) e «Começar pelo post 1 →» (`ato.comecar_url`, com `view-transition-name`). Com movimento reduzido aparecem duas `<table>` equivalentes (posts e pontos da prévia); fora dele ficam só para leitores de ecrã.
- View Transitions (`@view-transition`) só dentro de `prefers-reduced-motion: no-preference`.

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

### Narrador Rive (`rive:narrador`, STAR-38)

Glifo comum a **todos os posts imersivos** (`core/_narrador.html`, incluído nos 6 templates). Runtime Rive 2.35.0 vendorizado em `static/lab/vendor/` (nada de CDN) e `static/rive/narrador.riv` (fonte STAR-37, ViewModel `Narrador`: `progresso` 0–100, `era` 0–6, `humor` 0–2, `cor`).

- `static/js/imersivo/efeitos/rive-narrador.js` liga `progresso` ao scroll da página (`progressoPagina(cb)` no contexto do motor) e põe a `era` vinda de `data-parametros`; a `cor` sai da tabela de eras.
- Era por post: tabela `ERA_NARRADOR` em `core/views.py` (slug → era); fora da tabela vale 6. Post novo = uma linha na tabela.
- Reduced-motion: não carrega runtime nem wasm; fica o glifo SVG estático com a pele da era. A 390 px o glifo tem 48 px, no canto, sem capturar toques; é decorativo (`aria-hidden`).

## GSAP + ScrollTrigger e Lenis: PENDENTES
Decisão: ficam fora por agora. Se um dia entrarem, vão para `static/lab/vendor/gsap-3.12.x/gsap.min.js` e `static/lab/vendor/lenis-1.x/lenis.mjs` (caminhos esperados em `core/imersivo.py`), com a licença ao lado e versão + licença citadas aqui. Enquanto não existirem, o motor não os pede (o servidor só os indica se os ficheiros existirem, ver `core/imersivo.py`) e usa o fallback nativo (`scroll` + `requestAnimationFrame` + `IntersectionObserver`), sem erro de consola.

## Atmosfera «A IA afetiva» (`atmosfera:ia-afetiva`, STAR-44)
Efeito de página inteira (protótipo aprovado no STAR-51, revisão 5). Se o post tiver um ato com este efeito, `core/views.py` renderiza o template próprio `core/templates/core/imersivo_ia_afetiva.html` em vez do genérico.
- **Peças**: cidade ao entardecer (prédios gerados em JS, janela que acende com o scroll), conversa que se escreve ao rolar (a 1.ª bolha já vem inteira), cartões «é possível» / «é aceitável?» em cascata, escolha de limites com tabela ficção × 2026. Tudo escopado em `.aa-raiz`.
- **Ficheiros**: `static/js/imersivo/efeitos/atmosfera-ia-afetiva.js`, `static/css/atmosfera-ia-afetiva.css`, fixture `core/fixtures/ia_afetiva.json` (slug `a-ia-afetiva`).
- **Parâmetros**: nenhum (`PARAMETROS_POR_EFEITO["atmosfera:ia-afetiva"] = {}`).
- **Fonte**: títulos em Fraunces 600 local (`static/fonts/fraunces/`), via `--serif: var(--sg-serif)`; nada vem de CDN.
- **Imagens e libs**: nenhuma. A cidade e a janela são CSS; sem three, sem rede (1.º carregamento = HTML + 1 CSS + 2 JS + a fonte).
- **Movimento reduzido**: `reduzido` põe `.aa-estatico` (sem respiração da janela, sem cursor a piscar, diálogo completo e cartões visíveis); o botão «pausar movimento» pausa o resto.
- **Áudio**: desligado; o «som (em breve)» é uma caixa desactivada.
- **Medições (browser)**: ver o registo da entrega no STAR-44 (fps com «load» anotado, contraste AA, 390 px sem scroll horizontal).

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

## Atmosfera «Guerra das máquinas» (`atmosfera:guerra-maquinas`, STAR-42)
Post 2 da série. Mesmo padrão do STAR-41: um ato com este efeito faz `core/views.py` renderizar `core/templates/core/imersivo_guerra_maquinas.html` (mapa `TEMPLATES_ATMOSFERA`, uma entrada por atmosfera). Tudo escopado em `.ag-raiz` e com o prefixo `.ag-` (ids incluídos).
- **Peças**: HUD vermelho com contagem 10→0 que o leitor pode parar; glitch RGB, scanlines, vinheta e faixa de interferência que crescem com o scroll (variável CSS `--g`, de 0 a 1 e de volta a 0); mosaico 14×8 que se parte em pixels e se recompõe; 3 sinais de supervisão (`<details>`, um aberto de cada vez); formulário «Registro de supervisão» cujo botão «Interromper o sistema» baixa de facto o alarme (`--g` → 0) até alguém rearmar.
- **Ficheiros**: `static/js/imersivo/efeitos/atmosfera-guerra-maquinas.js`, `static/css/atmosfera-guerra-maquinas.css`, fixture `core/fixtures/guerra_maquinas.json` (slug `o-medo-da-guerra-das-maquinas`, post pk 4, ato pk 15), migration `core/0004`.
- **Parâmetros**: nenhum (`PARAMETROS_POR_EFEITO["atmosfera:guerra-maquinas"] = {}`).
- **Sem biblioteca própria**: o efeito da atmosfera não usa three nem Rive; é CSS + JS próprio. O único Rive da página é o narrador (`rive:narrador`), carregado à parte.
- **Imagens**: `static/img/guerra-maquinas/fundo-1920.webp` (≈66 KB) e `fundo-780.webp` (≈56 KB, só no mobile), ambas ≤ 70 KB. Arte original (Yamato) de paisagem noturna abstrata: sem personagens, cartazes, fotogramas ou logos, sem código verde. Servem de fundo da camada `.ag-arte`, com `mix-blend-mode: screen` a 50 %.
- **Barra de baixo**: o cabeçalho do site ocupa o topo, por isso a barra do protótipo (ligação à série, intensidade e «pausar movimento») fica fixa em baixo. A 390 px a ligação lê «Ficção · 2», numa linha só.
- **Cenas fixas**: as cenas `sticky` começam abaixo do cabeçalho do site (76 px; 66 px no mobile); o progresso do ato desconta esse deslocamento.
- **Movimento reduzido**: `reduzido` põe `.ag-estatico` (atos empilhados, contagem parada em 04, intensidade fixa em 15 %, mosaico em duas imagens lado a lado, sem glitch); o botão «pausar movimento» pausa o resto.
- **Retoques da REVISAO-5**: (1) atos mais curtos (190vh e 200vh; 170vh e 180vh a 390 px) e hero mais baixo, para não haver ecrãs sem texto; (3) a linha mono do hero tem entrelinha de 1,6 e, a 390 px, uma indicação por linha; (4) o sobrolho do hero e a ligação da série não se partem (`white-space: nowrap`).
- **Direitos**: HUD, mosaico e alarme são desenhos originais; nenhuma citação literal; fontes (AFI, NIST, Warner Bros.) no fim do post.

## Atmosfera «O que é ser humano?» (`atmosfera:ser-humano`, STAR-43)
Post 3 da série. Mesmo padrão: `TEMPLATES_ATMOSFERA` aponta para `core/templates/core/imersivo_ser_humano.html`. Tudo escopado em `.sh-raiz` com o prefixo `.sh-` (ids incluídos).
- **Peças**: sala de vidro (arte de fundo, 3 painéis e 2 silhuetas em parallax), reflexo que segue o cursor, brilho especular nos cartões `.sh-vidro` e teste original de 3 perguntas. As respostas (maioria; empate ou nenhuma = «não sei») põem `.sh-tom-<tom>` na raiz, reordenam os 3 cartões do ato 2 e escolhem o final do ato 3. Nada é guardado nem enviado. As perguntas são rascunho do Orochimaru (caixa-hokage#4253) e ficam como estão.
- **Ficheiros**: `static/js/imersivo/efeitos/atmosfera-ser-humano.js`, `static/css/atmosfera-ser-humano.css`, fixture `core/fixtures/ser_humano.json` (slug `o-que-e-ser-humano`, post pk 5, ato pk 16), migration `core/0006`.
- **Parâmetros**: nenhum (`PARAMETROS_POR_EFEITO["atmosfera:ser-humano"] = {}`). Sem biblioteca: nada de three nem Rive.
- **Ligação da série**: a «próxima estação» do post 2 é agora uma ligação para este post; a deste post (post 4) é texto até o post 4 existir.
- **Imagens**: `static/img/ser-humano/fundo-1920.webp` (≈35 KB) e `fundo-780.webp` (≈31 KB, só no mobile). Só fundos (sala de vidro, sem «personagem»); as figuras difusas das imagens-chave foram apagadas com desfoque. Camada `.sh-arte`, `mix-blend-mode: screen` a 38 %. 1.º carregamento medido: 130–175 KB.
- **Barra de baixo**: igual ao post 2 (o cabeçalho do site ocupa o topo); a 390 px a ligação lê «Ficção · 3».
- **Movimento reduzido**: `reduzido` põe `.sh-estatico` (sem reflexo nem transições, ordem fixa em «confiar», os 3 finais visíveis como texto); o botão «pausar movimento» pausa o resto.
- **Retoques da REVISAO-5 (3)**: a linha mono do hero tem entrelinha de 1,6 e, a 390 px, uma indicação por linha. O sobrolho do hero só quebra a 390 px (não cabe numa linha com este texto).
- **Acessibilidade medida no browser** (Playwright, `_provas/star43.py`): 24–25 seletores de texto a 1920 e a 390 px, 0 falhas; o mais baixo é `.sh-chip` com 5,67:1. Sem scroll horizontal a 390 px.
- **Desempenho**: fps em Chromium headless sem GPU, com o teste e o scroll a correr: média 40–42, p5 ≈ 30 (`backdrop-filter` por software); o protótipo marcava ≈ 59 com GPU. Se a média cair, a classe `.sh-sem-blur` tira o desfoque sozinha.
- **Direitos**: o teste é original e não copia o Voight-Kampff; sala, painéis e silhuetas genéricos; fontes (AFI, A24, HBO, NIST) no fim do post.
## Atmosfera «Leis, robôs e livros» (`atmosfera:leis-robos-livros`, STAR-45)
Post 5 da série. `TEMPLATES_ATMOSFERA` aponta para `core/templates/core/imersivo_leis_robos_livros.html`. Tudo escopado em `.lr-raiz` com o prefixo `.lr-` (ids incluídos).
- **Peças**: mesa de papel com lâmpada âmbar que segue o cursor e acende as «folhas»; livro aberto cuja página vira em 3D ao rolar (CSS 3D, `.lr-palco-sticky` de 560 vh, 2 folhas, 6 faces); tipos móveis «r o b ô» que se alinham; 3 regras que se riscam e se reescrevem; mapa de rede original (14 nós, 3 grandes); oficina «Escreva uma regra e confira o que falta» (conferência só no cliente).
- **Ficheiros**: `static/js/imersivo/efeitos/atmosfera-leis-robos-livros.js`, `static/css/atmosfera-leis-robos-livros.css`, fixture `core/fixtures/leis_robos_livros.json` (slug `leis-robos-e-livros`, post pk 7, ato pk 18), migration `core/0011_alter_ato_efeito`.
- **Parâmetros**: nenhum (`PARAMETROS_POR_EFEITO["atmosfera:leis-robos-livros"] = {}`); as faixas de scroll são constantes no JS (tipos 0,08–0,28; 1.ª virada 0,30–0,40; regras 0,42–0,72; 2.ª virada 0,74–0,84; rede 0,84–0,99). Sem biblioteca, sem imagens.
- **Sticky**: `top:76px` (cabeçalho do site); o progresso do livro vem de `.lr-pista` descontando esses 76 px. Barra de baixo «A IA na ficção · 5» (390 px: «Post 5», fundo opaco). Raiz com `overflow-x:clip`, nunca `hidden` no body.
- **Modo linear** (`.lr-linear`: 390, tablet ≤ 899 px e movimento reduzido): o livro vira 6 cartões em coluna, sem 3D nem sticky.
- **Movimento reduzido**: `.lr-estatico` + linear; estado final (`alinha(1); reescreve(1); desenhaRede(1)`), lâmpada parada, sem loop. `linearAtualiza()` e `livroAtualiza()` começam por `if (reduzido) { …(1); return; }` para o scroll e o resize não desfazerem o estado final (retoque 1 da revisão 7). O botão «pausar movimento» pausa o resto.
- **Direitos**: nunca o texto das Três Leis; as 3 regras são originais da série, com o selo «Regras desta série · não as leis do livro»; sem capas nem imagens de obras. As regras, a oficina e os textos são rascunho a rever pelo Orochimaru.

## Atmosfera «Escolhas da máquina» (`atmosfera:escolhas`, STAR-46)
Post 6 da série. `TEMPLATES_ATMOSFERA` aponta para `core/templates/core/imersivo_escolhas.html`. Tudo escopado em `.em-raiz` com o prefixo `.em-`.
- **Peças**: paisagem azul-noite (arte + névoa em 2 camadas com parallax), dois caminhos que se prolongam ao rolar, trilhas de dados cuja velocidade segue o scroll, escolha 1 (A/B), escolha 2 dependente da 1.ª, 4 finais (A1, A2, B1, B2) todos abríveis, árvore dos finais e contador «N de 4 finais vistos».
- **Estado**: `{a, b, seen}` só no cliente. `localStorage` (chave `star46.p6`) apenas se a caixa «Guardar meu caminho neste aparelho» estiver marcada, sempre em `try/catch`; «Limpar caminho» apaga. Sem modelo novo, sem gravar no servidor, sem rede.
- **Só teclado**: botões, caixa e lista são nativos; foco âmbar de 3 px. A lista «Abrir um final» é a alternativa ao nó 2.
- **Ficheiros**: `static/js/imersivo/efeitos/atmosfera-escolhas.js`, `static/css/atmosfera-escolhas.css`, fixture `core/fixtures/escolhas.json` (slug `escolhas-da-maquina`, post pk 6, ato pk 17), migration `core/0005`.
- **Parâmetros**: nenhum (`PARAMETROS_POR_EFEITO["atmosfera:escolhas"] = {}`). Sem biblioteca.
- **Imagens**: `static/img/escolhas/fundo-1920.webp` (≈60 KB) e `fundo-780.webp` (≈42 KB, só no mobile), dos fundos OpenAI 16x9 e 9x16. Sem personagens, sem andróide, sem HUD.
- **Versão linear** (390, movimento reduzido ou a pedido): `.em-linear` mostra as duas consequências e os 4 finais como texto, sem pulso nem parallax; o botão «Ver versão interativa» alterna.
- **Medido no browser** (Playwright, `_provas/star46.py`): contraste AA 0 falhas (mínimo 6,96:1), 390 sem scroll horizontal, 1.º carregamento 153–205 KB, 59,8 fps em Chromium headless.
- **Direitos**: nós, trilhas e finais são originais; nenhuma interface, personagem ou fala de jogo. Textos de consequência e finais são rascunho editorial a afinar pelo Orochimaru.

## Atmosfera «O placar» (`atmosfera:placar`, STAR-48)
Post 8 da série, a única página clara. `TEMPLATES_ATMOSFERA` aponta para `core/templates/core/imersivo_placar.html`; era do narrador 6. Tudo escopado em `.pl-raiz` com o prefixo `.pl-` (ids `pl-*`).
- **Peças**: hero escuro que «sobe» ao papel (`--sol`), gráfico de dispersão SVG (proximidade × preocupação, 30 obras, 4 mídias com cor e forma), obras que entram por década ao rolar o ato 1, destaques por fase no ato 2, filtros por mídia e década, ficha de cada ponto, tabela equivalente ordenável e o voto do leitor (ato 3). Sem imagens.
- **Dados, uma só fonte**: `core/dados/placar.json` (id, titulo, ano, midia, proximidade, preocupacao, justificativa; ids reais, ex. `be-right-back-2013`), carregado por `core/placar.py`. Não há campo `fontes`: nenhuma ligação foi inventada. A view entrega `placar` (tabela, renderizada no servidor, 30 linhas sem JS) e `placar_dados` (`{{ placar_dados|json_script:"pl-dados" }}`: obras, médias, votos do próprio leitor, `logado`, `voto_url`). O JS lê o `json_script`, sem pedir ficheiros.
- **Prévia do hub, os mesmos dados**: em `grelha:posts`, cada ponto de `previa` pode ser `{"id": "<id do placar>"}`; `Ato.previa_pontos` resolve título e posição (`x = proximidade/5·100`, `y = preocupacao/5·100`) com `core/placar.py`, e o validador recusa ids desconhecidos. O formato antigo `{obra, x, y}` continua aceito. A fixture `imersivo_hub.json` usa três ids reais.
- **Voto do leitor**: modelo `core.VotoPlacar` (utilizador, obra, proximidade e preocupação 0..5, `atualizado_em`; único por utilizador e obra). `POST /placar/voto/` (`core:placar_voto`), CSRF normal (cookie garantido pela view da página, token no cabeçalho `X-CSRFToken`), corpo JSON ou formulário `{obra, proximidade, preocupacao}`. Reaproveita o tecto diário: `UsoDiario.VOTO`, `leitores.tecto.limite("voto")`, `STARGATE_TECTO_VOTO` (30 por omissão), `exige_tecto("voto")`. Respostas: anónimo 401, tecto esgotado 429, obra desconhecida ou nota fora de 0..5 dá 400 e **não gasta o tecto** (a validação vem antes), repetição na mesma obra atualiza a linha existente (também gasta 1 do tecto). A resposta é JSON com a média do leitor-coletivo da obra (`proximidade`, `preocupacao`, `n`).
- **Camada «leitores»**: médias reais (obras com n ≥ 1), não simuladas. Aviso honesto na página: amostra de n votos, pequena e autosselecionada, não é pesquisa científica, só notas (sem texto livre nem dados pessoais). O anónimo vê as médias e um convite para entrar (`leitores:entrar`).
- **JS** (`static/js/imersivo/efeitos/atmosfera-placar.js`): a única chamada de rede é o `fetch` do voto; o teste do padrão que proíbe `fetch(` é adaptado só para este ficheiro (uma chamada, para `DADOS.voto_url`). Continuam proibidos `http`, `import(` e `XMLHttpRequest`. Escape e cliques escopados à raiz. «Pausar movimento» mostra tudo (mesmo estado do movimento reduzido: 30 pontos, destaques, tabela).
- **Movimento reduzido**: `.pl-estatico`, `--sol: 1`, sem transições, tabela visível e legível (também por CSS, sem JS). A 390: gráfico fora do sticky, ordem b1, gráfico, b2, b3; sem entrada por década.
- **Ficheiros**: `static/css/atmosfera-placar.css`, fixture `core/fixtures/placar_post.json` (slug `o-placar`, post pk 9, ato pk 20) e episódio 9 de `serie_ia_na_ficcao.json` ligado e publicado (o 8 é o quase-presente), migrations `core/0014` e `leitores/0002`. Testes: `AtmosferaPlacarTests` (`core/tests/test_imersivo.py`) e `core/tests/test_placar_voto.py`.

## Atmosfera «O quase-presente» (`atmosfera:quase-presente`, STAR-47)
Post 7 da série. `TEMPLATES_ATMOSFERA` aponta para `core/templates/core/imersivo_quase_presente.html`. Tudo escopado em `.qp-raiz` com o prefixo `.qp-` (ids `qp-*`, incluindo `qp-rachas` e `qp-mk`, que ficam dentro da raiz).
- **Peças**: cidade azul de vigilância (3 camadas de prédios com parallax); luz de varredura que desce com o scroll e incide nos cartões (`.qp-vig`); celular original que racha ao rolar, com faixa de incerteza 0,35 / 0,62 / 0,89 (dados fictícios); grafo de 6 registros com mira; 7 avisos de exemplo dispensáveis («AVISO DE EXEMPLO · FICÇÃO», com «Restaurar avisos»); salvaguardas (evidência, escolha, reparação) e celular-espelho cujo reflexo segue o cursor.
- **Ficheiros**: `static/js/imersivo/efeitos/atmosfera-quase-presente.js`, `static/css/atmosfera-quase-presente.css`, fixture `core/fixtures/quase_presente.json` (slug `o-quase-presente`, post pk 8, ato pk 19, um só ato com o efeito), migration `core/0012_alter_ato_efeito`. O episódio 7 da série (`serie_ia_na_ficcao.json`) passa a apontar para o post 8 e a ficar publicado: o hub liga a estação pela rota `/series/ia-na-ficcao/o-quase-presente/`.
- **Parâmetros**: nenhum (`PARAMETROS_POR_EFEITO["atmosfera:quase-presente"] = {}`); as faixas de scroll são constantes no JS (racha e faixa pela pista do ato 1; tremor de 1,6 px só enquanto racha). Sem biblioteca, sem imagens, sem rede, sem gravar nada.
- **Estado local**: variáveis dentro da função do efeito; `--rk` (racha) fica na raiz, nunca em `documentElement`. A varredura e o parallax medem a rolagem relativamente à raiz (`-raiz.getBoundingClientRect().top`), porque o cabeçalho e o rodapé do site deslocam a página.
- **Sticky**: `.qp-stage` (ato 1) a `top:76px` e `.qp-celular` do ato 3 a `top:96px`. Barra de baixo «A IA na ficção · 7» (390 px: «Ficção · 7»). Raiz com `overflow-x:clip`, nunca `hidden` no body.
- **Pausa**: botão «Pausar movimento» (≥ 44 px, `aria-pressed`) pára o loop (tremor, parallax, mira suave); o scroll continua a atualizar. Em movimento reduzido o botão fica oculto.
- **Movimento reduzido**: `.qp-estatico` (JS) e `@media (prefers-reduced-motion:reduce)` (CSS): celular rachado, faixa completa, 7 avisos visíveis, espelho a 100 %, varredura parada, sem tremor nem loop; pista e palco deixam de ser sticky.
- **390 px**: colunas únicas, parallax desligado; retoque 3 da revisão 7: o celular do ato 3 é escalado a 60 % (`transform:scale(.6)` com `margin-bottom:-240px`) para não ocupar quase um ecrã sem texto.
- **Fecho**: «Próxima estação: O placar» é um `<a>` para o post 8 (`core:episodio` com `serie`, senão `core:imersivo`); «Voltar» aponta ao hub `core:serie 'ia-na-ficcao'` (STAR-47). Idem no post 6 → 7. O fecho do post 8 liga ao hub e ao post 7 e mostra o índice dos 9 pontos da série (links aos publicados, texto nos restantes).
- **Vídeo e narração**: o bloco «Ver e ouvir» (`_midia.html`) vem do episódio 7; o `importar_midia` do STAR-59 já preenche o episódio 7 (só dados).
- **Direitos**: celular genérico (moldura lisa, sem marca); nenhum aviso imita alerta de sistema; todos os dados são «fictícios». Os avisos, as salvaguardas, as frases de registro e a nota do painel são rascunho a rever pelo Orochimaru.
