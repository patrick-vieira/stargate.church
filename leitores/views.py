from django.contrib.auth import login
from django.contrib.auth.views import LoginView, LogoutView
from django.shortcuts import redirect, render

from .forms import CriarContaForm


class Entrar(LoginView):
    template_name = "leitores/entrar.html"
    redirect_authenticated_user = True


class Sair(LogoutView):
    """Só POST (o Django já recusa GET)."""


def criar(request):
    if request.user.is_authenticated:
        return redirect("core:home")
    form = CriarContaForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        login(request, form.guardar())
        return redirect("core:home")
    return render(request, "leitores/criar.html", {"form": form})
