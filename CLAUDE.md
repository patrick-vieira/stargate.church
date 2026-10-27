# CLAUDE.md — stargate.church

Guia para qualquer agente (Claude, Codex, Gemini…) que trabalhe neste repositório.
O `AGENTS.md` aponta para este ficheiro: **a fonte é só esta**.

## O produto
Portal de notícias de tecnologia com uma **visão positiva do futuro, da IA e dos seus avanços**.
Tom: claro, verificado, esperançoso sem ser ingénuo. Todo artigo publicado tem fontes verificadas.

## Repositório PÚBLICO
- **Nunca** commitar segredos, chaves, tokens, `.env` com valores, dados pessoais ou de clientes.
- Segredos só por variável de ambiente; o `.env.example` leva os nomes, sem valores.
- Este projecto é isolado: não depende de nada de outros sistemas nem os referencia.

## Stack e layout
- Python 3.13, **Django 5.2 LTS**, dependências com **pip** (`requirements.txt` + `requirements-dev.txt`, versões fixas); `ruff` configurado no `pyproject.toml`.
- `manage.py` na raiz; settings em `config/settings/{base,dev,test,prod}.py`.
- Apps: `core` (home, `/saude/`) e `noticias` (modelo editorial). Testes em `<app>/tests/`.
- Banco: Postgres no `docker-compose.yml` de desenvolvimento; **testes em SQLite**.
- `LANGUAGE_CODE='pt-br'`, `TIME_ZONE='America/Sao_Paulo'`.

## Comandos
```
pip install -r requirements-dev.txt                            # instala dependências (num venv)
python manage.py check                                         # verificações do Django
python manage.py test --settings=config.settings.test          # testes (SQLite)
ruff check . && ruff format --check .                          # lint e formato
python scripts/testar_cadeira.py [modulo ...]                  # o portão do executor: ruff, format, makemigrations --check e test (rc por passo)
DJANGO_SETTINGS_MODULE=config.settings.prod DJANGO_SECRET_KEY=<chave-ficticia-longa> DJANGO_ALLOWED_HOSTS=exemplo.test python manage.py check --deploy  # settings de produção; valores fictícios só na linha de comando, nunca .env nem segredos reais. Avisos esperados: W005 (HSTS subdomínios) e W021 (HSTS preload), opt-in deliberado em prod.py
pre-commit run --all-files                                     # todos os ganchos
docker compose config                                          # valida o compose
```

## Régua de código
- **ruff** (lint + format) é a lei; o pre-commit e a CI usam-no. Código limpo antes do commit.
- Funções e classes pequenas, nomes claros; comentários só para o «porquê».
- Identificadores de código em inglês ou português, mas **coerentes** dentro de cada app;
  modelos de domínio editorial em português (`Artigo`, `Fonte`, `Tema`, `Autor`).
- Sem lógica de negócio em views ou templates: vai para modelos/serviços.
- Migrações sempre versionadas; nunca editar uma migração já integrada.

## Testes
- Todo comportamento novo leva teste; correção de bug leva teste que a reproduz.
- Correr antes de entregar: os testes das apps tocadas **e** os de quem usa as rotas/views alteradas.
- Fixtures e dados de teste são sempre fictícios.

## PT-BR
- **Toda a UI, mensagens, admin e conteúdo em português do Brasil.**
- Datas por extenso e em minúscula: «domingo, 18 de outubro de 2026».
- Código, commits e documentação interna em português (commits com a ref `STAR-n` no título).

## UI
- Design system: `static/css/tokens.css` (valores não se alteram). Fontes: Fraunces (títulos) e Instrument Sans (texto).
- Coral `#EB5A3C` só em formas e texto grande; texto pequeno e links em `#B3321A`.
- Sem scroll horizontal a 390 px. Conferir sempre em 1920 e 390.

## Portões
- **Código:** PR com CI verde + revisão do líder; o merge (merge commit) é feito pelo esp_git.
- **UI:** APROVADO do Hagoromo em pares mock | entregue, a 1920 e 390 px.
- **Deploy e domínio:** só o Patrick.
- Nunca push direto para `main`.

## Fluxo de um card
1. Ramo a partir da `main`; um card por ramo; só o recorte do card.
2. Commits pequenos, mensagem em português com `STAR-n` no título.
3. Abrir PR com o template (`.github/pull_request_template.md`), incluindo o **registo**.
4. Registo por entrega: provedor, modelo, tokens/custo, tempo, portão à 1.ª, retrabalho.
   O roteamento de executores está em `docs/roteamento.yaml`.

## Autoria dos commits
- Autor e committer identificam o agente (nome e e-mail do executor, marcados «IA»).
- Trailer obrigatório: `Co-authored-by: Patrick Vieira <pdsv88@gmail.com>`.

## Dúvida
Se o pedido não está claro, **não adivinhes**: pergunta ao líder, com opções e a tua recomendação.
