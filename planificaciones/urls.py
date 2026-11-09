from django.urls import path

from . import views, views_admin, views_colaborador

app_name = "planificaciones"

urlpatterns = [
    # Catálogo (usuarios con sesión)
    path("ideas/", views.catalogo, name="catalogo"),
    path("ideas/<int:pk>/", views.detalle, name="detalle"),
    path("ideas/<int:pk>/planificacion/", views.visor, name="visor"),
    path("ideas/<int:pk>/planificacion/documento/", views.documento_pdf, name="documento"),
    # Profesional Colaborador/a
    path("colaborador/", views_colaborador.panel, name="panel_colaborador"),
    path("colaborador/propuestas/", views_colaborador.mis_propuestas, name="mis_propuestas"),
    path("colaborador/propuestas/nueva/", views_colaborador.crear_propuesta, name="crear_propuesta"),
    path("colaborador/propuestas/<int:pk>/editar/", views_colaborador.editar_propuesta, name="editar_propuesta"),
    path("colaborador/propuestas/<int:pk>/eliminar/", views_colaborador.eliminar_propuesta, name="eliminar_propuesta"),
    # Administrador/a
    path("administracion/propuestas/", views_admin.revision, name="admin_revision"),
    path("administracion/propuestas/<int:pk>/", views_admin.detalle_revision, name="admin_detalle"),
    path("administracion/propuestas/<int:pk>/accion/", views_admin.accion_revision, name="admin_accion"),
]
