from django.urls import path

from . import views

app_name = "core"

urlpatterns = [
    path("", views.inicio, name="inicio"),
    path("administracion/", views.panel_admin, name="panel_admin"),
    path("administracion/auditoria/", views.auditoria, name="auditoria"),
]
