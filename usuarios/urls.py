from django.urls import path

from . import views

app_name = "usuarios"

urlpatterns = [
    path("ingresar/", views.IngresarView.as_view(), name="login"),
    path("salir/", views.SalirView.as_view(), name="logout"),
    path("registro/", views.registro, name="registro"),
    path("administracion/usuarios/", views.admin_lista, name="admin_lista"),
    path(
        "administracion/usuarios/<int:pk>/estado/",
        views.admin_cambiar_estado,
        name="admin_cambiar_estado",
    ),
]
