from django.contrib import admin
from django.contrib.auth.admin import UserAdmin

from .forms import UsuarioCambioAdminForm, UsuarioCreacionAdminForm
from .models import Usuario


@admin.register(Usuario)
class UsuarioAdmin(UserAdmin):
    """Admin técnico adaptado: no existe "username", se usa el correo."""

    form = UsuarioCambioAdminForm
    add_form = UsuarioCreacionAdminForm
    list_display = ("email", "first_name", "last_name", "rut", "rol", "is_active", "date_joined")
    list_filter = ("rol", "is_active", "is_staff")
    search_fields = ("email", "first_name", "last_name", "rut")
    ordering = ("-date_joined",)
    fieldsets = (
        (None, {"fields": ("email", "password")}),
        ("Datos personales", {"fields": ("first_name", "last_name", "rut", "fecha_nacimiento")}),
        ("Rol y estado", {"fields": ("rol", "is_active", "is_staff", "is_superuser")}),
        ("Fechas", {"fields": ("last_login", "date_joined")}),
    )
    add_fieldsets = (
        (
            None,
            {
                "classes": ("wide",),
                "fields": ("email", "first_name", "last_name", "rut", "rol", "password1", "password2"),
            },
        ),
    )
