from django.urls import path

from . import views

app_name = "notificaciones"

urlpatterns = [
    path("notificaciones/", views.lista, name="lista"),
    path("notificaciones/<int:pk>/abrir/", views.abrir, name="abrir"),
    path("notificaciones/marcar-leidas/", views.marcar_leidas, name="marcar_leidas"),
]
