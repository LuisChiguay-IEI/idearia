"""
Interacciones de los usuarios con las ideas publicadas:
favoritos (RF-07/08), valoraciones y comentarios (RF-09/10).

Las restricciones UniqueConstraint impiden, a nivel de base de datos,
duplicar un favorito o una valoración del mismo usuario sobre la misma idea.
"""

from django.conf import settings
from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models
from django.db.models import Q

from planificaciones.models import Planificacion


class Favorito(models.Model):
    usuario = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="favoritos"
    )
    planificacion = models.ForeignKey(
        Planificacion, on_delete=models.CASCADE, related_name="favoritos"
    )
    fecha_registro = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "favorito"
        verbose_name_plural = "favoritos"
        ordering = ["-fecha_registro"]
        constraints = [
            models.UniqueConstraint(
                fields=["usuario", "planificacion"], name="favorito_unico_por_usuario"
            )
        ]

    def __str__(self):
        return f"{self.usuario.email} ♥ {self.planificacion}"


class Valoracion(models.Model):
    usuario = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="valoraciones"
    )
    planificacion = models.ForeignKey(
        Planificacion, on_delete=models.CASCADE, related_name="valoraciones"
    )
    puntuacion = models.PositiveSmallIntegerField(
        validators=[MinValueValidator(1), MaxValueValidator(5)]
    )
    fecha_valoracion = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "valoración"
        verbose_name_plural = "valoraciones"
        constraints = [
            models.UniqueConstraint(
                fields=["usuario", "planificacion"], name="valoracion_unica_por_usuario"
            ),
            models.CheckConstraint(
                condition=Q(puntuacion__gte=1) & Q(puntuacion__lte=5),
                name="puntuacion_entre_1_y_5",
            ),
        ]

    def __str__(self):
        return f"{self.usuario.email}: {self.puntuacion}★ {self.planificacion}"


class Comentario(models.Model):
    class Estado(models.TextChoices):
        VISIBLE = "VISIBLE", "Visible"
        OCULTO = "OCULTO", "Oculto por moderación"

    planificacion = models.ForeignKey(
        Planificacion, on_delete=models.CASCADE, related_name="comentarios"
    )
    usuario = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="comentarios"
    )
    contenido = models.TextField(max_length=1000)
    fecha_comentario = models.DateTimeField(auto_now_add=True, db_index=True)
    estado = models.CharField(max_length=10, choices=Estado.choices, default=Estado.VISIBLE)

    class Meta:
        verbose_name = "comentario"
        verbose_name_plural = "comentarios"
        ordering = ["-fecha_comentario"]

    def __str__(self):
        return f"{self.usuario.email} en {self.planificacion}"
