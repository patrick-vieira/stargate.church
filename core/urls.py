from django.urls import path

from . import views

app_name = "core"

urlpatterns = [
    path("", views.home, name="home"),
    path("lab/spike/", views.lab_spike, name="lab_spike"),
    path("imersivo/<slug:slug>/", views.imersivo, name="imersivo"),
    path("series/<slug:serie>/", views.serie, name="serie"),
    path("series/<slug:serie>/<slug:episodio>/", views.episodio, name="episodio"),
    path("placar/voto/", views.placar_voto, name="placar_voto"),
    path("saude/", views.saude, name="saude"),
]
