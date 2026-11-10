import json

from django.db.models import Prefetch
from django.http import Http404, JsonResponse
from django.middleware.csrf import get_token
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.views.decorators.http import require_POST

from leitores.tecto import exige_tecto

from . import placar
from .imersivo import libs_opcionais
from .models import Ato, Episodio, PostImersivo, Serie, VotoPlacar

# Efeito de página inteira → template próprio (STAR-41, STAR-42).
TEMPLATES_ATMOSFERA = {
    Ato.Efeito.ATMOSFERA: "core/imersivo_maquina_fria.html",
    Ato.Efeito.ATMOSFERA_GUERRA: "core/imersivo_guerra_maquinas.html",
    Ato.Efeito.ATMOSFERA_SER_HUMANO: "core/imersivo_ser_humano.html",
    Ato.Efeito.ATMOSFERA_ESCOLHAS: "core/imersivo_escolhas.html",
    Ato.Efeito.ATMOSFERA_IA_AFETIVA: "core/imersivo_ia_afetiva.html",
    Ato.Efeito.ATMOSFERA_LEIS_ROBOS_LIVROS: "core/imersivo_leis_robos_livros.html",
    Ato.Efeito.ATMOSFERA_PLACAR: "core/imersivo_placar.html",
    Ato.Efeito.ATMOSFERA_QUASE_PRESENTE: "core/imersivo_quase_presente.html",
    Ato.Efeito.ATMOSFERA_HUB: "core/imersivo_hub.html",
}


# Era do narrador (0 1920, 1 1960, 2 1980, 3 1990, 4 2000, 5 2010, 6 2020) por post.
# Posts fora da tabela ficam na era 6 (creme Stargate).
ERA_NARRADOR = {
    "a-maquina-fria": 1,
    "efeitos-maquina-fria-provisorio": 1,
    "o-medo-da-guerra-das-maquinas": 2,
    "escolhas-da-maquina": 5,
    "o-que-e-ser-humano": 3,
    "a-ia-afetiva": 5,
    "leis-robos-e-livros": 0,
    "o-placar": 6,
}


def home(request):
    """Portal das séries (STAR-58); as notícias vivem em /noticias/."""
    episodios = Episodio.objects.filter(publicado=True, post__publicado=True)
    series = Serie.objects.filter(publicado=True).select_related("hub")
    series = series.prefetch_related(
        Prefetch("episodios", queryset=episodios, to_attr="episodios_publicados")
    )
    return render(request, "core/portal.html", {"series": series})


def saude(request):
    return JsonResponse({"status": "ok"})


def lab_spike(request):
    """Página de prova do STAR-19: WebGL, Rive e diagrama ao scroll (laboratório)."""
    return render(request, "core/lab_spike.html")


def _midia(post, serie, episodio):
    """Mídia embutida da página: vídeo/áudio do episódio, ou trailer no hub."""
    if episodio is not None and episodio.tem_midia:
        return {
            "titulo": episodio.titulo or post.titulo,
            "video": episodio.video,
            "vertical": episodio.video_vertical,
            "poster": episodio.poster,
            "audio": episodio.audio,
            "audio_ogg": episodio.audio_ogg,
            "legenda": episodio.legenda,
            "transcricao": episodio.transcricao,
        }
    if serie is not None and serie.hub_id == post.id and serie.trailer:
        return {
            "titulo": f"Trailer — {serie.titulo}",
            "video": serie.trailer,
            "poster": serie.trailer_poster,
            "legenda": serie.trailer_legenda,
        }
    return None


def _renderizar_post(request, post, serie=None, episodio=None):
    """Post imersivo: atos em dados, efeitos pelo motor JS."""
    atos = list(post.atos.all())
    urls = {}
    if serie is not None:
        episodios = serie.episodios.filter(
            publicado=True, post__publicado=True
        ).select_related("serie")
        urls = {e.slug: e.get_absolute_url() for e in episodios}
    lista = []
    comecar = None
    if serie is not None:
        for e in serie.episodios.exclude(numero=0).select_related("post"):
            url = urls.get(e.slug) if e.post_id else None
            lista.append(
                {
                    "numero": e.numero,
                    "titulo": e.titulo or (e.post.titulo if e.post_id else e.slug),
                    "slug": e.slug,
                    "url": url,
                }
            )
            if e.numero == 1:
                comecar = url
    for a in atos:
        a.urls_episodios = urls
        a.episodios_serie = lista
        a.comecar_url = comecar
    contexto = {
        "post": post,
        "atos": atos,
        "serie": serie,
        "n_posts": len(lista),
        "episodio": episodio,
        "midia": _midia(post, serie, episodio),
        "libs": libs_opcionais(),
        "narrador_era": ERA_NARRADOR.get(post.slug, 6),
    }
    for a in atos:
        if a.efeito == Ato.Efeito.ATMOSFERA_PLACAR:
            contexto.update(_contexto_placar(request))
        if a.efeito == Ato.Efeito.ATMOSFERA_HUB:
            # Cartões «Entrar →» só para posts publicados; os outros dizem «Em breve».
            contexto["publicados"] = set(
                PostImersivo.publicados().values_list("slug", flat=True)
            )
        if a.efeito in TEMPLATES_ATMOSFERA:
            return render(request, TEMPLATES_ATMOSFERA[a.efeito], contexto)
    return render(request, "core/imersivo.html", contexto)


