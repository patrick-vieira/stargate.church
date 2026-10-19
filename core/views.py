from django.http import JsonResponse

from noticias.views import home as home_noticias


def home(request):
    """A home é a das notícias; o nome `core:home` continua valendo."""
    return home_noticias(request)


def saude(request):
    return JsonResponse({"status": "ok"})
