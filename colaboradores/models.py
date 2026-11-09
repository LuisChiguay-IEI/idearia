"""
Solicitud para convertirse en Profesional Colaborador/a (RF-10, RF-11).

El RUT y el nombre completo NO se repiten aquí: se obtienen del usuario
asociado (relación usuario -> solicitudes). Así el modelo queda normalizado.
"""

import uuid
from pathlib import Path

from django.conf import settings
from django.db import models
from django.db.models import Q
from django.utils import timezone

from core.excepciones import TransicionInvalida


def ruta_acreditacion(instancia, nombre_original):
    """Guarda el archivo con un nombre aleatorio (evita sobrescrituras y rutas maliciosas)."""
    extension = Path(nombre_original).suffix.lower()
    return f"acreditaciones/{uuid.uuid4().hex}{extension}"


class SolicitudColaborador(models.Model):
    class Estado(models.TextChoices):
        PENDIENTE = "PENDIENTE", "Pendiente"
        EN_REVISION = "EN_REVISION", "En revisión"
        APROBADA = "APROBADA", "Aprobada"
        RECHAZADA = "RECHAZADA", "Rechazada"

    ESTADOS_ACTIVOS = (Estado.PENDIENTE, Estado.EN_REVISION)

    usuario = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="solicitudes_colaborador",
    )
    titulo_profesional = models.CharField("título profesional", max_length=150)
    institucion = models.CharField("institución", max_length=150)
    anio_titulacion = models.PositiveSmallIntegerField("año de titulación")
    documento_respaldo = models.FileField(
        "documento de respaldo", upload_to=ruta_acreditacion, max_length=255
    )
    nombre_archivo = models.CharField("nombre original del archivo", max_length=200)
    estado = models.CharField(
        max_length=20, choices=Estado.choices, default=Estado.PENDIENTE, db_index=True
    )
    observacion_admin = models.TextField("observación del administrador", blank=True)
    revisado_por = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="solicitudes_revisadas",
    )
    fecha_solicitud = models.DateTimeField(auto_now_add=True, db_index=True)
    fecha_resolucion = models.DateTimeField(null=True, blank=True)

    class Meta:
        verbose_name = "solicitud de colaborador"
        verbose_name_plural = "solicitudes de colaborador"
        ordering = ["-fecha_solicitud"]
        constraints = [
            # Un usuario no puede tener dos solicitudes activas al mismo tiempo
            models.UniqueConstraint(
                fields=["usuario"],
                condition=Q(estado__in=["PENDIENTE", "EN_REVISION"]),
                name="una_solicitud_activa_por_usuario",
            ),
        ]

    def __str__(self):
        return f"Solicitud de {self.usuario.get_full_name()} ({self.get_estado_display()})"

    @property
    def esta_activa(self):
        return self.estado in self.ESTADOS_ACTIVOS

    @property
    def es_imagen(self):
        return Path(self.documento_respaldo.name).suffix.lower() in (".png", ".jpg", ".jpeg")

    # --- Flujo de estados (diagrama de estados de la Evaluación 2) -----
    def tomar_en_revision(self, administrador):
        if self.estado != self.Estado.PENDIENTE:
            raise TransicionInvalida("Solo una solicitud pendiente puede pasar a revisión.")
        self.estado = self.Estado.EN_REVISION
        self.revisado_por = administrador
        self.save(update_fields=["estado", "revisado_por"])

    def resolver(self, administrador, aprobar, observacion=""):
        """Aprueba o rechaza. Al aprobar, el usuario pasa a rol Colaborador."""
        if not self.esta_activa:
            raise TransicionInvalida(
                f"Esta solicitud ya fue procesada (estado: {self.get_estado_display()})."
            )
        if not aprobar and not observacion.strip():
            raise TransicionInvalida("Debes indicar el motivo del rechazo.")
        self.estado = self.Estado.APROBADA if aprobar else self.Estado.RECHAZADA
        self.observacion_admin = observacion.strip()
        self.revisado_por = administrador
        self.fecha_resolucion = timezone.now()
        self.save()
        if aprobar:
            usuario = self.usuario
            usuario.rol = usuario.Rol.COLABORADOR
            usuario.save(update_fields=["rol"])
