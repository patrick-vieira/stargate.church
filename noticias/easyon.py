"""Cliente fino da API do EasyON (agentes alugados).

O contrato é PROVISÓRIO (a API E2/E3 ainda não existe) e vive só aqui:
  GET  agentes/                -> [{"slug", "nome", "voz"}, ...]
  POST agentes/<slug>/audio/   -> {"url": ..., "cache": bool}   (corpo {"texto": ...})
A chave lê-se de um ficheiro em modo 600 e nunca aparece em logs nem em repr.
"""

import json
import stat
import urllib.request
from pathlib import Path

from django.conf import settings

TIMEOUT = 5


class EasyONIndisponivel(Exception):
    """A API não está configurada, não responde ou respondeu mal."""


def _ler_chave(caminho):
    if not caminho:
        raise EasyONIndisponivel("EASYON_API_KEY_FILE não está configurado.")
    ficheiro = Path(caminho)
    try:
        modo = stat.S_IMODE(ficheiro.stat().st_mode)
    except OSError:
        raise EasyONIndisponivel("Ficheiro da chave do EasyON ilegível.") from None
    if modo != 0o600:
        raise EasyONIndisponivel(
            f"Ficheiro da chave do EasyON recusado: modo {modo:o}, esperado 600."
        )
    chave = ficheiro.read_text().strip()
    if not chave:
        raise EasyONIndisponivel("Ficheiro da chave do EasyON está vazio.")
    return chave


def _transporte_urllib(metodo, url, cabecalhos, corpo, timeout):
    dados = None if corpo is None else json.dumps(corpo).encode()
    pedido = urllib.request.Request(url, data=dados, headers=cabecalhos, method=metodo)
    with urllib.request.urlopen(pedido, timeout=timeout) as resposta:  # noqa: S310
        return json.loads(resposta.read().decode())


class ClienteEasyON:
    def __init__(self, url=None, chave_ficheiro=None, transporte=None):
        self.url = (url if url is not None else settings.EASYON_API_URL).rstrip("/")
        self._chave_ficheiro = (
            chave_ficheiro
            if chave_ficheiro is not None
            else settings.EASYON_API_KEY_FILE
        )
        self._transporte = transporte or _transporte_urllib

    def __repr__(self):
        return f"<ClienteEasyON url={self.url!r}>"

    def _pedir(self, metodo, caminho, corpo=None):
        if not self.url:
            raise EasyONIndisponivel("EASYON_API_URL não está configurado.")
        chave = _ler_chave(self._chave_ficheiro)
        cabecalhos = {
            "Authorization": f"Bearer {chave}",
            "Accept": "application/json",
            "Content-Type": "application/json",
        }
        try:
            return self._transporte(
                metodo, f"{self.url}/{caminho}", cabecalhos, corpo, TIMEOUT
            )
        except EasyONIndisponivel:
            raise
        except Exception as erro:  # rede, HTTP, JSON: nunca propagar a chave
            raise EasyONIndisponivel(
                f"EasyON indisponível ({type(erro).__name__})."
            ) from None

    def agentes(self):
        return self._pedir("GET", "agentes/")

    def gerar_audio(self, slug, texto):
        resposta = self._pedir("POST", f"agentes/{slug}/audio/", {"texto": texto})
        if not isinstance(resposta, dict) or not resposta.get("url"):
            raise EasyONIndisponivel("Resposta do EasyON sem URL de áudio.")
        return resposta
