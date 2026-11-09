from django.contrib import admin

from .models import RegistroAccion


@admin.register(RegistroAccion)
class RegistroAccionAdmin(admin.ModelAdmin):
    """El registro de auditoría es de solo lectura: no se puede editar ni borrar."""

    list_display = ("fecha", "usuario", "accion", "objeto_tipo", "objeto_id", "direccion_ip")
    list_filter = ("accion",)
    search_fields = ("usuario__email", "descripcion")
    readonly_fields = [f.name for f in RegistroAccion._meta.fields]

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return False
