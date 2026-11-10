# Séries editoriais do museu

Os seis grafos ficam versionados em `core/dados/grafos/`. A importação é
repetível e não publica séries por padrão:

```sh
python manage.py importar_series_museu --settings=config.settings.dev
```

Para preparar uma demonstração local com as portas visíveis, publique as seis
séries apenas no banco local selecionado:

```sh
python manage.py importar_series_museu --settings=config.settings.dev --publicar
```

O comando `importar_grafo` valida cada fixture e preserva o estado de publicação
existente. O importador em lote não corre automaticamente na inicialização e
não altera a publicação sem `--publicar`. Não há migration nova.
