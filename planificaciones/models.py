"""
Planificación / propuesta pedagógica y sus catálogos.

- Ambito y Nucleo: catálogos de las Bases Curriculares de Educación Parvularia.
- Categoria: temática de la idea (relación muchos a muchos mediante
  PlanificacionCategoria, la tabla "planificaciones_categorias" de la Evaluación 2).
- Material: recursos requeridos (relación muchos a muchos).
- Planificacion: la idea pedagógica + el archivo Word/PDF adjunto por su autor.
"""

import uuid
from pathlib import Path

from django.conf import settings
from django.core.validators import MaxLengthValidator
from django.db import models
from django.utils import timezone

from core.excepciones import TransicionInvalida


def ruta_planificacion(instancia, nombre_original):
    """Nombre aleatorio para el archivo; el nombre original se guarda aparte."""
    extension = Path(nombre_original).suffix.lower()
    return f"planificaciones/{uuid.uuid4().hex}{extension}"


class Ambito(models.Model):
    nombre = models.CharField(max_length=100, unique=True)
    descripcion = models.TextField(blank=True)
    orden = models.PositiveSmallIntegerField(default=0)
    icono = models.CharField(max_length=30, default="hoja", help_text="Nombre del ícono SVG")

    class Meta:
        verbose_name = "ámbito"
        verbose_name_plural = "ámbitos"
        ordering = ["orden", "nombre"]

    def __str__(self):
        return self.nombre


class Nucleo(models.Model):
    ambito = models.ForeignKey(Ambito, on_delete=models.PROTECT, related_name="nucleos")
    nombre = models.CharField(max_length=100)

    class Meta:
        verbose_name = "núcleo"
        verbose_name_plural = "núcleos"
        ordering = ["ambito__orden", "nombre"]
        constraints = [
            models.UniqueConstraint(fields=["ambito", "nombre"], name="nucleo_unico_por_ambito")
        ]

    def __str__(self):
        return self.nombre


class Categoria(models.Model):
    nombre = models.CharField(max_length=100, unique=True)
    descripcion = models.TextField(blank=True)

    class Meta:
        verbose_name = "categoría"
        verbose_name_plural = "categorías"
        ordering = ["nombre"]

    def __str__(self):
        return self.nombre


class Material(models.Model):
    nombre = models.CharField(max_length=100, unique=True)

    class Meta:
        verbose_name = "material"
        verbose_name_plural = "materiales"
        ordering = ["nombre"]

    def __str__(self):
        return self.nombre


