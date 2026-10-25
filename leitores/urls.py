from django.urls import path

from . import views

app_name = "leitores"

urlpatterns = [
    path("conta/entrar/", views.Entrar.as_view(), name="entrar"),
    path("conta/sair/", views.Sair.as_view(), name="sair"),
    path("conta/criar/", views.criar, name="criar"),
]
