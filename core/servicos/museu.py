"""Validação e adaptação do grafo editorial, sem acesso a rede ou banco."""

import copy
import json
import re
from pathlib import Path
from urllib.parse import urlsplit

from django.core.exceptions import ValidationError

TIPOS = ("seguir", "aprofundar", "subir", "otimista", "catastrofico")
POLOS = {"neutro": 0, "otimista": 1, "catastrofico": -1}


def validar_grafo(dados):
    def falha(mensagem):
        raise ValidationError(mensagem)

    if (
        not isinstance(dados, dict)
        or not isinstance(dados.get("serie"), str)
        or not re.fullmatch(r"[-a-zA-Z0-9_]+", dados["serie"])
    ):
        falha("Série inválida.")
    blocos = dados.get("blocos")
    if not isinstance(blocos, list) or not blocos:
        falha("O grafo precisa de blocos.")
    nos = {}
    numeros = set()
    for n in blocos:
        if not isinstance(n, dict) or type(n.get("id")) is not int or n["id"] <= 0:
            falha("ID de bloco inválido.")
        if n["id"] in nos:
            falha("IDs repetidos.")
        nos[n["id"]] = n
        if (
            type(n.get("numero")) is not int
            or n["numero"] <= 0
            or n["numero"] in numeros
        ):
            falha("Número de bloco inválido ou repetido.")
        numeros.add(n["numero"])
        if n.get("tipo") not in (
            "texto",
            "video",
            "personagem",
            "texto que se expande",
            "camadas",
            "dialogo",
        ):
            falha("Tipo de bloco inválido.")
        if (
            not isinstance(n.get("polo"), str)
            or n.get("polo") not in POLOS
            or type(n.get("profundidade")) is not int
            or not 0 <= n["profundidade"] <= 20
        ):
            falha("Polo ou profundidade inválidos.")
        for campo in ("titulo", "texto"):
            if not isinstance(n.get(campo), str) or not n[campo].strip():
                falha("Título e texto são obrigatórios.")
        for campo in ("visual", "som", "narracao"):
            if campo in n and not isinstance(n[campo], str):
                falha("Notas editoriais devem ser texto.")
        if not isinstance(n.get("fontes", []), list):
            falha("Fontes devem ser uma lista.")
        for fonte in n.get("fontes", []):
            if (
                not isinstance(fonte, dict)
                or not isinstance(fonte.get("titulo"), str)
                or not isinstance(fonte.get("url"), str)
                or urlsplit(fonte["url"]).scheme not in ("http", "https")
            ):
                falha("Fonte inválida.")
        uuid = n.get("video_imagetools_uuid", "")
        if not isinstance(uuid, str) or (
            uuid and not re.fullmatch(r"[a-zA-Z0-9-]{1,64}", uuid)
        ):
            falha("Identificador de vídeo inválido.")
        if "camadas" in n:
            if (
                not isinstance(n["camadas"], list)
                or not n["camadas"]
                or any(
                    not isinstance(c, dict)
                    or not all(
                        isinstance(c.get(k), str) and c[k].strip()
                        for k in ("rotulo", "texto")
                    )
                    for c in n["camadas"]
                )
            ):
                falha("Camadas inválidas.")
        if "dialogo" in n:
            d = n["dialogo"]
            if (
                not isinstance(d, dict)
                or not isinstance(d.get("personagem"), dict)
                or not all(
                    isinstance(d["personagem"].get(k), str) for k in ("nome", "papel")
                )
                or not isinstance(d.get("falas"), list)
                or not all(isinstance(t, str) for t in d["falas"])
                or not isinstance(d.get("respostas"), list)
                or not d["respostas"]
            ):
                falha("Diálogo inválido.")
            if any(
                not isinstance(r, dict)
                or type(r.get("vai")) is not int
                or not isinstance(r.get("texto"), str)
                for r in d["respostas"]
            ):
                falha("Respostas inválidas.")
        if (
            n["tipo"] == "camadas"
            and "camadas" not in n
            or n["tipo"] == "dialogo"
            and "dialogo" not in n
        ):
            falha("Peça incompleta.")
        escolhas = n.get("escolhas")
        if not isinstance(escolhas, list) or not escolhas:
            falha("Todo bloco precisa de saída.")
        usados = set()
        for e in escolhas:
            if (
                not isinstance(e, dict)
                or not isinstance(e.get("tipo"), str)
                or e.get("tipo") not in TIPOS
                or e["tipo"] in usados
                or type(e.get("destino")) is not int
                or not isinstance(e.get("rotulo"), str)
                or not e["rotulo"].strip()
            ):
                falha("Escolha inválida ou repetida.")
            usados.add(e["tipo"])
    for n in blocos:
        if any(r["vai"] not in nos for r in n.get("dialogo", {}).get("respostas", [])):
            falha("Destino de diálogo inexistente.")
        for e in n["escolhas"]:
            if e["destino"] not in nos:
                falha("Destino inexistente.")
            destino = nos[e["destino"]]
            if (
                e["tipo"] == "aprofundar"
                and destino["profundidade"] <= n["profundidade"]
                or e["tipo"] == "subir"
                and destino["profundidade"] >= n["profundidade"]
            ):
                falha("Escolha incompatível com a profundidade.")
            if (
                e["tipo"] in ("otimista", "catastrofico")
                and destino["polo"] != e["tipo"]
            ):
                falha("Escolha incompatível com o polo.")
    vistos, fila = set(), [blocos[0]["id"]]
    while fila:
        atual = fila.pop()
        if atual not in vistos:
            vistos.add(atual)
            fila.extend(e["destino"] for e in nos[atual]["escolhas"])
            fila.extend(
                r["vai"] for r in nos[atual].get("dialogo", {}).get("respostas", [])
            )
    if vistos != set(nos):
        falha("Há blocos inalcançáveis.")
    return dados


