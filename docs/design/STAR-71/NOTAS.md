# STAR-71 — notas do mock `estilos.html` (09/11/2026)

Ficheiro único: `/data/Shopify/EonTeams/Hagoromo/cadeiras/_entregas/STAR-71/mock/estilos.html` (CSS no head, JS inline; só Google Fonts por rede).
Abrir: `estilos.html?estilo=3&pagina=series` (páginas: portal, series, noticias, newsletter, conta, post-sem-envelope). `?ab=1,5` abre o A × B.
Provedor: executor Sonnet (subagente); o CSS da direção 0 é a cópia literal de `tokens.css`, `stargate.css` e `luz.css` do Hidan, e o `luz.js` é o do STAR-51.

Mapa de páginas: o «portal» é a home com manchete, «O futuro, hoje», séries, números e newsletter; «séries» é o `portal.html` actual (a lista de séries do Hidan) mais os episódios da série. O site de produção hoje não tem notícias publicadas (a lista diz «Ainda não há outras notícias»); o mock usa notícias e números fictícios (marcados como tal) para o estilo poder ser julgado com conteúdo cheio.

## As 6 direções

### 0 · Editorial solar (o atual)
- **Ideia:** o site como está: creme quente, coral e sol, serifa expressiva, cantos arredondados e a luz do dia que muda com a hora.
- **Fontes:** Fraunces + Instrument Sans.
- **Paleta:** `--sg-creme #FBF5EA`, `--sg-tinta #1F1914`, `--sg-coral #EB5A3C` / `--sg-coral-ink #B3321A`, `--sg-sol #F7B84B`, `--sg-ceu #2A6FA8`.
- **Grelha:** colunas simétricas 3/4, cartões de 14–24 px de raio, manchete 5fr/7fr.
- **Movimento:** hover de cartão sobe 3 px; luz segue o cursor.
- **Luz e névoa:** as 5 fases do dia no herói (`luz-ceu`), brilho no botão, halo no cartão, névoa na caixa de conta e na newsletter.
- **Riscos:** nenhum de acessibilidade (já validado no STAR-51). O problema é de carácter: é correto e morno, sem assinatura; as páginas internas parecem um template.
- **Brilha:** coerência com os posts de tom quente. **Falha:** não acompanha o nível dos posts imersivos.

### 1 · Revista «Capa»
- **Ideia:** o Stargate como capa de revista de ciência: título-monumento, régua grossa, numeração de folhas e preto e branco com um único vermelho.
- **Fontes:** Bodoni Moda (títulos, itálico forte) + Hanken Grotesk (rótulos, UI).
- **Paleta:** `--sg-creme #FAF9F6`, `--sg-tinta #0F0F0F`, `--sg-coral #D4141C` (acento único), `--sg-creme-2 #EFEDE7`; ilustrações em tons de cinza que ganham cor ao passar o rato.
- **Grelha:** 12 colunas com fios verticais finos; cabeçalho a «mastro» central; cartões sem raio, numerados (01, 02, …) por contador CSS; secção «números» em bloco preto; newsletter em bloco vermelho de largura total.
- **Movimento:** só cor e sublinhado (arte cinza → cor em 0,5 s).
- **Luz e névoa:** luz = holofote branco `soft-light` que segue o cursor sobre a capa; névoa = bruma rosada que se desloca devagar atrás do título.
- **Riscos:** Bodoni em corpo pequeno tem hastes finas (usado só ≥ 1,05 rem, o corpo corrente é a Hanken). Contraste alto, bom. Peso: duas famílias, 5 estilos Bodoni.
- **Brilha:** autoridade e ritmo editorial; **falha:** as ilustrações a cinza apagam a cor dos temas (Futuro, Saúde, etc.), que o site actual usa como código.

### 2 · Retro «Sala de controle»
- **Ideia:** ficção científica dos anos 1980 como painel de bordo: fósforo verde, âmbar e molduras de terminal.
- **Fontes:** Orbitron (títulos) + IBM Plex Mono (texto).
- **Paleta:** `--sg-creme #050F0A`, `--sg-tinta #D2FFE6`, verde `#4DFFA4`, âmbar `--sg-coral #FFB000`, `--sg-linha #1F6B46`.
- **Grelha:** painéis com moldura de 1 px e cantos «colchete», títulos com prefixo `$` e `//`, nav `[ ASSIM ]`, manchete dentro de uma janela `stargate://manchete`.
- **Movimento:** cursor `_` a piscar na marca, uma barra de varredura a descer; ambos só com `prefers-reduced-motion: no-preference`.
- **Luz e névoa:** luz = brilho verde sob o cursor; névoa = bloom verde no rodapé da página e linhas de varrimento; as ilustrações ficam monocromáticas verdes.
- **Riscos:** texto longo em monoespaçada cansa (corpo 16 px, mantido curto); `text-shadow` de brilho baixa a nitidez em ecrãs ruins; contraste do texto 10:1 ou mais. As linhas de varrimento são decorativas (`pointer-events: none`).
- **Brilha:** personalidade e proximidade com a ficção da série «A IA na ficção». **Falha:** tom pesado para notícias de saúde e clima; risco de parecer «tech de 2012».

