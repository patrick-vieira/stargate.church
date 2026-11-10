"""Escolha do envelope visual; posts imersivos mantêm sua própria atmosfera."""

from django.utils.cache import patch_vary_headers

ESTILOS = {"0": "Original", "3": "Noite estrelada", "5": "Bloco"}
COOKIE = "stargate_estilo"


def estilo_do_leitor(request):
    escolha = request.GET.get("estilo")
    if escolha not in ESTILOS:
        escolha = request.COOKIES.get(COOKIE, "3")
    return escolha if escolha in ESTILOS else "3"


def envelope(request):
    estilo = estilo_do_leitor(request)
    opcoes = []
    for valor, nome in ESTILOS.items():
        parametros = request.GET.copy()
        parametros["estilo"] = valor
        opcoes.append(
            {"valor": valor, "nome": nome, "url": "?" + parametros.urlencode()}
        )
    return {
        "estilo_base": estilo,
        "estilos_base": opcoes,
        "convite_estilo": COOKIE not in request.COOKIES
        and request.COOKIES.get("stargate_convite") != "fechado"
        and "estilo" not in request.GET,
        "outro_estilo": opcoes[2] if estilo != "5" else opcoes[1],
    }


class PreferenciaEstiloMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        response = self.get_response(request)
        patch_vary_headers(response, ("Cookie",))
        escolha = request.GET.get("estilo")
        if escolha in ESTILOS and response.status_code == 200:
            response.set_cookie(
                COOKIE,
                escolha,
                max_age=31536000,
                samesite="Lax",
                secure=request.is_secure(),
            )
            # Uma resposta personalizada não deve entrar num cache compartilhado.
            response["Cache-Control"] = "private"
        return response