def apresentar(serie, dados):
    """O conteúdo editorial permanece no servidor; o cliente recebe só o publicado."""
    nos = []
    for n in dados["blocos"]:
        texto = [p for p in n["texto"].split("\n\n") if p.strip()]
        nivel = n["profundidade"]
        tipo = (
            "camadas"
            if n["tipo"] == "texto que se expande"
            else n["tipo"]
            if n["tipo"] in ("camadas", "dialogo")
            else "texto"
        )
        no = dict(
            n,
            serie=serie.slug,
            num=n["numero"],
            nivel=nivel,
            polo=POLOS[n["polo"]],
            texto=texto,
            tipo=tipo,
            sala=f"nivel-{nivel}",
            ligacoes={t: None for t in TIPOS},
            mock=True,
        )
        for e in n["escolhas"]:
            no["ligacoes"][e["tipo"]] = e["destino"]
        no["fontes"] = [
            dict(
                f,
                veiculo=f.get("veiculo", f["titulo"]),
                data=f.get("data", ""),
                verificada=f.get("verificada", False),
            )
            for f in n.get("fontes", [])
        ]
        no["rotulos"] = {e["tipo"]: e["rotulo"] for e in n["escolhas"]}
        if tipo == "camadas" and "camadas" not in n:
            no["camadas"] = [
                {"rotulo": f"Camada {i + 1}", "texto": t} for i, t in enumerate(texto)
            ]
        if n["tipo"] == "video":
            no["tipo"] = "video"
            no["video"] = {
                "src": "",
                "poster": "",
                "track": "",
                "legenda": "Vídeo em preparação. O texto permanece disponível.",
                "endpoint": f"/museu/{serie.slug}/video/{n['id']}/"
                if n.get("video_imagetools_uuid")
                else "",
            }
        nos.append(no)
    salas = [
        {
            "id": f"nivel-{i}",
            "nome": f"Sala de aprofundamento {i}",
            "contexto": "[MOCK] Explore os caminhos e compare perspectivas.",
            "tema": {"cor": "#9a7458", "luz": "#f4d6a0", "textura": "paineis"},
        }
        for i in sorted({n["profundidade"] for n in dados["blocos"]})
    ]
    visitas = [
        {
            "id": "editorial",
            "nome": "[MOCK] Visita pelo museu",
            "passos": [n["id"] for n in nos],
            "segundos_por_passo": 20,
        }
    ]
    if serie.slug == "mock-energia-sem-fim":
        salas, visitas = integrar_extras(nos)
    return {
        "series": [
            {
                "slug": serie.slug,
                "titulo": serie.titulo,
                "resumo": serie.resumo,
                "mock": True,
                "episodios": [],
            }
        ],
        "noticias": [],
        "grafo": {
            "serie": serie.slug,
            "titulo": serie.titulo,
            "entrada": nos[0]["id"],
            "nos": nos,
            "salas": salas,
            "visitas": visitas,
        },
    }


def integrar_extras(nos):
    """Funde apenas apresentação; os dados editoriais persistidos não mudam.

    O editorial ganhou o ID 24. Essa peça da v3 é omitida e suas referências
    continuam apontando ao bloco editorial 24. As quatro outras peças mantêm ID.
    """
    extras = json.loads(
        (Path(__file__).resolve().parent.parent / "dados/museu_extras.json").read_text(
            encoding="utf-8"
        )
    )
    por_id = {n["id"]: n for n in nos}
    for n in nos:
        n["sala"] = extras["atribuicoes"].get(str(n["id"]), "futuros")
    for original in extras["nos"]:
        if original["id"] in por_id:
            continue
        no = copy.deepcopy(original)
        no.update(mock=True, fontes=[], narracao="", numero=no["id"], num=no["id"])
        no["rotulos"] = {
            t: f"Continuar para a peça {v}"
            for t, v in no["ligacoes"].items()
            if v is not None
        }
        no["escolhas"] = [
            {"tipo": t, "destino": v, "rotulo": no["rotulos"][t]}
            for t, v in no["ligacoes"].items()
            if v is not None
        ]
        nos.append(no)
        por_id[no["id"]] = no
    # Uma saída de apresentação própria evita substituir o 'seguir' editorial.
    entrada = por_id.get(21) or nos[0]
    entrada["ligacoes"]["museu"] = 27
    entrada["rotulos"]["museu"] = "Explorar as peças do museu"
    entrada["escolhas"] = [
        *entrada["escolhas"],
        {"tipo": "museu", "destino": 27, "rotulo": "Explorar as peças do museu"},
    ]
    vistos, fila = set(), [nos[0]["id"]]
    while fila:
        atual = fila.pop()
        if atual in vistos:
            continue
        if atual not in por_id:
            raise ValidationError("Destino de apresentação inexistente.")
        vistos.add(atual)
        no = por_id[atual]
        fila.extend(v for v in no["ligacoes"].values() if v is not None)
        fila.extend(r["vai"] for r in no.get("dialogo", {}).get("respostas", []))
    if vistos != set(por_id):
        raise ValidationError("Peça de apresentação inalcançável.")
    visitas = copy.deepcopy(extras["visitas"])
    for visita in visitas:
        visita["passos"] = [p for p in visita["passos"] if p in por_id]
    return extras["salas"], visitas