### 3 · Observatório «Noite estrelada»
- **Ideia:** um observatório à noite: tudo é visto por uma lente redonda, com estrelas e uma nebulosa lenta atrás.
- **Fontes:** Cormorant Garamond (títulos, itálico) + Jost (UI).
- **Paleta:** `--sg-creme #090E22`, `--sg-papel #0F1840`, `--sg-tinta #F7F0DC`, ouro `--sg-coral #E8C170`, `--sg-ceu #8FA8FF`.
- **Grelha:** eixo central, secções com título centrado e estrela ✦, cartões centrados com a arte em círculo (lente) e anéis de órbita no herói.
- **Movimento:** estrelas que cintilam (opacidade, 4 s) e nebulosa que deriva (40 s); a lente cresce 4% no hover.
- **Luz e névoa:** luz = brilho creme sob o cursor, como a ocular de um telescópio; névoa = nebulosa roxa e azul desfocada.
- **Riscos:** Cormorant tem x-height baixa, por isso os corpos são 18 px+ e itálico só no lede; modo escuro permanente (o leitor que prefere claro não tem alternativa); a camada de estrelas é grande mas barata (gradientes, sem imagens).
- **Brilha:** é a direção mais próxima da atmosfera dos posts imersivos de espaço. **Falha:** secções de «números» e conta ficam mais sérias do que o tom «boas notícias».

### 4 · Papel e tinta «Gazeta»
- **Ideia:** um jornal-artesanato: papel com fibra, tinta azul-preta, carimbo vermelho, recortes colados com fita.
- **Fontes:** IM Fell English (títulos, irregular de impressão antiga) + Libre Baskerville (corpo e UI).
- **Paleta:** `--sg-creme #ECE2CA`, `--sg-papel #F6EFDC`, `--sg-tinta #1C1A2A`, vermelho carimbo `--sg-coral #A8281D`, ouro `--sg-sol #C99A3B`.
- **Grelha:** assimétrica, cartões «recorte» com borda irregular e rotação de ±0,8°, fita adesiva, fotos «polaroid» no herói, régua dupla nas secções, newsletter com borda serrilhada (`clip-path`).
- **Movimento:** o cartão endireita e sobe 4 px no hover; o botão roda 1,5°; a nebulosa de tinta faz uma deriva lenta (30 s).
- **Luz e névoa:** luz = poça de candeeiro quente (`soft-light`) sob o cursor; névoa = manchas de tinta desfocadas e vinheta nos cantos.
- **Riscos:** textura de papel em SVG (feTurbulence) como fundo repetido: custa pintura, e foi limitada a 220 px; IM Fell só tem peso 400 (títulos nunca em negrito); `clip-path` recorta a sombra da newsletter.
- **Brilha:** calor e humanidade, diferente de todos os portais de tecnologia. **Falha:** menos «futuro», o tema pede conteúdo mais literário.

### 5 · Brutalista luminoso «Bloco»
- **Ideia:** brutalismo gráfico e alegre: blocos de cor chapada, bordas pretas de 3 px, sombra dura e letras enormes.
- **Fontes:** Archivo Black (títulos, maiúsculas) + Space Grotesk (texto).
- **Paleta:** `--sg-creme #FBFBF4`, `--sg-tinta #000`, amarelo `#FFE53B`, azul `--sg-coral-ink #1F2FE0`, rosa `--sg-coral #FF4FA3`.
- **Grelha:** blocos rígidos com borda, cabeçalho em células, faixa «ticker» a correr, secções alternadas amarelo / rosa / azul, cartões com sombra deslocada 6 px.
- **Movimento:** passos (`steps(2)`) em vez de curvas: o cartão «salta» 4 px; ticker linear lento (só sem reduced-motion).
- **Luz e névoa:** luz = holofote duro amarelo (borda nítida, sem gradiente) sob o cursor sobre o herói; névoa = trama de pontos de meio-tom a esbater nas bordas da página. A «luz» projecta sombras duras, não suaves.
- **Riscos:** muito barulhento para leitura longa (a estratégia é o envelope ser barulhento e o post calmo); maiúsculas em títulos longos dificultam a leitura; o ticker é decorativo e `aria-hidden`.
- **Brilha:** é a mais memorável e a de menor risco técnico (sem imagens, sem texturas). **Falha:** pode contradizer o «otimismo com fontes» sério do texto.

## Arquitetura do tema base para o Hidan

**Princípio:** o tema só desenha o *envelope* (topo, cabeçalho, rodapé, newsletter, tipografia e tokens). O conteúdo (HTML do site base) é o mesmo em todas as direções; o mock prova-o: as 6 direções partilham 100% do markup.

