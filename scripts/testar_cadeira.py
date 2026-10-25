"""O portão do executor: lint, formato, migrations e testes, num só comando.

Uso: python scripts/testar_cadeira.py [modulo ...]
Sem módulos corre a suíte toda. Não pára no 1.º erro; sai com rc≠0 se algum
passo falhar.
"""

import subprocess
import sys
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[1]
SETTINGS = "--settings=config.settings.test"


def _ruff() -> str:
    candidato = Path(sys.executable).parent / "ruff"
    return str(candidato) if candidato.exists() else "ruff"


def passos(modulos: list[str]) -> list[tuple[str, list[str]]]:
    ruff = _ruff()
    py = sys.executable
    return [
        ("ruff check", [ruff, "check", "."]),
        ("ruff format --check", [ruff, "format", "--check", "."]),
        (
            "makemigrations --check",
            [py, "manage.py", "makemigrations", "--check", "--dry-run", SETTINGS],
        ),
        ("test", [py, "manage.py", "test", *modulos, SETTINGS, "--noinput"]),
    ]


def main(argv: list[str] | None = None) -> int:
    modulos = list(sys.argv[1:] if argv is None else argv)
    falhou = False
    for nome, comando in passos(modulos):
        rc = subprocess.run(comando, cwd=RAIZ).returncode
        print(f"[{'OK' if rc == 0 else 'FALHOU'}] {nome} (rc={rc})")
        falhou = falhou or rc != 0
    return 1 if falhou else 0


if __name__ == "__main__":
    sys.exit(main())
