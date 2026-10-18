# AGENTS.md — stargate.church

As instruções para agentes (Codex, Gemini, Claude e outros) vivem num só ficheiro:
**[CLAUDE.md](CLAUDE.md)**. Lê-o por inteiro antes de começar; é a única fonte.

Resumo mínimo:
- Repositório **público**: nunca segredos nem dados de clientes.
- Django 5.2 + uv; testes: `uv run python manage.py test --settings=config.settings.test`; lint: ruff.
- UI e conteúdo em **PT-BR**; commits em português com `STAR-n` no título.
- Sem push direto para `main`: PR com CI verde, revisão do líder e o registo preenchido.
- Executores e roteamento: `docs/roteamento.yaml`.
