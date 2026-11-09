from django.urls import path

from . import views

app_name = "noticias"

urlpatterns = [
    path("noticias/", views.home, name="home"),
    path("tema/<slug:slug>/", views.tema, name="tema"),
    path("artigo/<slug:slug>/", views.artigo, name="artigo"),
    path("artigo/<slug:slug>/comentar/", views.comentar, name="comentar"),
]
