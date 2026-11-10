"""Cliente mínimo do ImageTools (S3 com API) para os vídeos dos episódios.

Configuração só por variáveis de ambiente (nunca com valor no código):
  IMAGETOOLS_API_URL  base da API, sem barra final
  IMAGETOOLS_API_KEY  chave de acesso (Bearer)
"""

import os
from pathlib import Path

TAGS = "stargate"
TIMEOUT_S = 600  # vídeos de dezenas de MB


class ImageToolsErro(Exception):
    """Falha de configuração ou de comunicação com o ImageTools."""


def configuracao():
    """(url_base, chave) vindos de os.environ; erro claro se faltar algo."""
    url = os.environ.get("IMAGETOOLS_API_URL", "").strip().rstrip("/")
    chave = os.environ.get("IMAGETOOLS_API_KEY", "").strip()
    faltam = [
        nome
        for nome, valor in (
            ("IMAGETOOLS_API_URL", url),
            ("IMAGETOOLS_API_KEY", chave),
        )
        if not valor
    ]
    if faltam:
        raise ImageToolsErro("Faltam variáveis de ambiente: " + ", ".join(faltam))
    return url, chave


def _http(metodo, url, chave, ficheiro=None):
    """ÚNICO ponto que toca a rede (os testes substituem-no). Devolve o JSON."""
    import httpx  # import tardio: só quem envia precisa dele

    cabecalhos = {"Authorization": f"Bearer {chave}"}
    try:
        if ficheiro is None:
            resp = httpx.request(metodo, url, headers=cabecalhos, timeout=60)
        else:
            with open(ficheiro, "rb") as f:
                resp = httpx.request(
                    metodo,
                    url,
                    headers=cabecalhos,
                    data={"tags": TAGS},
                    files={"file": (Path(ficheiro).name, f, "video/mp4")},
                    timeout=TIMEOUT_S,
                )
        resp.raise_for_status()
        return resp.json()
    except (httpx.HTTPError, ValueError, OSError) as exc:
        raise ImageToolsErro(f"ImageTools {metodo} {url} falhou: {exc}") from exc


def enviar_video(caminho):
    """Envia o vídeo e devolve `(uuid, file_url)`.

    Se a resposta do POST vier sem `file_url`, consulta `GET /api/v2/media/<uuid>/`.
    """
    base, chave = configuracao()
    dados = _http("POST", f"{base}/api/v2/media/", chave, ficheiro=caminho)
    uuid = str(dados.get("uuid") or "")
    if not uuid:
        raise ImageToolsErro("Resposta do ImageTools sem uuid.")
    url = dados.get("file_url") or ""
    if not url:
        dados = _http("GET", f"{base}/api/v2/media/{uuid}/", chave)
        url = dados.get("file_url") or ""
    if not url:
        raise ImageToolsErro(f"ImageTools não devolveu file_url (uuid {uuid}).")
    return uuid, url
