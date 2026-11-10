"""Gera e publica o áudio dos blocos, com retomada por conteúdo."""

import hashlib
import json
import os
import re
import tempfile
from pathlib import Path
from urllib.parse import quote

import httpx
from django.core.management.base import BaseCommand, CommandError

from core.servicos import imagetools


def duracao_mp3(caminho):
    """Soma a duração dos quadros MPEG Layer III, incluindo arquivos VBR."""
    dados = caminho.read_bytes()
    pos = 0
    if dados[:3] == b"ID3" and len(dados) >= 10:
        pos = 10 + sum((dados[6 + i] & 127) << (7 * (3 - i)) for i in range(4))
        if dados[5] & 16:
            pos += 10
    duracao = 0.0
    while pos + 4 <= len(dados):
        cab = int.from_bytes(dados[pos : pos + 4], "big")
        versao, camada = (cab >> 19) & 3, (cab >> 17) & 3
        taxa, frequencia = (cab >> 12) & 15, (cab >> 10) & 3
        if (
            cab >> 21 != 2047
            or versao == 1
            or camada != 1
            or taxa in (0, 15)
            or frequencia == 3
        ):
            pos += 1
            continue
        taxas = (
            (32, 40, 48, 56, 64, 80, 96, 112, 128, 160, 192, 224, 256, 320)
            if versao == 3
            else (8, 16, 24, 32, 40, 48, 56, 64, 80, 96, 112, 128, 144, 160)
        )
        hz = (44100, 48000, 32000)[frequencia] // (
            1 if versao == 3 else 2 if versao == 2 else 4
        )
        tamanho = (144 if versao == 3 else 72) * taxas[taxa - 1] * 1000 // hz + (
            (cab >> 9) & 1
        )
        if pos + tamanho > len(dados):
            break
        duracao += (1152 if versao == 3 else 576) / hz
        pos += tamanho
    if not duracao:
        raise ValueError("MP3 sem quadros válidos.")
    return round(duracao, 3)


def gravar_json(caminho, dados):
    caminho.parent.mkdir(parents=True, exist_ok=True)
    fd, temporario = tempfile.mkstemp(dir=caminho.parent, prefix=".audio-")
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as arquivo:
            json.dump(dados, arquivo, ensure_ascii=False, indent=2)
            arquivo.flush()
            os.fsync(arquivo.fileno())
        os.replace(temporario, caminho)
    finally:
        if os.path.exists(temporario):
            os.unlink(temporario)


def ler_json(caminho):
    dados = json.loads(caminho.read_text(encoding="utf-8"))
    if not isinstance(dados, dict):
        raise ValueError("O JSON deve ser um objeto.")
    return dados


