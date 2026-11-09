"""Registro de acciones administrativas (auditoría, RNF-11)."""

from django.conf import settings
from django.db import models


class RegistroAccion(models.Model):
    class Accion(models.TextChoices):
        REVISAR_SOLICITUD = "REVISAR_SOLICITUD", "Tomar solicitud en revisión"
        APROBAR_SOLICITUD = "APROBAR_SOLICITUD", "Aprobar solicitud de colaborador"
        RECHAZAR_SOLICITUD = "RECHAZAR_SOLICITUD", "Rechazar solicitud de colaborador"
        APROBAR_PROPUESTA = "APROBAR_PROPUESTA", "Aprobar propuesta"
        RECHAZAR_PROPUESTA = "RECHAZAR_PROPUESTA", "Rechazar propuesta"
        SOLICITAR_CORRECCION = "SOLICITAR_CORRECCION", "Solicitar corrección"
        PUBLICAR_PROPUESTA = "PUBLICAR_PROPUESTA", "Publicar propuesta"
        RETIRAR_PROPUESTA = "RETIRAR_PROPUESTA", "Retirar propuesta"
        REPUBLICAR_PROPUESTA = "REPUBLICAR_PROPUESTA", "Volver a publicar propuesta"
        ACTIVAR_USUARIO = "ACTIVAR_USUARIO", "Activar usuario"
        DESACTIVAR_USUARIO = "DESACTIVAR_USUARIO", "Desactivar usuario"
        OCULTAR_COMENTARIO = "OCULTAR_COMENTARIO", "Ocultar comentario"
        MOSTRAR_COMENTARIO = "MOSTRAR_COMENTARIO", "Mostrar comentario"

    usuario = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,  # si se borra el usuario, el registro se conserva
        null=True,
        related_name="acciones_registradas",
    )
    accion = models.CharField(max_length=30, choices=Accion.choices, db_index=True)
    objeto_tipo = models.CharField("tipo de objeto", max_length=60, blank=True)
    objeto_id = models.PositiveBigIntegerField("id del objeto", null=True, blank=True)
    descripcion = models.CharField(max_length=500, blank=True)
    direccion_ip = models.GenericIPAddressField("dirección IP", null=True, blank=True)
    fecha = models.DateTimeField(auto_now_add=True, db_index=True)

    class Meta:
        verbose_name = "registro de acción"
        verbose_name_plural = "registro de acciones"
        ordering = ["-fecha"]

    def __str__(self):
        return f"{self.fecha:%d-%m-%Y %H:%M} {self.get_accion_display()}"
