from django.urls import path

from . import views

app_name = "noticias"

urlpatterns = [
    path("tema/<slug:slug>/", views.tema, name="tema"),
    path("artigo/<slug:slug>/", views.artigo, name="artigo"),
]
