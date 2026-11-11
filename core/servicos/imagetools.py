"""Cliente mínimo do ImageTools (S3 com API) para os vídeos dos episódios.

Autentica por cabeçalho `X-API-Key` com um `User-Agent` (o Bearer é recusado).

Configuração (nunca com valor no código), por ordem de precedência:
  IMAGETOOLS_API_URL / IMAGETOOLS_API_KEY  base da API (sem barra final) e chave
  IMAGETOOLS_CREDENCIAIS  caminho de um JSON com os campos `url` e `token`,
                          lido só para o que as variáveis acima não definem
"""

import json
import os
from pathlib import Path

TAGS = "stargate"
TIMEOUT_S = 600  # vídeos de dezenas de MB
USER_AGENT = "stargate.church/importar_midia"


class ImageToolsErro(Exception):
    """Falha de configuração ou de comunicação com o ImageTools."""


def _ler_credenciais(caminho):
    """(url, token) do JSON em `caminho`; nunca inclui o token nos erros."""
    try:
        dados = json.loads(Path(caminho).read_text())
    except (OSError, ValueError) as exc:
        raise ImageToolsErro(
            f"IMAGETOOLS_CREDENCIAIS não pôde ser lido ({type(exc).__name__})."
        ) from None
    if not isinstance(dados, dict):
        raise ImageToolsErro("IMAGETOOLS_CREDENCIAIS: o JSON deve ser um objeto.")
    url = str(dados.get("url") or "").strip().rstrip("/")
    token = str(dados.get("token") or "").strip()
    return url, token


def configuracao():
    """(url_base, chave): variáveis de ambiente, depois o JSON das credenciais."""
    url = os.environ.get("IMAGETOOLS_API_URL", "").strip().rstrip("/")
    chave = os.environ.get("IMAGETOOLS_API_KEY", "").strip()
    caminho = os.environ.get("IMAGETOOLS_CREDENCIAIS", "").strip()
    if caminho and not (url and chave):
        url_j, chave_j = _ler_credenciais(caminho)
        url = url or url_j
        chave = chave or chave_j
    faltam = [
        nome
        for nome, valor in (
            ("IMAGETOOLS_API_URL (ou `url` em IMAGETOOLS_CREDENCIAIS)", url),
            ("IMAGETOOLS_API_KEY (ou `token` em IMAGETOOLS_CREDENCIAIS)", chave),
        )
        if not valor
    ]
    if faltam:
        raise ImageToolsErro("Falta configurar: " + ", ".join(faltam))
    return url, chave


def _http(metodo, url, chave, ficheiro=None):
    """ÚNICO ponto que toca a rede (os testes substituem-no). Devolve o JSON."""
    import httpx  # import tardio: só quem envia precisa dele

    cabecalhos = {"X-API-Key": chave, "User-Agent": USER_AGENT}
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


def enviar_audio(caminho, pasta):
    """Publica um MP3 na pasta da série e retorna seu UUID."""
    import httpx

    base, chave = configuracao()
    try:
        with open(caminho, "rb") as arquivo:
            resp = httpx.request(
                "POST",
                f"{base}/api/v2/media/",
                headers={"X-API-Key": chave, "User-Agent": USER_AGENT},
                data={"tags": TAGS, "folder": pasta},
                files={"file": (Path(caminho).name, arquivo, "audio/mpeg")},
                timeout=TIMEOUT_S,
            )
        resp.raise_for_status()
        uuid = resp.json().get("uuid")
        if not isinstance(uuid, str) or not uuid:
            raise ValueError("Resposta sem uuid.")
        return uuid
    except (httpx.HTTPError, ValueError, OSError) as exc:
        raise ImageToolsErro(f"Falha ao enviar áudio ({type(exc).__name__}).") from None
