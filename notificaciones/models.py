"""Notificaciones internas por cambios relevantes (RF-17)."""

from django.conf import settings
from django.db import models


class Notificacion(models.Model):
    class Tipo(models.TextChoices):
        NUEVA_SOLICITUD = "NUEVA_SOLICITUD", "Nueva solicitud de colaborador"
        SOLICITUD_APROBADA = "SOLICITUD_APROBADA", "Solicitud aprobada"
        SOLICITUD_RECHAZADA = "SOLICITUD_RECHAZADA", "Solicitud rechazada"
        NUEVA_PROPUESTA = "NUEVA_PROPUESTA", "Nueva propuesta en revisión"
        PROPUESTA_APROBADA = "PROPUESTA_APROBADA", "Propuesta aprobada"
        PROPUESTA_PUBLICADA = "PROPUESTA_PUBLICADA", "Propuesta publicada"
        PROPUESTA_RECHAZADA = "PROPUESTA_RECHAZADA", "Propuesta rechazada"
        CORRECCION_SOLICITADA = "CORRECCION_SOLICITADA", "Corrección solicitada"
        PROPUESTA_RETIRADA = "PROPUESTA_RETIRADA", "Propuesta retirada"

    usuario = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="notificaciones"
    )
    tipo = models.CharField(max_length=30, choices=Tipo.choices)
    mensaje = models.TextField()
    enlace = models.CharField(max_length=200, blank=True)
    leida = models.BooleanField(default=False)
    fecha_envio = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "notificación"
        verbose_name_plural = "notificaciones"
        ordering = ["-fecha_envio"]
        indexes = [
            # Se consulta en cada página: "¿cuántas no leídas tiene este usuario?"
            models.Index(fields=["usuario", "leida"], name="notif_usuario_leida_idx"),
        ]

    def __str__(self):
        return f"{self.get_tipo_display()} → {self.usuario.email}"
