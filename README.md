# stargate.church

Portal de notícias sobre tecnologia com uma visão positiva do futuro, da IA e dos seus avanços.
O projeto é construído em Python 3.13 com o framework Django 5.2 LTS, utilizando PostgreSQL como banco de dados (SQLite em desenvolvimento) e um sistema de templates com design limpo e moderno.

## Estrutura do Repositório

```text
├── config/       # Configurações do Django (settings, urls, etc.)
├── core/         # App principal (home e funcionalidades gerais)
├── leitores/     # App de gerenciamento de leitores
├── noticias/     # App de domínio editorial (artigos, fontes, temas)
├── scripts/      # Scripts utilitários (ex: testar_cadeira.py)
├── static/       # Arquivos estáticos (CSS, fontes, imagens)
├── docs/         # Documentação complementar
├── manage.py     # Script de gerenciamento do Django
└── README.md     # Esta documentação
```

## Arranque Local (Sem Docker)

Para rodar o projeto localmente com o banco SQLite padrão, siga os passos abaixo:

1. **Crie e ative o ambiente virtual:**
   ```bash
   python3 -m venv .venv
   source .venv/bin/activate
   ```
2. **Instale as dependências de desenvolvimento:**
   ```bash
   pip install -r requirements-dev.txt
   ```
3. **Execute as migrações do banco de dados:**
   ```bash
   python manage.py migrate --settings=config.settings.dev
   ```
4. **Carregue os dados de demonstração (fixture):**
   ```bash
   python manage.py loaddata stargate_demo --settings=config.settings.dev
   ```
5. **Inicie o servidor de desenvolvimento:**
   ```bash
   python manage.py runserver --settings=config.settings.dev
   ```

## Arranque Local (Com Docker)

Você pode utilizar o `docker-compose.yml` para rodar a aplicação junto com o banco PostgreSQL.

1. Crie o arquivo `.env` na raiz do projeto contendo pelo menos a senha do banco:
   ```bash
   echo "POSTGRES_PASSWORD=sua-senha-ficticia" > .env
   ```
2. Inicie os serviços em segundo plano:
   ```bash
   docker compose up -d
   ```

## Ambiente de Staging

O ambiente de staging utiliza as configurações de produção (`config.settings.staging`, que estende `prod.py`), mas difere do ambiente local ou de produção estrita por ser configurado para rodar em HTTP na LAN atrás de um proxy. Dessa forma, as variáveis que forçam HTTPS e cookies seguros (`DJANGO_SECURE_SSL_REDIRECT`, `DJANGO_SESSION_COOKIE_SECURE`, `DJANGO_CSRF_COOKIE_SECURE`) são definidas como `False`.

## Testes e Qualidade

O projeto possui comandos dedicados para assegurar a qualidade do código:

- **Executar os testes (utiliza SQLite em memória):**
  ```bash
  python manage.py test --settings=config.settings.test
  ```
- **Portão do executor (Lint, formatação, migrações e testes):**
  ```bash
  python scripts/testar_cadeira.py
  ```

## Variáveis de Ambiente

As configurações do projeto suportam as seguintes variáveis através do arquivo `.env` ou do ambiente:

| Nome da Variável               | Obrigatória?        | Exemplo Fictício                                |
|--------------------------------|---------------------|-------------------------------------------------|
| `DJANGO_SETTINGS_MODULE`       | Sim (se não passada)| `config.settings.dev`                           |
| `DJANGO_SECRET_KEY`            | Sim (em prod)       | `chave-secreta-ficticia-super-segura`           |
| `DJANGO_ALLOWED_HOSTS`         | Sim (em prod)       | `localhost,127.0.0.1`                           |
| `DATABASE_URL`                 | Não (default SQLite)| `postgres://user:pass@db:5432/stargate`         |
| `POSTGRES_DB`                  | Não (p/ Docker)     | `stargate`                                      |
| `POSTGRES_USER`                | Não (p/ Docker)     | `stargate_user`                                 |
| `POSTGRES_PASSWORD`            | Sim (p/ Docker)     | `senha-ficticia-banco`                          |
| `DJANGO_CSRF_TRUSTED_ORIGINS`  | Não                 | `https://stargate.church`                       |
| `DJANGO_SECURE_SSL_REDIRECT`   | Não                 | `True` (False em staging)                       |
| `DJANGO_SESSION_COOKIE_SECURE` | Não                 | `True` (False em staging)                       |
| `DJANGO_CSRF_COOKIE_SECURE`    | Não                 | `True` (False em staging)                       |
| `STARGATE_TECTO_CONVERSA`      | Não                 | `20`                                            |
| `STARGATE_TECTO_COMENTARIO`    | Não                 | `10`                                            |
| `EASYON_API_URL`               | Não                 | `https://api.exemplo.com/v1`                    |
| `EASYON_API_KEY_FILE`          | Não                 | `/caminho/para/chave-easyon.txt`                |
