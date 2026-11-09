"""Registra en el log los inicios de sesión exitosos y fallidos."""

import logging

from django.contrib.auth.signals import user_logged_in, user_login_failed
from django.dispatch import receiver

logger = logging.getLogger("idearia.seguridad")


def _ip(request):
    return request.META.get("REMOTE_ADDR", "desconocida") if request else "desconocida"


@receiver(user_logged_in)
def registrar_inicio_sesion(sender, request, user, **kwargs):
    logger.info("Inicio de sesión: %s desde %s", user.email, _ip(request))


@receiver(user_login_failed)
def registrar_intento_fallido(sender, credentials, request=None, **kwargs):
    # Django ya oculta la contraseña en "credentials"; solo se registra el correo.
    logger.warning(
        "Intento de inicio de sesión fallido para %s desde %s",
        credentials.get("username", "?"),
        _ip(request),
    )
