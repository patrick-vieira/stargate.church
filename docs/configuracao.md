# Configuração por variáveis de ambiente

## STATIC_ROOT (STAR-35)
Pasta onde o `collectstatic` escreve (e de onde o WhiteNoise serve).

- **Ausente:** `<projecto>/staticfiles` (comportamento histórico, inalterado).
- **Definida:** o valor é usado como caminho, p. ex. `STATIC_ROOT=/var/www/stargate/static`.
- Não a deixes **vazia** no `.env`: vazio não conta como ausente e dá a pasta actual. Comenta a linha ou omite-a.

Definição em `config/settings/base.py`; exemplo em `.env.example`.
