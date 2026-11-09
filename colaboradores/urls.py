from django.urls import path

from . import views

app_name = "colaboradores"

urlpatterns = [
    path("zona-colaborador/", views.informacion, name="informacion"),
    path("colaborador/acreditacion/", views.mi_solicitud, name="mi_solicitud"),
    path("colaborador/acreditacion/nueva/", views.nueva_solicitud, name="nueva_solicitud"),
    path("colaborador/acreditacion/<int:pk>/documento/", views.documento, name="documento"),
    path("administracion/solicitudes/", views.admin_lista, name="admin_lista"),
    path("administracion/solicitudes/<int:pk>/", views.admin_detalle, name="admin_detalle"),
    path("administracion/solicitudes/<int:pk>/resolver/", views.admin_resolver, name="admin_resolver"),
]
