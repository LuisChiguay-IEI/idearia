"""Formularios de búsqueda, propuesta pedagógica y revisión."""

from django import forms
from django.core.cache import cache
from django.core.files.uploadedfile import UploadedFile

from core.validators import (
    EXTENSIONES_IMAGEN_PORTADA,
    EXTENSIONES_PLANIFICACION,
    validar_archivo,
)

from .models import Ambito, Categoria, Material, Nucleo, Planificacion


RANGOS_DURACION = [
    ("corta", "Menos de 30 minutos"),
    ("media", "30 a 60 minutos"),
    ("larga", "Más de 60 minutos"),
]

ORDENES = [
    ("recientes", "Más recientes"),
    ("valoradas", "Mejor valoradas"),
    ("titulo", "Título (A-Z)"),
]


def opciones_en_cache(modelo, etiqueta_vacia=None, segundos=600):
    """
    Lista (id, nombre) de un catálogo guardada 10 minutos en caché.

    Los catálogos casi nunca cambian, por lo que así se evita
    consultar constantemente la base de datos.
    """

    clave = f"catalogo:{modelo._meta.label_lower}"

    opciones = cache.get(clave)

    if opciones is None:

        opciones = [
            (objeto.pk, str(objeto))
            for objeto in modelo.objects.all()
        ]

        cache.set(
            clave,
            opciones,
            segundos,
        )

    return (
        [("", etiqueta_vacia)]
        if etiqueta_vacia
        else []
    ) + opciones


class FiltroCatalogoForm(forms.Form):
    """
    Filtros de búsqueda del Educador.

    Todos los filtros son opcionales.
    """

    def __init__(self, *args, **kwargs):

        super().__init__(*args, **kwargs)

        self.fields["ambito"].choices = opciones_en_cache(
            Ambito,
            "Todos los ámbitos",
        )

        self.fields["nucleo"].choices = opciones_en_cache(
            Nucleo,
            "Todos los núcleos",
        )

        self.fields["materiales"].choices = opciones_en_cache(
            Material,
        )

        self.fields["categoria"].choices = opciones_en_cache(
            Categoria,
            "Todas las categorías",
        )

    q = forms.CharField(
        required=False,
        max_length=100,
        label="Buscar",
    )

    nivel = forms.MultipleChoiceField(
        required=False,
        choices=Planificacion.Nivel.choices,
        widget=forms.CheckboxSelectMultiple,
        label="Nivel educativo",
    )

    edad = forms.MultipleChoiceField(
        required=False,
        choices=Planificacion.Edad.choices,
        widget=forms.CheckboxSelectMultiple,
        label="Edad",
    )

    ambito = forms.ModelChoiceField(
        required=False,
        queryset=Ambito.objects.all(),
        empty_label="Todos los ámbitos",
        label="Ámbito",
    )

    nucleo = forms.ModelChoiceField(
        required=False,
        queryset=Nucleo.objects.all(),
        empty_label="Todos los núcleos",
        label="Núcleo",
    )

    oa = forms.CharField(
        required=False,
        max_length=100,
        label="Objetivo de aprendizaje",
        widget=forms.TextInput(
            attrs={
                "placeholder": "Ej.: explorar, emociones, números"
            }
        ),
    )

    duracion = forms.MultipleChoiceField(
        required=False,
        choices=RANGOS_DURACION,
        widget=forms.CheckboxSelectMultiple,
        label="Duración",
    )

    materiales = forms.ModelMultipleChoiceField(
        required=False,
        queryset=Material.objects.all(),
        widget=forms.CheckboxSelectMultiple,
        label="Materiales disponibles",
        help_text=(
            "Muestra ideas que puedes realizar solo con "
            "los materiales seleccionados."
        ),
    )

    categoria = forms.ModelChoiceField(
        required=False,
        queryset=Categoria.objects.all(),
        empty_label="Todas las categorías",
        label="Categoría",
    )

    orden = forms.ChoiceField(
        required=False,
        choices=ORDENES,
        label="Ordenar por",
    )


