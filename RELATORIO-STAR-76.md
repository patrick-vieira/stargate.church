# STAR-76 — viagem entre estrelas

## Implementação

A escolha do envelope permanece em `core/estilos.py`: query `estilo`, depois cookie `stargate_estilo`, com Noite estrelada (`3`) como padrão. O template compartilhado é `noticias/templates/noticias/base.html`; o fundo estático de estrelas permanece em `static/css/estilos.css`.

O template carrega `static/css/viagem-estrelas.css` e `static/js/viagem-estrelas.js` somente para Noite estrelada, fora dos posts imersivos. O bloco `viagem_estrelas` permite que templates derivados dispensem os recursos. O JS também verifica o envelope efetivo no HTML antes de criar a camada.

Substituí a antiga ampliação da página inteira por um céu independente, com 48 estrelas decorativas, distribuição determinística e `view-transition-name: estrelas`. O instantâneo antigo acelera radialmente em direção ao leitor por 380 ms; o novo desacelera por 420 ms. O conteúdo faz apenas uma passagem de opacidade. A camada é fixa, recortada na viewport, sem eventos de ponteiro e oculta da árvore de acessibilidade.

## Decisões

- View Transitions entre documentos, com `@view-transition { navigation: auto; }` e eventos `pageswap`/`pagereveal`. Sem interceptar cliques, atrasar a navegação, buscar HTML ou alterar o histórico.
- Sem suporte aos eventos/API, navegação normal. No envelope Noite estrelada, o fallback anterior de entrada também fica sem animação.
- `prefers-reduced-motion: reduce` impede a camada e desliga as animações. A opção existente `?semvt=1` continua sendo respeitada; `?semvt=0` a limpa.
- Não foi encontrado interruptor lúdico/sóbrio no repositório (busca pelos termos com e sem acento).
- Bloco e Original não carregam os novos recursos. A seleção automática do antigo clima `estelar` saiu do JS compartilhado; os demais climas permanecem como estavam.
- Sem dependências novas, mudanças nos tokens, comandos git ou subagentes.

## Verificação

- `python` não está disponível no PATH; utilizado o Python do ambiente virtual autorizado.
- `.venv/bin/python manage.py test --settings=config.settings.dev`, sem paralelismo: **469 testes, OK, 1 falha esperada**. System check sem problemas.
- Testes novos cobrem recursos exclusivos da Noite estrelada na home, notícias e entrada de leitores, contexto do estilo e precedência query/cookie/padrão. O teste de posts imersivos verifica ausência dos novos recursos.
- `.venv/bin/ruff check .`: passou.
- `.venv/bin/ruff format --check .`: passou (96 arquivos).
- Aviso de teste: diretório `staticfiles/` ausente, sem falha na suíte.
- A animação e as larguras de 1920/390 px ainda precisam de conferência visual em navegador; não foi realizada validação visual nesta execução. A camada usa `position: fixed`, `inset: 0` e `overflow: hidden` para conter as estrelas na viewport.

## Como ver

1. Inicie o servidor com `.venv/bin/python manage.py runserver --settings=config.settings.dev`.
2. Em navegador com suporte a View Transitions entre documentos e tipos de transição, abra `http://127.0.0.1:8000/?estilo=3`.
3. Clique em Notícias e depois na marca Stargate: o céu acelera e desacelera durante a troca, em aproximadamente 800 ms. A primeira abertura não inicia uma viagem.
4. Confira nas larguras de 1920 e 390 px. Links para fragmentos, novas abas e downloads mantêm o comportamento nativo.
5. Repita com `?estilo=5`: o Bloco não tem viagem nem carrega os novos arquivos.
6. Ative redução de movimento no sistema/navegador ou use `?semvt=1`: navegação sem viagem. Para restaurar a API na sessão, use `?semvt=0`.

Executor: OpenAI Codex. Tokens/custo não disponíveis nesta sessão. Commit e revisão ficam a cargo do Hokage.
