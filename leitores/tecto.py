"""Tecto diário por utilizador e tipo (conversa, comentário)."""

from functools import wraps

from django.conf import settings
from django.db import IntegrityError, transaction
from django.db.models import F
from django.http import JsonResponse
from django.utils import timezone

from .models import UsoDiario


def limite(tipo: str) -> int:
    if tipo == UsoDiario.CONVERSA:
        return settings.STARGATE_TECTO_CONVERSA
    if tipo == UsoDiario.COMENTARIO:
        return settings.STARGATE_TECTO_COMENTARIO
    raise ValueError(f"tipo desconhecido: {tipo}")


def _hoje():
    return timezone.localdate()


def restante(utilizador, tipo: str) -> int:
    teto = limite(tipo)
    if not getattr(utilizador, "is_authenticated", False):
        return 0
    uso = UsoDiario.objects.filter(
        utilizador=utilizador, dia=_hoje(), tipo=tipo
    ).first()
    return max(teto - (uso.quantidade if uso else 0), 0)


def consumir(utilizador, tipo: str) -> bool:
    """Gasta 1 do tecto de hoje. Falso se o tecto já foi atingido ou se é anónimo."""
    teto = limite(tipo)
    if not getattr(utilizador, "is_authenticated", False):
        return False
    dia = _hoje()
    with transaction.atomic():
        try:
            with transaction.atomic():
                UsoDiario.objects.get_or_create(
                    utilizador=utilizador, dia=dia, tipo=tipo
                )
        except IntegrityError:
            pass
        # A linha fica bloqueada até ao fim da transação; o UPDATE é feito com F().
        linha = UsoDiario.objects.select_for_update().get(
            utilizador=utilizador, dia=dia, tipo=tipo
        )
        if linha.quantidade >= teto:
            return False
        UsoDiario.objects.filter(pk=linha.pk).update(quantidade=F("quantidade") + 1)
        return True


def exige_tecto(tipo: str):
    """Decorador para as views do F3: 401 ao anónimo, 429 quando o tecto acabou."""

    def decorador(view):
        @wraps(view)
        def envolvida(request, *args, **kwargs):
            if not request.user.is_authenticated:
                return JsonResponse({"erro": "login"}, status=401)
            if not consumir(request.user, tipo):
                return JsonResponse({"erro": "tecto"}, status=429)
            return view(request, *args, **kwargs)

        return envolvida

    return decorador