class Command(BaseCommand):
    help = "Gera narrações e sons de um grafo e grava um manifesto de UUIDs."

    def add_arguments(self, parser):
        parser.add_argument("--grafo", required=True, type=Path)
        parser.add_argument("--saida", required=True, type=Path)
        parser.add_argument("--chaves", type=Path)
        parser.add_argument("--voz")
        parser.add_argument("--max-narracoes", type=int, default=0)
        parser.add_argument("--max-sons", type=int, default=0)
        parser.add_argument("--max-caracteres", type=int, default=0)
        parser.add_argument("--seco", action="store_true")

    def handle(self, *args, **op):
        try:
            self.executar(op)
        except (OSError, ValueError, imagetools.ImageToolsErro) as exc:
            # Nunca reproduzir respostas, URLs ou conteúdo do arquivo de chaves.
            raise CommandError(
                f"Configuração ou arquivo inválido ({type(exc).__name__})."
            ) from None

    def executar(self, op):
        grafo = ler_json(op["grafo"])
        serie = grafo.get("serie", "")
        if not isinstance(serie, str) or not re.fullmatch(r"[\w-]+", serie):
            raise ValueError("Série inválida.")
        blocos = grafo.get("blocos")
        if not isinstance(blocos, list):
            raise ValueError("Blocos inválidos.")
        ids = set()
        for bloco in blocos:
            if not isinstance(bloco, dict) or not isinstance(
                bloco.get("id"), (str, int)
            ):
                raise ValueError("Bloco sem ID.")
            identificador = str(bloco["id"])
            if identificador in ids:
                raise ValueError("ID duplicado.")
            ids.add(identificador)
            for campo in ("narracao", "som"):
                if bloco.get(campo) is not None and not isinstance(bloco[campo], str):
                    raise ValueError("Texto inválido.")
        limites = {"narracao": op["max_narracoes"], "som": op["max_sons"]}
        if min(*limites.values(), op["max_caracteres"]) < 0:
            raise ValueError("Os limites devem ser não negativos.")
        saida = op["saida"]
        cache_path = saida.with_name(saida.name + ".cache.json")
        cache = ler_json(cache_path) if cache_path.exists() else {}
        manifesto = {}
        chave = base = None
        if not op["seco"]:
            if not op["chaves"] or not op["voz"]:
                raise ValueError("Informe --chaves e --voz.")
            cred = ler_json(op["chaves"])
            chave, base = cred.get("api_key"), cred.get("base_url")
            if not isinstance(chave, str) or not chave.strip():
                raise ValueError("Chave ausente.")
            if not isinstance(base, str) or not base.startswith(
                ("https://", "http://")
            ):
                raise ValueError("Base inválida.")
            base = base.rstrip("/")
            imagetools.configuracao()
        tentativas = dict.fromkeys(limites, 0)
        gerados = acertos = erros = planejados = caracteres = 0
        pasta = saida.with_name(saida.name + ".audios")
        for bloco in blocos:
            item = dict.fromkeys(
                ("narracao_uuid", "som_uuid", "narracao_sha", "som_sha")
            )
            item["duracao"] = None
            manifesto[str(bloco["id"])] = item
            for tipo in limites:
                texto = bloco.get(tipo)
                if not texto or not texto.strip():
                    continue
                sha = hashlib.sha256(texto.encode("utf-8")).hexdigest()
                item[tipo + "_sha"] = sha
                # O hash é do texto; o contexto impede reutilizar outra voz ou tipo.
                contexto = f"{serie}:{tipo}:{op['voz'] if tipo == 'narracao' else '4s'}"
                entradas = cache.setdefault(contexto, {})
                salvo = entradas.get(sha, {})
                if salvo.get("uuid"):
                    item[tipo + "_uuid"] = salvo["uuid"]
                    if tipo == "narracao":
                        item["duracao"] = salvo.get("duracao")
                    acertos += 1
                    continue
                if (
                    tentativas[tipo] >= limites[tipo]
                    or caracteres + len(texto) > op["max_caracteres"]
                ):
                    continue
                tentativas[tipo] += 1
                caracteres += len(texto)
                if op["seco"]:
                    planejados += 1
                    continue
                arquivo = pasta / (
                    hashlib.sha256(contexto.encode()).hexdigest() + sha + ".mp3"
                )
                try:
                    if not arquivo.exists():
                        endpoint = (
                            "text-to-speech/" + quote(op["voz"], safe="")
                            if tipo == "narracao"
                            else "sound-generation"
                        )
                        corpo = {"text": texto}
                        corpo.update(
                            {"model_id": "eleven_multilingual_v2"}
                            if tipo == "narracao"
                            else {"duration_seconds": 4}
                        )
                        resp = httpx.post(
                            f"{base}/v1/{endpoint}",
                            headers={"xi-api-key": chave},
                            json=corpo,
                            timeout=120,
                        )
                        resp.raise_for_status()
                        if not resp.content:
                            raise ValueError("Áudio vazio.")
                        pasta.mkdir(parents=True, exist_ok=True)
                        temporario = arquivo.with_suffix(".tmp")
                        temporario.write_bytes(resp.content)
                        os.replace(temporario, arquivo)
                    uuid = imagetools.enviar_audio(arquivo, f"stargate/audio/{serie}/")
                    duracao = duracao_mp3(arquivo)
                    entradas[sha] = {"uuid": uuid, "duracao": duracao}
                    if tipo == "narracao":
                        item["duracao"] = duracao
                    gravar_json(cache_path, cache)
                    item[tipo + "_uuid"] = uuid
                    gerados += 1
                except (httpx.HTTPError, imagetools.ImageToolsErro, ValueError) as exc:
                    erros += 1
                    self.stderr.write(
                        f"Bloco {bloco['id']}, {tipo}: falha ({type(exc).__name__})."
                    )
            if not op["seco"]:
                gravar_json(saida, manifesto)
        if not op["seco"]:
            gravar_json(saida, manifesto)
        self.stdout.write(
            f"Resumo: {gerados} publicados; {acertos} em cache; "
            f"{erros} erros; {planejados} planejados (seco); {caracteres} caracteres."
        )
