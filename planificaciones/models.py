"""
Planificación / propuesta pedagógica y sus catálogos.

- Ambito y Nucleo: catálogos de las Bases Curriculares de Educación Parvularia.
- Categoria: temática de la idea.
- Material: recursos requeridos.
- Planificacion: idea pedagógica + planificación Word/PDF.
- Imagen de portada: opcional. Si no existe, Idearia mantiene el ícono del ámbito.
"""

import uuid
from pathlib import Path

from django.conf import settings
from django.core.validators import MaxLengthValidator
from django.db import models
from django.utils import timezone

from core.excepciones import TransicionInvalida


def ruta_planificacion(instancia, nombre_original):
    """Genera un nombre aleatorio para la planificación adjunta."""
    extension = Path(nombre_original).suffix.lower()
    return f"planificaciones/{uuid.uuid4().hex}{extension}"


def ruta_imagen_portada(instancia, nombre_original):
    """Genera un nombre aleatorio para la imagen de portada."""
    extension = Path(nombre_original).suffix.lower()
    return f"portadas/{uuid.uuid4().hex}{extension}"


class Ambito(models.Model):
    nombre = models.CharField(max_length=100, unique=True)
    descripcion = models.TextField(blank=True)
    orden = models.PositiveSmallIntegerField(default=0)

    icono = models.CharField(
        max_length=30,
        default="hoja",
        help_text="Nombre del ícono SVG",
    )

    class Meta:
        verbose_name = "ámbito"
        verbose_name_plural = "ámbitos"
        ordering = ["orden", "nombre"]

    def __str__(self):
        return self.nombre


class Nucleo(models.Model):
    ambito = models.ForeignKey(
        Ambito,
        on_delete=models.PROTECT,
        related_name="nucleos",
    )

    nombre = models.CharField(
        max_length=100
    )

    class Meta:
        verbose_name = "núcleo"
        verbose_name_plural = "núcleos"
        ordering = [
            "ambito__orden",
            "nombre",
        ]

        constraints = [
            models.UniqueConstraint(
                fields=[
                    "ambito",
                    "nombre",
                ],
                name="nucleo_unico_por_ambito",
            )
        ]

    def __str__(self):
        return self.nombre


class Categoria(models.Model):
    nombre = models.CharField(
        max_length=100,
        unique=True,
    )

    descripcion = models.TextField(
        blank=True
    )

    class Meta:
        verbose_name = "categoría"
        verbose_name_plural = "categorías"
        ordering = ["nombre"]

    def __str__(self):
        return self.nombre


