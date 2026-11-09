from django.contrib import admin

from .models import SolicitudColaborador


@admin.register(SolicitudColaborador)
class SolicitudColaboradorAdmin(admin.ModelAdmin):
    list_display = ("usuario", "titulo_profesional", "institucion", "anio_titulacion", "estado", "fecha_solicitud")
    list_filter = ("estado",)
    search_fields = ("usuario__email", "usuario__rut", "titulo_profesional", "institucion")
    readonly_fields = ("documento_respaldo", "nombre_archivo", "fecha_solicitud", "fecha_resolucion")
