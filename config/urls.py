"""
Rutas principales de Idearia.

Cada aplicación declara sus propias rutas completas en su archivo urls.py.
Las rutas que comienzan con "administracion/" exigen rol Administrador
(se valida en cada vista, no solo ocultando botones).
"""

from django.conf import settings
from django.contrib import admin
from django.urls import include, path

admin.site.site_header = "Idearia - Administración técnica"
admin.site.site_title = "Idearia"

urlpatterns = [
    # Admin técnico de Django (solo superusuarios). La ruta se define en .env
    path(settings.ADMIN_URL, admin.site.urls),
    path("", include("core.urls")),
    path("", include("usuarios.urls")),
    path("", include("planificaciones.urls")),
    path("", include("colaboradores.urls")),
    path("", include("interacciones.urls")),
    path("", include("notificaciones.urls")),
]
