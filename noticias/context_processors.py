from . import servicos


def portal(request):
    """Dados do cabeçalho e do rodapé, presentes em todas as páginas."""
    return {"hoje": servicos.hoje(), "temas_menu": servicos.temas_do_menu()}
