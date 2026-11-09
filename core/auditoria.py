"""Funciones para registrar acciones relevantes (base de datos + archivo de log)."""

import logging

from .models import RegistroAccion

logger = logging.getLogger("idearia.auditoria")


def registrar_accion(request, accion, objeto=None, descripcion=""):
    """Guarda quién hizo qué, sobre qué objeto, cuándo y desde qué IP."""
    usuario = request.user if request.user.is_authenticated else None
    registro = RegistroAccion.objects.create(
        usuario=usuario,
        accion=accion,
        objeto_tipo=objeto._meta.verbose_name if objeto is not None else "",
        objeto_id=objeto.pk if objeto is not None else None,
        descripcion=(descripcion or "")[:500],
        direccion_ip=request.META.get("REMOTE_ADDR"),
    )
    logger.info(
        "%s | %s | %s #%s | %s",
        usuario.email if usuario else "anónimo",
        accion,
        registro.objeto_tipo,
        registro.objeto_id,
        registro.descripcion,
    )
    return registro
