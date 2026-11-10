# STAR-71 — Aparências do envelope

A decisão do Patrick manteve duas direções: 3 Noite estrelada (padrão) e 5 Bloco. O original permanece em `?estilo=0`.

- **3 — Noite estrelada:** azul profundo, estrelas em CSS, cartões translúcidos, títulos Fraunces e texto Instrument Sans. A navegação usa os eventos da onda 7 com aproximação e afastamento estelar em 720 ms. Movimento reduzido desliga a viagem; navegadores sem View Transitions mantêm o fundido existente.
- **5 — Bloco:** amarelo, lilás e verde, contornos grossos, sombras sólidas, cantos retos e títulos em Instrument Sans. Mantém o fundido comum da onda 7.
- **0 — Original:** conserva os tokens e o desenho anterior; ganha somente o seletor de comparação.

## Escolha do leitor

O painel «Seu Stargate» está disponível para todos, conforme a decisão do card de permitir a troca pelo leitor. Os links recarregam a página, preservam filtros e funcionam sem JavaScript. A query válida prevalece sobre o cookie; um valor inválido usa o cookie válido ou o padrão 3. O cookie próprio dura um ano, tem caminho `/`, SameSite=Lax e Secure em HTTPS. A preferência é por navegador, sem alteração de conta ou migration.

Na primeira visita sem escolha, o convite oferece a outra direção. Escolher uma direção encerra o convite. «Agora não» dispensa o convite por um ano no mesmo navegador; o seletor continua disponível. Sem JavaScript, o convite e os links continuam utilizáveis, mas a dispensa fica indisponível.

## Isolamento dos imersivos

`tokens.css` não foi editado. As novas variáveis e regras visuais exigem `data-envelope=base`. Páginas com `post` recebem `data-envelope=livre`, não exibem seletor nem convite e conservam os templates, efeitos e HTML anteriores. A função de clima só aplica a viagem estelar ao envelope base. Um template futuro pode sobrescrever os blocos `envelope`, `topo_envelope`, `newsletter` e `rodape_envelope` para dispensar completamente o envelope. Os novos testes cobrem essa opção.

## Arquivos e revisão

- `core/estilos.py`: validação, contexto, links e persistência; respostas variam por Cookie e escolhas explícitas são privadas para cache.
- `config/settings/base.py`: registro do middleware e contexto.
- `noticias/templates/noticias/base.html` e `_estilos.html`: atributos de isolamento, painel, convite e blocos opcionais.
- `static/css/estilos.css`, `static/js/estilos.js` e `static/js/transicao.js`: variantes, dispensa e clima estelar.
- `core/tests/test_estilos.py`: preferência, precedência, cookie HTTPS, entrada inválida, filtros, imersivos, opção sem envelope e sete guardas de sinks.
- `core/tests/test_onda7.py`: expectativa atualizada para os novos atributos do elemento html.

## Provas locais

O portão é `scripts/testar_cadeira.py` do próprio projeto, conforme o brief Codex. O wrapper externo do kit aponta para `e2/src` e settings de outro projeto; não foi modificado nem executado.

Módulos: `core.tests.test_estilos`, `core.tests.test_onda7`, `core.tests.test_imersivo`, `core.tests.test_series`, `core.tests.test_views`, `core.tests.test_fumo_rotas`, `noticias.tests.test_views`, `noticias.tests.test_context_processors`, `leitores.tests.test_conta`, `leitores.tests.test_luz_conta`. Resultado: 256 testes, OK, uma falha esperada preexistente; ruff, formato e migrations verdes.

Capturas em `_provas/STAR-71/`: portal, notícias e conta nos estilos 0/3/5, em 1920 e 390 px. Os arquivos JSON registram a largura efetiva e a geometria: sem excesso horizontal ou textos/controles cortados nas 18 combinações. As capturas finais são do palco local isolado, renderizado no Chromium com movimento reduzido para congelar as imagens. Dados fictícios, SQLite exclusivo em `_provas`, porta 19371 medida livre por `ss -ltn` após semáforo verde. O servidor próprio foi encerrado ao final, após conferir seu cwd; nenhum processo alheio foi tocado e a porta 8170 não foi usada.

`palco.json` registra também duas interações reais no navegador: clicar no estilo Bloco e navegar para notícias preservando o cookie; dispensar o convite e recarregar sem que ele reapareça. Ambas passaram. A revisão visual da viagem com movimento normal e o aceite do líder continuam pendentes. Nenhuma migration em banco compartilhado; somente o SQLite exclusivo da prova foi preparado.

## Registro

OpenAI/Codex, implementação direta autorizada por caixa-stargate#1824 e decisão #1765. Modelo exato, tokens, custo e duração total não expostos/medidos. Primeiro portão detectou regressão de rodapé ao retirar HTML de imersivos; corrigida preservando o HTML original. Sem git, commit, push, PR ou migration nova. Revisão do líder, commit/PR e CI continuam pendentes. O resultado final do portão e a contagem constam na carta de entrega.
