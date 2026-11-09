"""
Control de acceso por rol (autorización en el servidor).

Ocultar un botón en el HTML no es seguridad: cualquiera puede escribir la URL.
Por eso cada vista protegida usa uno de estos decoradores:

    @administrador_requerido
    def panel_admin(request): ...

- Sin sesión iniciada  -> redirige al login.
- Con sesión, sin rol  -> error 403 (Prohibido).
"""

from functools import wraps

from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied

from .models import Usuario


def rol_requerido(*roles):
    def decorador(vista):
        @wraps(vista)
        def envoltura(request, *args, **kwargs):
            usuario = request.user
            es_admin_valido = usuario.is_superuser and Usuario.Rol.ADMINISTRADOR in roles
            if usuario.rol in roles or es_admin_valido:
                return vista(request, *args, **kwargs)
            raise PermissionDenied("No tienes permisos para acceder a esta sección.")

        return login_required(envoltura)

    return decorador


administrador_requerido = rol_requerido(Usuario.Rol.ADMINISTRADOR)
colaborador_requerido = rol_requerido(Usuario.Rol.COLABORADOR)
educador_requerido = rol_requerido(Usuario.Rol.EDUCADOR)
# Favoritos, valoraciones y comentarios
interaccion_requerida = rol_requerido(Usuario.Rol.EDUCADOR, Usuario.Rol.COLABORADOR)