1. **Tokens que o tema expõe** (já existem; o mock só os redefine): cor `--sg-creme`, `--sg-creme-2`, `--sg-papel`, `--sg-linha`, `--sg-campo-borda`, `--sg-tinta` (1 a 3), `--sg-coral` / `--sg-coral-ink` / `--sg-coral-bg`, `--sg-sol`, `--sg-ceu`, `--sg-t-<tema>` (6); tipo `--sg-serif`, `--sg-sans`, `--sg-fs-*`, `--sg-lh-*`; forma `--sg-r1..r3`, `--sg-pill`, `--sg-sombra`; luz `--luz-sol`, `--luz-cor`, `--luz-borda`, `--luz-borda-foco`, `--luz-foco`; hero do dia `--ceu-tx/tx2/tx3/ac` e as 5 fases (`.luz-ceu__fundo i[data-f]`). Para a arte SVG: `--g0..g2` (gradiente) e `--s1..s3` (formas), no lugar das cores fixas do `_arte.html`.
2. **Como o tema entra:** `<html data-estilo="N">`, e cada tema é um ficheiro `static/css/temas/<nome>.css` com `html[data-estilo=N] .sg-env { tokens; regras do envelope }`. A direção 0 (hoje) continua a ser o `stargate.css` sem atributo. O ID `N` mapeia para um nome estável (`solar`, `capa`, `controle`, `observatorio`, `gazeta`, `bloco`).
3. **O envelope é uma classe.** O `noticias/base.html` ganha um invólucro `.sg-env` à volta de topo + cabeçalho + `<main>` + newsletter + rodapé, e um bloco Django `{% block envelope %}` ao redor dele. Um post imersivo declara «sem envelope» de uma de duas maneiras: (a) override do bloco `{% block envelope %}{% endblock %}` no seu template (o que o `imersivo.html` já faz hoje na prática, pois tem o seu `<html>`); (b) uma flag `PostImersivo.sem_envelope` (default `True` para os 8 posts atuais) que o base lê para não escrever `.sg-env` nem o `<link>` do tema. O mock mostra (a): `#pg-post` está fora de `.env`.
4. **Como o seletor lê `?estilo=`:** ordem de precedência `?estilo=` (URL) → escolha guardada → padrão do site. Em produção a escolha guardada seria um cookie `sg-estilo` (o servidor escreve o `data-estilo` já no HTML, sem piscar) ou, para quem tem sessão, um campo do perfil; no mock é `localStorage['sg-estilo']` com try/catch. O painel flutuante só é emitido para quem tem sessão de staff ou com `?estilo=`; os leitores recebem o estilo escolhido pelo Patrick (uma variável de configuração do site).
5. **O que o tema não pode tocar nos posts imersivos:** nada fora de `.sg-env`; nenhum seletor global (`body`, `a`, `h1`, `:root`) nos ficheiros de tema; nenhuma fonte global (o tema declara as suas fontes via `<link>` só quando renderiza envelope); nenhum `overflow`/`position` no `body`; o `luz.js` continua a ser o mesmo (só escreve `--luz-*` em `[data-luz]`, que no post não existem); nada de `z-index` acima do canvas do post; o `transicao.css`/`transicao.js` mantém o `--vt-fundo` do tema **só** na página de envelope (hoje está fixo em `#FBF5EA`, o que precisará de passar a ser lido do tema para a transição envelope → post não piscar).
6. **Mudança mínima no código:** (i) `base.html`: `data-estilo` no `<html>` e `.sg-env`; (ii) `<link>` condicional ao tema; (iii) mover as cores fixas de `_arte.html`, `base.html` (o SVG da marca) e `stargate.css` (`rgba(251,245,234,…)`, `#FFB59E`, `#DDF1E7` etc.) para tokens; (iv) `luz.css`: os 5 fundos do `luz-ceu` passam a ser opcionais por tema (os temas 1 a 5 desligam-nos).

## Perguntas ao Patrick

1. **Qual das 5 direções novas quer ver implementada primeiro?** Recomendo a **3 (Observatório)** se o que mais o incomoda é a distância para os posts imersivos (é a que melhor os acompanha), ou a **1 (Revista)** se quer o site mais sério e jornalístico. A 5 é a mais barata e a 2 a mais arriscada.
2. **Um estilo único para todos ou o leitor pode escolher (claro/escuro, por exemplo)?** Recomendo **um estilo único** agora (menos código e menos casos de teste) e, depois, uma variante escura da escolhida. A arquitetura de tokens já permite as duas coisas.
3. **A mudança vale só para o site base ou também para as páginas-hub das séries (como `/series/ia-na-ficcao/`)?** Recomendo **incluir os hubs** no tema (têm cabeçalho e rodapé do site) mas manter o corpo dos posts, como hoje, «sem envelope».

## O que ficou por fazer
- Não foi feito: o hub real da série, o artigo (`artigo.html`) e a página «criar conta»; só as 5 páginas pedidas e o post sem envelope.
- Contraste: verificado a olho nos 6 temas; falta uma passagem com a ferramenta de contraste (o `docs/contrastes.txt` do Hidan é a régua).
- Desempenho: o mock carrega 11 famílias de uma vez; em produção cada tema carregaria só as suas 2.
