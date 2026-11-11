# STAR-74 — áudio dos blocos do livro-jogo

Implementado o management command `gerar_audio_grafo` em `core/management/commands/`, seguindo o padrão do app. O cliente existente `core/servicos/imagetools.py` ganhou `enviar_audio`, sem alterar o envio de vídeos. Nenhuma dependência foi acrescentada; usa o `httpx` já fixado nos requisitos.

O comando aceita `--grafo`, `--saida`, `--max-narracoes`, `--max-sons`, `--voz`, `--chaves` e `--seco`. O JSON de chaves deve conter `api_key` e `base_url` (raiz do serviço, sem `/v1`). Os pedidos de narração usam `eleven_multilingual_v2`; os efeitos duram quatro segundos. O upload usa `X-API-Key`, multipart `file`, MIME `audio/mpeg` e `folder=stargate/audio/<serie>/`. As credenciais de ImageTools seguem o cliente existente, por ambiente ou `IMAGETOOLS_CREDENCIAIS` (JSON `url`/`token`). Nenhum segredo é registrado em mensagens.

## Decisões

- Os limites são tetos de tentativas por execução, independentes por tipo, incluindo falhas. O padrão é zero, exigindo definir explicitamente o orçamento. Acertos da cache não consomem o teto.
- Cache JSON ao lado do manifesto: `<saida>.cache.json`. As entradas usam SHA-256 do texto exato e contexto de série/tipo/voz; sons usam contexto de duração fixa. Assim uma mudança de voz não reutiliza uma narração anterior.
- MP3s ficam em `<saida>.audios/`; após falha de upload, a próxima execução reaproveita o áudio local. Cache e manifesto usam arquivo temporário, flush, fsync e substituição atômica. Rodar um único processo por manifesto/cache; não há bloqueio para execuções concorrentes. Uma interrupção entre sucesso remoto do upload e persistência local pode exigir novo upload, pois a API não fornece aqui uma chave de idempotência.
- Manifesto contém todos os IDs do grafo atual, com os quatro campos solicitados. Campos sem resultado têm `null`; textos presentes recebem seu hash mesmo quando o teto impede a geração. A cache permite reconstruir o manifesto em uma retomada.
- `--seco` apenas lê, calcula e resume o plano: não exige chaves, não chama rede nem escreve arquivos. Não substitui um manifesto real com resultados fictícios.
- Falhas HTTP de geração ou upload registram ID/tipo/classe do erro e seguem. Não imprimem corpos de resposta nem detalhes de exceção que possam conter credenciais. O resumo informa publicados, acertos da cache, erros e planejados. Erros de configuração/arquivos encerram com erro de comando.
- Foram lidos apenas os exemplos externos indicados. Nenhuma API real foi chamada e nenhum comando git foi executado.

## Verificação

Cinco testes novos em `core/tests/test_audio_grafo.py`, com `httpx.post` e `httpx.request` simulados: contratos HTTP de geração/upload, manifesto e hashes, deduplicação entre blocos e execuções, limites, modo seco, continuidade após erro sem expor segredo e retomada de upload sem nova síntese.

Os dois venvs da cadeira não tinham `httpx`. A tentativa de instalar a versão já declarada falhou por indisponibilidade de DNS/rede. A suíte foi repetida usando dependências locais compartilhadas, sem instalação ou alteração dos requisitos:

```sh
PYTHONPATH=/data/Shopify/EonTeams/partilhada/venv-dev/lib/python3.13/site-packages /data/Shopify/EonTeams/Hidan/cadeiras/e2/.venv/bin/python manage.py test --settings=config.settings.dev
```

Resultado: **472 testes em 18,901 s; OK (expected failures=1)**. Sem `--parallel`. Aviso existente: diretório `staticfiles/` ausente. A primeira execução, antes do ajuste do ambiente, teve erro de importação de `httpx` no módulo novo.

Ruff check e format --check passaram para os três arquivos Python alterados.

## Corrida real

Defina `CHAVES_AUDIO`, `CHAVES_IMAGETOOLS` e `VOZ_AUDIO` no ambiente com os caminhos dos arquivos privados e o ID da voz escolhida. Não coloque esses arquivos no repositório. O comando abaixo processa até 24 narrações e 24 sons do exemplo fornecido e escreve os artefatos fora do repositório:

```sh
PYTHONPATH=/data/Shopify/EonTeams/partilhada/venv-dev/lib/python3.13/site-packages \
IMAGETOOLS_CREDENCIAIS="$CHAVES_IMAGETOOLS" \
/data/Shopify/EonTeams/Hidan/cadeiras/e2/.venv/bin/python manage.py gerar_audio_grafo \
  --settings=config.settings.dev \
  --grafo /data/Shopify/EonTeams/Konan/cadeiras/_entregas/STAR-73/energia-sem-fim.grafo.json \
  --saida /tmp/STAR-74/energia-sem-fim.audio.json \
  --chaves "$CHAVES_AUDIO" \
  --voz "$VOZ_AUDIO" \
  --max-narracoes 24 --max-sons 24
```

Acrescente `--seco` para conferir o plano. Guarde os arquivos de cache e MP3 junto do manifesto para retomar sem repetir trabalho. A integração real com os provedores permanece sem execução; os contratos foram verificados com mocks.