class PropuestaForm(forms.ModelForm):
    """
    Crear o editar una propuesta pedagógica.

    Guardar borrador:
    - solamente el título es obligatorio.

    Enviar a revisión:
    - deben completarse los datos pedagógicos;
    - debe existir una planificación Word/PDF.

    Imagen de portada:
    - es completamente opcional;
    - puede ser JPG o PNG;
    - si no existe, Idearia mantiene los íconos actuales;
    - puede reemplazarse o eliminarse;
    - será revisada por el Administrador junto con la
      planificación antes de publicar.
    """

    OBLIGATORIOS_ENVIO = (
        "descripcion",
        "nivel_educativo",
        "edad_recomendada",
        "duracion_minutos",
        "nucleo",
        "objetivo_aprendizaje",
        "categorias",
    )

    quitar_imagen_portada = forms.BooleanField(
        required=False,
        label="Quitar imagen de portada",
        help_text=(
            "Si quitas la imagen, Idearia volverá a mostrar "
            "automáticamente el ícono correspondiente al ámbito."
        ),
    )

    class Meta:

        model = Planificacion

        fields = [
            "titulo",
            "nivel_educativo",
            "edad_recomendada",
            "duracion_minutos",
            "nucleo",
            "objetivo_aprendizaje",
            "descripcion",
            "categorias",
            "materiales",
            "imagen_portada",
            "archivo",
        ]

        labels = {

            "titulo":
                "Título de la planificación",

            "duracion_minutos":
                "Duración aproximada",

            "nucleo":
                "Ámbito o núcleo de aprendizaje",

            "descripcion":
                "Descripción breve",

            "categorias":
                "Categorías",

            "materiales":
                "Materiales requeridos",

            "archivo":
                "Planificación pedagógica adjunta",

            "imagen_portada":
                "Imagen de portada",
        }

        help_texts = {

            "objetivo_aprendizaje": (
                "Indica el objetivo de aprendizaje (OA) "
                "que se espera potenciar."
            ),

            "descripcion": (
                "Cuéntanos en qué consiste la experiencia, "
                "su desarrollo y contexto de aplicación."
            ),

            "nucleo": (
                "Selecciona el núcleo principal que aborda "
                "la planificación."
            ),

            "imagen_portada": (
                "Opcional. Puedes agregar una imagen relacionada "
                "con la experiencia pedagógica. "
                "Si no agregas ninguna, Idearia utilizará "
                "el ícono correspondiente al ámbito. "
                "La imagen será revisada junto con la planificación "
                "antes de publicar."
            ),

            "archivo": (
                "Adjunta la planificación pedagógica en "
                "formato PDF o Word (.docx)."
            ),
        }

        widgets = {

            "titulo": forms.TextInput(
                attrs={
                    "placeholder": (
                        "Ej.: El juego como oportunidad para "
                        "explorar el entorno natural"
                    ),
                    "data-contador": "1",
                }
            ),

            "objetivo_aprendizaje": forms.Textarea(
                attrs={
                    "rows": 3,
                    "maxlength": 300,
                }
            ),

            "descripcion": forms.Textarea(
                attrs={
                    "rows": 5,
                    "maxlength": 1000,
                }
            ),

            "categorias":
                forms.CheckboxSelectMultiple,

            "materiales":
                forms.CheckboxSelectMultiple,

            "imagen_portada": forms.FileInput(
                attrs={
                    "accept":
                        ".jpg,.jpeg,.png,image/jpeg,image/png",
                }
            ),

            "archivo": forms.FileInput(
                attrs={
                    "accept": ".pdf,.docx",
                }
            ),
        }

    def __init__(
        self,
        *args,
        enviar=False,
        **kwargs,
    ):

        super().__init__(
            *args,
            **kwargs,
        )

        self.enviar = enviar

        # -----------------------------------------------------
        # NÚCLEOS AGRUPADOS POR ÁMBITO
        # -----------------------------------------------------

        grupos = [
            (
                "",
                "Selecciona un ámbito o núcleo",
            )
        ]

        for ambito in Ambito.objects.prefetch_related(
            "nucleos"
        ):

            grupos.append(
                (
                    ambito.nombre,

                    [
                        (
                            nucleo.pk,
                            nucleo.nombre,
                        )
                        for nucleo
                        in ambito.nucleos.all()
                    ],
                )
            )

        self.fields["nucleo"].choices = grupos

        # -----------------------------------------------------
        # OPCIONES DE SELECT
        # -----------------------------------------------------

        self.fields["nivel_educativo"].choices = [
            (
                "",
                "Selecciona un nivel",
            )
        ] + list(
            Planificacion.Nivel.choices
        )

        self.fields["edad_recomendada"].choices = [
            (
                "",
                "Selecciona una edad",
            )
        ] + list(
            Planificacion.Edad.choices
        )

        self.fields["duracion_minutos"].choices = [
            (
                "",
                "Selecciona duración",
            )
        ] + Planificacion.DURACIONES

        # -----------------------------------------------------
        # CAMPOS OBLIGATORIOS AL ENVIAR
        # -----------------------------------------------------

        if enviar:

            for nombre in self.OBLIGATORIOS_ENVIO:

                self.fields[
                    nombre
                ].required = True

        # La portada siempre es opcional.
        self.fields[
            "imagen_portada"
        ].required = False

        # -----------------------------------------------------
        # OPCIÓN PARA QUITAR LA PORTADA
        # -----------------------------------------------------
        #
        # Solo tiene sentido mostrarla cuando realmente existe
        # una imagen guardada en la propuesta.
        # -----------------------------------------------------

        if not (
            self.instance
            and self.instance.pk
            and self.instance.imagen_portada
        ):

            self.fields[
                "quitar_imagen_portada"
            ].widget = forms.HiddenInput()


    # =========================================================
    # VALIDACIÓN DE PLANIFICACIÓN
    # =========================================================

    def clean_archivo(self):

        archivo = self.cleaned_data.get(
            "archivo"
        )

        if isinstance(
            archivo,
            UploadedFile,
        ):

            validar_archivo(
                archivo,
                EXTENSIONES_PLANIFICACION,
            )

        return archivo


    # =========================================================
    # VALIDACIÓN DE IMAGEN DE PORTADA
    # =========================================================

    def clean_imagen_portada(self):

        imagen = self.cleaned_data.get(
            "imagen_portada"
        )

        if isinstance(
            imagen,
            UploadedFile,
        ):

            validar_archivo(
                imagen,
                EXTENSIONES_IMAGEN_PORTADA,
            )

        return imagen


    # =========================================================
    # VALIDACIÓN GENERAL
    # =========================================================

    def clean(self):

        datos = super().clean()

        # -----------------------------------------------------
        # PLANIFICACIÓN OBLIGATORIA AL ENVIAR
        # -----------------------------------------------------

        if (
            self.enviar
            and not datos.get("archivo")
            and not self.instance.archivo
        ):

            self.add_error(
                "archivo",
                (
                    "Debes adjuntar la planificación en "
                    "Word (.docx) o PDF para enviarla a revisión."
                ),
            )

        # -----------------------------------------------------
        # NUEVA IMAGEN SUBIDA EN ESTE FORMULARIO
        # -----------------------------------------------------
        #
        # IMPORTANTE:
        #
        # No utilizamos cleaned_data["imagen_portada"] aquí
        # para saber si se subió una nueva imagen.
        #
        # Cuando se edita una propuesta, Django puede devolver
        # la imagen que ya estaba almacenada como valor inicial.
        #
        # self.files comprueba únicamente si el usuario acaba
        # de seleccionar una NUEVA imagen desde su equipo.
        # -----------------------------------------------------

        nueva_imagen = self.files.get(
            "imagen_portada"
        )

        quitar_imagen = datos.get(
            "quitar_imagen_portada",
            False,
        )

        # -----------------------------------------------------
        # NO PERMITIR DOS ACCIONES CONTRADICTORIAS
        # -----------------------------------------------------

        if (
            nueva_imagen
            and quitar_imagen
        ):

            self.add_error(
                "imagen_portada",
                (
                    "Selecciona una sola opción: "
                    "subir una nueva imagen o quitar "
                    "la imagen actual."
                ),
            )

        return datos


class AccionRevisionForm(forms.Form):
    """
    Decisión del Administrador sobre una propuesta pedagógica.
    """

    accion = forms.ChoiceField(
        choices=[
            (
                accion,
                accion,
            )
            for accion
            in Planificacion.ACCIONES_REVISION
        ]
    )

    observacion = forms.CharField(
        required=False,
        max_length=1000,
        label="Observación para el colaborador",
        widget=forms.Textarea(
            attrs={
                "rows": 3,
                "maxlength": 1000,
                "placeholder": (
                    "Obligatoria al rechazar, "
                    "solicitar cambios o retirar."
                ),
            }
        ),
    )

    def clean(self):

        datos = super().clean()

        accion = datos.get(
            "accion"
        )

        observacion = datos.get(
            "observacion",
            "",
        ).strip()

        if (
            accion
            in Planificacion.ACCIONES_CON_MOTIVO
            and not observacion
        ):

            self.add_error(
                "observacion",
                (
                    "Debes escribir el motivo u observación "
                    "para el colaborador."
                ),
            )

        return datos