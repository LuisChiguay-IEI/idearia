"""Funciones para crear notificaciones desde cualquier parte del sistema (RF-17)."""

from usuarios.models import Usuario

from .models import Notificacion


def notificar(usuario, tipo, mensaje, enlace=""):
    return Notificacion.objects.create(usuario=usuario, tipo=tipo, mensaje=mensaje, enlace=enlace)


def notificar_administradores(tipo, mensaje, enlace=""):
    """Envía la misma notificación a todos los administradores activos."""
    administradores = Usuario.objects.filter(rol=Usuario.Rol.ADMINISTRADOR, is_active=True)
    Notificacion.objects.bulk_create(
        [Notificacion(usuario=a, tipo=tipo, mensaje=mensaje, enlace=enlace) for a in administradores]
    )
