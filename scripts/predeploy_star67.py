"""Pré-deploy local (STAR-67): migrate do zero, fixtures, check --deploy,
collectstatic e fumo HTTP com DEBUG=False. Só local: SQLite novo, env FALSO.

Uso: python scripts/predeploy_star67.py <pasta-de-saida>
Cada fase corre num processo filho com o env falso; nada toca em produção,
em `.env*` ou em portas (o fumo usa django.test.Client).
"""

import os
import subprocess
import sys
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[1]
SETTINGS = "config.settings.prod"

# Ordem que funciona: posts (os episódios apontam para eles), depois a série.
FIXTURES = [
    "maquina_fria",
    "guerra_maquinas",
    "ser_humano",
    "escolhas",
    "leis_robos_livros",
    "quase_presente",
    "placar_post",
    "ia_afetiva",
    "imersivo_hub",
    "serie_ia_na_ficcao",
]

HOST = "stargate.invalid"
EPISODIOS = [
    "a-serie",
    "a-maquina-fria",
    "o-medo-da-guerra-das-maquinas",
    "o-que-e-ser-humano",
    "a-ia-afetiva",
    "leis-robos-e-livros",
    "escolhas-da-maquina",
    "o-quase-presente",
    "o-placar",
]


def env_falso(saida: Path) -> dict[str, str]:
    env = {
        k: v for k, v in os.environ.items() if not k.startswith(("DJANGO_", "DATABASE"))
    }
    env.update(
        DJANGO_SETTINGS_MODULE=SETTINGS,
        DJANGO_SECRET_KEY="falsa-" + "x" * 60,
        DJANGO_ALLOWED_HOSTS=HOST,
        DJANGO_CSRF_TRUSTED_ORIGINS=f"https://{HOST}",
        DATABASE_URL=f"sqlite:///{saida / 'predeploy.sqlite3'}",
        STATIC_ROOT=str(saida / "static"),
        MEDIA_ROOT=str(saida / "media"),
    )
    return env


def manage(env: dict[str, str], *args: str) -> int:
    cmd = [sys.executable, "manage.py", *args, f"--settings={SETTINGS}"]
    print("$ manage.py", " ".join(args), flush=True)
    return subprocess.run(cmd, cwd=RAIZ, env=env).returncode


def fumo() -> int:
    import django

    django.setup()
    from django.test import Client

    tabela = []
    cli = Client(HTTP_X_FORWARDED_PROTO="https", HTTP_HOST=HOST)

    def caso(nome, metodo, url, esperado, **kw):
        resp = getattr(cli, metodo)(url, **kw)
        loc = resp.headers.get("Location", "")
        pedido = f"{metodo.upper()} {url}"
        tabela.append((nome, pedido, esperado, resp.status_code, loc))

    caso("home", "get", "/", 200)
    caso("série", "get", "/series/ia-na-ficcao/", 200)
    for i, slug in enumerate(EPISODIOS):
        # o ep. 0 (a-serie) é o próprio hub: 301 para a página da série
        url = f"/series/ia-na-ficcao/{slug}/"
        caso(f"episódio {i}", "get", url, 301 if i == 0 else 200)
    caso("legado 301 (hub)", "get", "/imersivo/ia-na-ficcao/", 301)
    caso("legado 301 (post)", "get", "/imersivo/a-maquina-fria/", 301)
    caso("404", "get", "/series/ia-na-ficcao/nao-existe/", 404)
    caso("voto anónimo", "post", "/placar/voto/", 401, data={"obra": "x", "nota": 3})
    caso("saúde", "get", "/saude/", 200)
    sem_proxy = Client(HTTP_HOST=HOST).get("/")
    loc = sem_proxy.headers.get("Location", "")
    tabela.append(
        ("http puro → https (opt-in SSL)", "GET /", 301, sem_proxy.status_code, loc)
    )

    falhas = 0
    print("| caso | pedido | esperado | obtido | Location | ok |")
    print("|---|---|---|---|---|---|")
    for nome, pedido, esp, obt, loc in tabela:
        ok = esp == obt
        falhas += not ok
        print(f"| {nome} | `{pedido}` | {esp} | {obt} | {loc} | {'✓' if ok else '✗'} |")
    print(f"\n{len(tabela) - falhas}/{len(tabela)} como esperado")
    return 1 if falhas else 0


def main() -> int:
    if len(sys.argv) >= 2 and sys.argv[1] == "--fumo":
        os.chdir(RAIZ)
        sys.path.insert(0, str(RAIZ))
        return fumo()
    saida = Path(sys.argv[1]).resolve()
    saida.mkdir(parents=True, exist_ok=True)
    (saida / "predeploy.sqlite3").unlink(missing_ok=True)  # banco SEMPRE novo
    env = env_falso(saida)
    rc = 0
    for args in (
        ("migrate", "--noinput"),
        ("makemigrations", "--check", "--dry-run"),
        ("loaddata", *FIXTURES),
        ("check", "--deploy"),
        ("collectstatic", "--noinput"),
    ):
        r = manage(env, *args)
        print(f"-> rc={r}\n", flush=True)
        rc = rc or r
    print("$ fumo", flush=True)
    r = subprocess.run([sys.executable, __file__, "--fumo"], env=env).returncode
    return rc or r


if __name__ == "__main__":
    sys.exit(main())