class Planificacion(models.Model):
    class Estado(models.TextChoices):
        BORRADOR = "BORRADOR", "Borrador"
        EN_REVISION = "EN_REVISION", "En revisión"
        REQUIERE_CORRECCION = "REQUIERE_CORRECCION", "Requiere corrección"
        APROBADA = "APROBADA", "Aprobada"
        RECHAZADA = "RECHAZADA", "Rechazada"
        PUBLICADA = "PUBLICADA", "Publicada"
        RETIRADA = "RETIRADA", "Retirada"

    class Nivel(models.TextChoices):
        SALA_CUNA = "SALA_CUNA", "Sala Cuna"
        NIVEL_MEDIO = "NIVEL_MEDIO", "Nivel Medio"
        PREKINDER = "PREKINDER", "Prekínder"
        KINDER = "KINDER", "Kínder"

    class Edad(models.TextChoices):
        E0_2 = "0-2", "0 a 2 años"
        E2_3 = "2-3", "2 a 3 años"
        E3_4 = "3-4", "3 a 4 años"
        E4_5 = "4-5", "4 a 5 años"
        E5_6 = "5-6", "5 a 6 años"

    DURACIONES = [
        (15, "15 minutos"),
        (20, "20 minutos"),
        (30, "30 minutos"),
        (45, "45 minutos"),
        (60, "60 minutos"),
        (90, "90 minutos"),
        (120, "120 minutos"),
    ]

    # Estados en que el colaborador puede editar su propuesta
    ESTADOS_EDITABLES = (Estado.BORRADOR, Estado.REQUIERE_CORRECCION)

    # Acciones del Administrador: acción -> (estados de origen, estado destino)
    ACCIONES_REVISION = {
        "aprobar": ((Estado.EN_REVISION,), Estado.APROBADA),
        "rechazar": ((Estado.EN_REVISION,), Estado.RECHAZADA),
        "corregir": ((Estado.EN_REVISION,), Estado.REQUIERE_CORRECCION),
        "publicar": ((Estado.APROBADA,), Estado.PUBLICADA),
        "retirar": ((Estado.PUBLICADA,), Estado.RETIRADA),
        "republicar": ((Estado.RETIRADA,), Estado.PUBLICADA),
    }
    # Acciones que exigen escribir una observación para el colaborador
    ACCIONES_CON_MOTIVO = ("rechazar", "corregir", "retirar")

    colaborador = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,  # no se pierde contenido si se intenta borrar al autor
        related_name="planificaciones",
    )
    titulo = models.CharField("título", max_length=120)
    descripcion = models.TextField(
        "descripción", blank=True, validators=[MaxLengthValidator(1000)]
    )
    nivel_educativo = models.CharField(
        "nivel educativo", max_length=20, choices=Nivel.choices, blank=True
    )
    edad_recomendada = models.CharField(
        "edad recomendada", max_length=5, choices=Edad.choices, blank=True
    )
    nucleo = models.ForeignKey(
        Nucleo,
        verbose_name="núcleo de aprendizaje",
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name="planificaciones",
    )
    objetivo_aprendizaje = models.TextField(
        "objetivo de aprendizaje", blank=True, validators=[MaxLengthValidator(300)]
    )
    duracion_minutos = models.PositiveSmallIntegerField(
        "duración", choices=DURACIONES, null=True, blank=True
    )
    materiales = models.ManyToManyField(Material, blank=True, related_name="planificaciones")
    categorias = models.ManyToManyField(
        Categoria,
        through="PlanificacionCategoria",
        blank=True,
        related_name="planificaciones",
    )

    # Archivo de la planificación (Word/PDF) + datos del archivo (Evaluación 2, sección 5.3)
    archivo = models.FileField(
        "planificación adjunta", upload_to=ruta_planificacion, blank=True, max_length=255
    )
    nombre_archivo = models.CharField(max_length=200, blank=True)
    tipo_archivo = models.CharField(max_length=10, blank=True)
    tamano_archivo = models.PositiveIntegerField("tamaño (bytes)", null=True, blank=True)

    # Flujo de revisión
    estado = models.CharField(
        max_length=20, choices=Estado.choices, default=Estado.BORRADOR, db_index=True
    )
    observacion_revision = models.TextField("observación de revisión", blank=True)
    revisado_por = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="planificaciones_revisadas",
    )
    fecha_creacion = models.DateTimeField(auto_now_add=True)
    fecha_actualizacion = models.DateTimeField(auto_now=True)
    fecha_envio = models.DateTimeField("fecha de envío a revisión", null=True, blank=True)
    fecha_publicacion = models.DateTimeField(null=True, blank=True)

    class Meta:
        verbose_name = "planificación"
        verbose_name_plural = "planificaciones"
        ordering = ["-fecha_publicacion", "-fecha_creacion"]
        indexes = [
            # Consulta más frecuente: catálogo de publicadas ordenado por fecha
            models.Index(fields=["estado", "-fecha_publicacion"], name="planif_estado_fecha_idx"),
            # Filtros de búsqueda del Educador
            models.Index(fields=["nivel_educativo", "edad_recomendada"], name="planif_nivel_edad_idx"),
            models.Index(fields=["duracion_minutos"], name="planif_duracion_idx"),
        ]

    def __str__(self):
        return self.titulo

    # --- Consultas de estado -------------------------------------------
    @property
    def es_publica(self):
        return self.estado == self.Estado.PUBLICADA

    @property
    def es_editable(self):
        return self.estado in self.ESTADOS_EDITABLES

    @property
    def ambito(self):
        return self.nucleo.ambito if self.nucleo_id else None

    def puede_ver(self, usuario):
        """Publicadas: cualquier usuario con sesión. Otras: solo su autor o un administrador."""
        if not usuario.is_authenticated:
            return False
        if self.es_publica:
            return True
        return usuario.pk == self.colaborador_id or usuario.es_administrador

    def campos_faltantes(self):
        """Datos obligatorios para enviar a revisión o aprobar (requiere que esté guardada)."""
        faltantes = []
        if not self.titulo.strip():
            faltantes.append("título")
        if not self.descripcion.strip():
            faltantes.append("descripción")
        if not self.nivel_educativo:
            faltantes.append("nivel educativo")
        if not self.edad_recomendada:
            faltantes.append("edad recomendada")
        if not self.nucleo_id:
            faltantes.append("ámbito o núcleo")
        if not self.objetivo_aprendizaje.strip():
            faltantes.append("objetivo de aprendizaje")
        if not self.duracion_minutos:
            faltantes.append("duración")
        if self.pk and not self.categorias.exists():
            faltantes.append("categoría")
        if not self.archivo:
            faltantes.append("planificación adjunta (Word o PDF)")
        return faltantes

    # --- Flujo de estados -------------------------------------------------
    def enviar_a_revision(self):
        """El colaborador envía su propuesta (RF-15). Exige datos completos y archivo."""
        if not self.es_editable:
            raise TransicionInvalida(
                f"Esta propuesta ya fue enviada (estado: {self.get_estado_display()})."
            )
        faltantes = self.campos_faltantes()
        if faltantes:
            raise TransicionInvalida("Completa los campos obligatorios: " + ", ".join(faltantes) + ".")
        self.estado = self.Estado.EN_REVISION
        self.fecha_envio = timezone.now()
        self.save(update_fields=["estado", "fecha_envio", "fecha_actualizacion"])

    def aplicar_accion_revision(self, accion, administrador, observacion=""):
        """Aprobar, rechazar, solicitar corrección, publicar, retirar o volver a publicar."""
        if accion not in self.ACCIONES_REVISION:
            raise TransicionInvalida("Acción no reconocida.")
        origenes, destino = self.ACCIONES_REVISION[accion]
        if self.estado not in origenes:
            raise TransicionInvalida(
                f"No se puede realizar esta acción sobre una propuesta en estado "
                f"«{self.get_estado_display()}»."
            )
        observacion = (observacion or "").strip()
        if accion in self.ACCIONES_CON_MOTIVO and not observacion:
            raise TransicionInvalida("Debes escribir el motivo u observación para el colaborador.")
        if accion in ("aprobar", "publicar"):
            faltantes = self.campos_faltantes()
            if faltantes:
                raise TransicionInvalida(
                    "No se puede aprobar: faltan datos obligatorios (" + ", ".join(faltantes) + ")."
                )
        self.estado = destino
        self.revisado_por = administrador
        if observacion:
            self.observacion_revision = observacion
        if destino == self.Estado.PUBLICADA:
            self.fecha_publicacion = timezone.now()
        self.save()


class PlanificacionCategoria(models.Model):
    """Tabla intermedia planificación <-> categoría (Evaluación 2: planificaciones_categorias)."""

    planificacion = models.ForeignKey(Planificacion, on_delete=models.CASCADE)
    categoria = models.ForeignKey(Categoria, on_delete=models.PROTECT)

    class Meta:
        verbose_name = "categoría de planificación"
        verbose_name_plural = "categorías de planificación"
        constraints = [
            models.UniqueConstraint(
                fields=["planificacion", "categoria"], name="categoria_unica_por_planificacion"
            )
        ]

    def __str__(self):
        return f"{self.planificacion} - {self.categoria}"