class Material(models.Model):
    nombre = models.CharField(
        max_length=100,
        unique=True,
    )

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

    ESTADOS_EDITABLES = (
        Estado.BORRADOR,
        Estado.REQUIERE_CORRECCION,
    )

    # ---------------------------------------------------------
    # FLUJO DE REVISIÓN
    # ---------------------------------------------------------
    #
    # Desde ahora:
    #
    # EN_REVISION -> aprobar -> PUBLICADA
    #
    # Así se evita una doble revisión innecesaria.
    #
    # El estado APROBADA se mantiene por compatibilidad con
    # propuestas antiguas que pudieran haber quedado en ese estado.
    # ---------------------------------------------------------

    ACCIONES_REVISION = {

        "aprobar": (
            (Estado.EN_REVISION,),
            Estado.PUBLICADA,
        ),

        "rechazar": (
            (Estado.EN_REVISION,),
            Estado.RECHAZADA,
        ),

        "corregir": (
            (Estado.EN_REVISION,),
            Estado.REQUIERE_CORRECCION,
        ),

        # Compatibilidad con propuestas antiguas ya aprobadas.
        "publicar": (
            (Estado.APROBADA,),
            Estado.PUBLICADA,
        ),

        "retirar": (
            (Estado.PUBLICADA,),
            Estado.RETIRADA,
        ),

        "republicar": (
            (Estado.RETIRADA,),
            Estado.PUBLICADA,
        ),
    }

    ACCIONES_CON_MOTIVO = (
        "rechazar",
        "corregir",
        "retirar",
    )

    colaborador = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="planificaciones",
    )

    titulo = models.CharField(
        "título",
        max_length=120,
    )

    descripcion = models.TextField(
        "descripción",
        blank=True,
        validators=[
            MaxLengthValidator(1000)
        ],
    )

    nivel_educativo = models.CharField(
        "nivel educativo",
        max_length=20,
        choices=Nivel.choices,
        blank=True,
    )

    edad_recomendada = models.CharField(
        "edad recomendada",
        max_length=5,
        choices=Edad.choices,
        blank=True,
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
        "objetivo de aprendizaje",
        blank=True,
        validators=[
            MaxLengthValidator(300)
        ],
    )

    duracion_minutos = models.PositiveSmallIntegerField(
        "duración",
        choices=DURACIONES,
        null=True,
        blank=True,
    )

    materiales = models.ManyToManyField(
        Material,
        blank=True,
        related_name="planificaciones",
    )

    categorias = models.ManyToManyField(
        Categoria,
        through="PlanificacionCategoria",
        blank=True,
        related_name="planificaciones",
    )


    # =========================================================
    # PLANIFICACIÓN PEDAGÓGICA ADJUNTA
    # =========================================================

    archivo = models.FileField(
        "planificación adjunta",
        upload_to=ruta_planificacion,
        blank=True,
        max_length=255,
    )

    nombre_archivo = models.CharField(
        max_length=200,
        blank=True,
    )

    tipo_archivo = models.CharField(
        max_length=10,
        blank=True,
    )

    tamano_archivo = models.PositiveIntegerField(
        "tamaño (bytes)",
        null=True,
        blank=True,
    )


    # =========================================================
    # IMAGEN DE PORTADA OPCIONAL
    # =========================================================

    imagen_portada = models.FileField(
        "imagen de portada",
        upload_to=ruta_imagen_portada,
        blank=True,
        max_length=255,
    )

    nombre_imagen = models.CharField(
        "nombre original de la imagen",
        max_length=200,
        blank=True,
    )

    tipo_imagen = models.CharField(
        "tipo de imagen",
        max_length=20,
        blank=True,
    )

    tamano_imagen = models.PositiveIntegerField(
        "tamaño de imagen (bytes)",
        null=True,
        blank=True,
    )


    # =========================================================
    # ESTADO Y REVISIÓN
    # =========================================================

    estado = models.CharField(
        max_length=20,
        choices=Estado.choices,
        default=Estado.BORRADOR,
        db_index=True,
    )

    observacion_revision = models.TextField(
        "observación de revisión",
        blank=True,
    )

    revisado_por = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="planificaciones_revisadas",
    )

    fecha_creacion = models.DateTimeField(
        auto_now_add=True,
    )

    fecha_actualizacion = models.DateTimeField(
        auto_now=True,
    )

    fecha_envio = models.DateTimeField(
        "fecha de envío a revisión",
        null=True,
        blank=True,
    )

    fecha_publicacion = models.DateTimeField(
        null=True,
        blank=True,
    )


    class Meta:

        verbose_name = "planificación"
        verbose_name_plural = "planificaciones"

        ordering = [
            "-fecha_publicacion",
            "-fecha_creacion",
        ]

        indexes = [

            models.Index(
                fields=[
                    "estado",
                    "-fecha_publicacion",
                ],
                name="planif_estado_fecha_idx",
            ),

            models.Index(
                fields=[
                    "nivel_educativo",
                    "edad_recomendada",
                ],
                name="planif_nivel_edad_idx",
            ),

            models.Index(
                fields=[
                    "duracion_minutos",
                ],
                name="planif_duracion_idx",
            ),
        ]


    def __str__(self):
        return self.titulo


    # =========================================================
    # CONSULTAS DE ESTADO
    # =========================================================

    @property
    def es_publica(self):
        return (
            self.estado
            == self.Estado.PUBLICADA
        )


    @property
    def es_editable(self):
        return (
            self.estado
            in self.ESTADOS_EDITABLES
        )


    @property
    def ambito(self):

        return (
            self.nucleo.ambito
            if self.nucleo_id
            else None
        )


    @property
    def tiene_imagen_portada(self):
        """Indica si la propuesta posee una imagen de portada."""

        return bool(
            self.imagen_portada
        )


    def puede_ver(
        self,
        usuario,
    ):
        """
        Las propuestas publicadas pueden ser vistas por
        usuarios autenticados.

        Las propuestas no publicadas solamente pueden ser
        vistas por su autor o por un Administrador.
        """

        if not usuario.is_authenticated:
            return False

        if self.es_publica:
            return True

        return (
            usuario.pk
            == self.colaborador_id
            or usuario.es_administrador
        )


    # =========================================================
    # CAMPOS OBLIGATORIOS
    # =========================================================

    def campos_faltantes(self):
        """
        Devuelve los campos obligatorios que faltan.

        La imagen de portada NO es obligatoria.
        """

        faltantes = []

        if not self.titulo.strip():
            faltantes.append(
                "título"
            )

        if not self.descripcion.strip():
            faltantes.append(
                "descripción"
            )

        if not self.nivel_educativo:
            faltantes.append(
                "nivel educativo"
            )

        if not self.edad_recomendada:
            faltantes.append(
                "edad recomendada"
            )

        if not self.nucleo_id:
            faltantes.append(
                "ámbito o núcleo"
            )

        if not self.objetivo_aprendizaje.strip():
            faltantes.append(
                "objetivo de aprendizaje"
            )

        if not self.duracion_minutos:
            faltantes.append(
                "duración"
            )

        if (
            self.pk
            and not self.categorias.exists()
        ):
            faltantes.append(
                "categoría"
            )

        if not self.archivo:
            faltantes.append(
                "planificación adjunta (Word o PDF)"
            )

        return faltantes


    # =========================================================
    # ENVÍO A REVISIÓN
    # =========================================================

    def enviar_a_revision(self):
        """
        El colaborador envía su propuesta al Administrador.

        La planificación debe estar completa.

        La imagen de portada sigue siendo opcional.
        """

        if not self.es_editable:

            raise TransicionInvalida(
                (
                    "Esta propuesta ya fue enviada "
                    f"(estado: {self.get_estado_display()})."
                )
            )

        faltantes = self.campos_faltantes()

        if faltantes:

            raise TransicionInvalida(
                (
                    "Completa los campos obligatorios: "
                    + ", ".join(faltantes)
                    + "."
                )
            )

        self.estado = (
            self.Estado.EN_REVISION
        )

        self.fecha_envio = (
            timezone.now()
        )

        self.save(
            update_fields=[
                "estado",
                "fecha_envio",
                "fecha_actualizacion",
            ]
        )


    # =========================================================
    # ACCIONES DEL ADMINISTRADOR
    # =========================================================

    def aplicar_accion_revision(
        self,
        accion,
        administrador,
        observacion="",
    ):
        """
        Aplica una decisión administrativa.

        Flujo principal:

        EN_REVISION
            -> aprobar
            -> PUBLICADA

        De esta forma la aprobación y la publicación ocurren
        en una sola acción.

        También se mantienen:

        - solicitar corrección;
        - rechazar;
        - retirar una publicación;
        - republicar una propuesta retirada;
        - publicar propuestas antiguas que hayan quedado
          en estado APROBADA.

        Si existe una imagen de portada, se considera parte
        del contenido revisado junto con la planificación.
        """

        if accion not in self.ACCIONES_REVISION:

            raise TransicionInvalida(
                "Acción no reconocida."
            )

        origenes, destino = (
            self.ACCIONES_REVISION[
                accion
            ]
        )

        if self.estado not in origenes:

            raise TransicionInvalida(
                (
                    "No se puede realizar esta acción "
                    "sobre una propuesta en estado "
                    f"«{self.get_estado_display()}»."
                )
            )

        observacion = (
            observacion
            or ""
        ).strip()

        if (
            accion
            in self.ACCIONES_CON_MOTIVO
            and not observacion
        ):

            raise TransicionInvalida(
                (
                    "Debes escribir el motivo u observación "
                    "para el colaborador."
                )
            )

        # -----------------------------------------------------
        # VALIDACIÓN ANTES DE APROBAR / PUBLICAR
        # -----------------------------------------------------

        if accion in (
            "aprobar",
            "publicar",
        ):

            faltantes = (
                self.campos_faltantes()
            )

            if faltantes:

                raise TransicionInvalida(
                    (
                        "No se puede aprobar: "
                        "faltan datos obligatorios ("
                        + ", ".join(faltantes)
                        + ")."
                    )
                )

        # -----------------------------------------------------
        # APLICAR NUEVO ESTADO
        # -----------------------------------------------------

        self.estado = destino

        self.revisado_por = (
            administrador
        )

        if observacion:

            self.observacion_revision = (
                observacion
            )

        # -----------------------------------------------------
        # FECHA DE PUBLICACIÓN
        # -----------------------------------------------------
        #
        # Esto ocurre automáticamente al:
        #
        # - aprobar una propuesta nueva;
        # - publicar una propuesta antigua aprobada;
        # - volver a publicar una propuesta retirada.
        # -----------------------------------------------------

        if destino == self.Estado.PUBLICADA:

            self.fecha_publicacion = (
                timezone.now()
            )

        self.save()


class PlanificacionCategoria(models.Model):
    """
    Tabla intermedia planificación <-> categoría.
    """

    planificacion = models.ForeignKey(
        Planificacion,
        on_delete=models.CASCADE,
    )

    categoria = models.ForeignKey(
        Categoria,
        on_delete=models.PROTECT,
    )

    class Meta:

        verbose_name = (
            "categoría de planificación"
        )

        verbose_name_plural = (
            "categorías de planificación"
        )

        constraints = [

            models.UniqueConstraint(
                fields=[
                    "planificacion",
                    "categoria",
                ],
                name=(
                    "categoria_unica_por_planificacion"
                ),
            )

        ]

    def __str__(self):

        return (
            f"{self.planificacion} - "
            f"{self.categoria}"
        )