def _contexto_placar(request):
    """Obras, médias reais dos leitores e estado do voto para a página do placar."""
    # Garante o cookie csrftoken: o JS envia o voto com o cabeçalho X-CSRFToken.
    get_token(request)
    logado = request.user.is_authenticated
    meus = {}
    if logado:
        meus = {
            v.obra: [v.proximidade, v.preocupacao]
            for v in VotoPlacar.objects.filter(utilizador=request.user)
        }
    obras = placar.obras()
    medias = placar.medias()
    return {
        "placar": obras,
        "placar_dados": {
            "obras": obras,
            "medias": medias,
            "meus": meus,
            "logado": logado,
            "voto_url": reverse("core:placar_voto"),
        },
        "placar_logado": logado,
        "placar_total_votos": sum(m["n"] for m in medias.values()),
    }


def _ler_voto(request):
    """Lê (obra, proximidade, preocupacao) do corpo (JSON ou form); None se inválido."""
    if request.content_type == "application/json":
        try:
            bruto = json.loads(request.body or b"{}")
        except ValueError:
            return None
        if not isinstance(bruto, dict):
            return None
    else:
        bruto = request.POST
    obra = bruto.get("obra")
    if not isinstance(obra, str) or placar.obra(obra) is None:
        return None
    notas = []
    for chave in ("proximidade", "preocupacao"):
        v = bruto.get(chave)
        if isinstance(v, bool):
            return None
        if isinstance(v, str) and v.isascii() and v.isdigit():
            v = int(v)
        if not isinstance(v, int) or not 0 <= v <= 5:
            return None
        notas.append(v)
    return obra, notas[0], notas[1]


@exige_tecto("voto")
def _gravar_voto(request, obra, proximidade, preocupacao):
    VotoPlacar.objects.update_or_create(
        utilizador=request.user,
        obra=obra,
        defaults={"proximidade": proximidade, "preocupacao": preocupacao},
    )
    return JsonResponse(
        {"obra": obra, "voto": [proximidade, preocupacao], **placar.media_da_obra(obra)}
    )


@require_POST
def placar_voto(request):
    """Voto do leitor numa obra do placar (STAR-48), com o tecto diário «voto».

    O pedido é validado ANTES de gastar o tecto: obra desconhecida ou nota fora de
    0..5 dá 400 e não consome nada. O anónimo recebe 401 (decidido no tecto) e o
    tecto esgotado 429. Votar de novo na mesma obra atualiza o voto, sem linha nova.
    """
    voto = _ler_voto(request)
    if voto is None and request.user.is_authenticated:
        return JsonResponse({"erro": "voto inválido"}, status=400)
    if voto is None:
        return JsonResponse({"erro": "login"}, status=401)
    return _gravar_voto(request, *voto)


def imersivo(request, slug):
    """Rota antiga: 301 para a rota da série; sem série, serve o post (legado)."""
    post = get_object_or_404(PostImersivo.publicados(), slug=slug)
    serie_hub = Serie.objects.filter(publicado=True, hub=post).first()
    if serie_hub is not None:
        return redirect(serie_hub.get_absolute_url(), permanent=True)
    episodio = (
        Episodio.objects.filter(post=post, publicado=True, serie__publicado=True)
        .select_related("serie")
        .first()
    )
    if episodio is not None:
        return redirect(episodio.get_absolute_url(), permanent=True)
    return _renderizar_post(request, post)


def serie(request, serie):
    """Página da série: renderiza o hub (STAR-40)."""
    obj = get_object_or_404(Serie.objects.filter(publicado=True), slug=serie)
    if obj.hub is None or not obj.hub.publicado:
        raise Http404("Série sem página.")
    ep0 = Episodio.objects.filter(serie=obj, post=obj.hub, publicado=True).first()
    return _renderizar_post(request, obj.hub, obj, ep0)


def episodio(request, serie, episodio):
    """Episódio da série: renderiza o post imersivo ligado."""
    obj = get_object_or_404(
        Episodio.objects.select_related("serie", "post"),
        serie__slug=serie,
        serie__publicado=True,
        slug=episodio,
        publicado=True,
    )
    if obj.post is None or not obj.post.publicado:
        raise Http404("Episódio sem conteúdo.")
    if obj.post_id == obj.serie.hub_id:
        return redirect(obj.serie.get_absolute_url(), permanent=True)
    return _renderizar_post(request, obj.post, obj.serie, obj)
