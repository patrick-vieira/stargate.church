import re
import subprocess
import sys

# Coautor com e-mail «noreply» (assistentes de código) não expõe ninguém: é aceito.
_COAUTOR = re.compile(r"^\s*co-authored-by:", re.IGNORECASE)
_NOREPLY = re.compile(r"<[^>]*noreply[^>]*>\s*$", re.IGNORECASE)


def linhas_proibidas(mensagem: str) -> list[str]:
    """Linhas de trailer Co-authored-by com e-mail pessoal (sem «noreply»)."""
    return [
        linha
        for linha in mensagem.splitlines()
        if _COAUTOR.match(linha) and not _NOREPLY.search(linha)
    ]


def main(argv) -> int:
    if len(argv) != 1:
        print("Uso: python scripts/verificar_mensagens.py <intervalo-git>")
        return 1

    intervalo = argv[0]
    if not intervalo:
        return 0

    try:
        resultado = subprocess.run(
            ["git", "log", "--format=%H%x00%B%x1e", intervalo],
            capture_output=True,
            text=True,
            check=True,
        )
    except subprocess.CalledProcessError as e:
        print(f"Erro ao executar git log: {e}", file=sys.stderr)
        return 2

    commits_com_problemas = False
    commits = resultado.stdout.strip().split("\x1e")

    for commit in commits:
        if not commit.strip():
            continue

        sha, mensagem = commit.strip().split("\x00", 1)
        sha_curto = sha[:7]
        linhas = linhas_proibidas(mensagem)

        if linhas:
            commits_com_problemas = True
            for linha in linhas:
                print(f"{sha_curto}: {linha}")

    return 1 if commits_com_problemas else 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
