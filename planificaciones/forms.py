"""Formularios de búsqueda, propuesta pedagógica y revisión."""

from django import forms
from django.core.files.uploadedfile import UploadedFile

from core.validators import EXTENSIONES_PLANIFICACION, validar_archivo

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


class FiltroCatalogoForm(forms.Form):
    """Filtros de búsqueda del Educador (RF-01 a RF-05). Todos son opcionales."""

    q = forms.CharField(required=False, max_length=100, label="Buscar")
    nivel = forms.MultipleChoiceField(
        required=False, choices=Planificacion.Nivel.choices, widget=forms.CheckboxSelectMultiple,
        label="Nivel educativo",
    )
    edad = forms.MultipleChoiceField(
        required=False, choices=Planificacion.Edad.choices, widget=forms.CheckboxSelectMultiple,
        label="Edad",
    )
    ambito = forms.ModelChoiceField(
        required=False, queryset=Ambito.objects.all(), empty_label="Todos los ámbitos", label="Ámbito"
    )
    nucleo = forms.ModelChoiceField(
        required=False, queryset=Nucleo.objects.all(), empty_label="Todos los núcleos", label="Núcleo"
    )
    oa = forms.CharField(
        required=False, max_length=100, label="Objetivo de aprendizaje",
        widget=forms.TextInput(attrs={"placeholder": "Ej.: explorar, emociones, números"}),
    )
    duracion = forms.MultipleChoiceField(
        required=False, choices=RANGOS_DURACION, widget=forms.CheckboxSelectMultiple, label="Duración"
    )
    materiales = forms.ModelMultipleChoiceField(
        required=False, queryset=Material.objects.all(), widget=forms.CheckboxSelectMultiple,
        label="Materiales disponibles",
        help_text="Muestra ideas que puedes realizar solo con los materiales marcados.",
    )
    categoria = forms.ModelChoiceField(
        required=False, queryset=Categoria.objects.all(), empty_label="Todas las categorías",
        label="Categoría",
    )
    orden = forms.ChoiceField(required=False, choices=ORDENES, label="Ordenar por")


class PropuestaForm(forms.ModelForm):
    """
    Crear/editar una propuesta (RF-12, RF-13, RF-14).

    - "Guardar borrador": solo el título es obligatorio.
    - "Enviar a revisión": todos los campos y la planificación adjunta son obligatorios.
    """

    OBLIGATORIOS_ENVIO = (
        "descripcion", "nivel_educativo", "edad_recomendada", "duracion_minutos",
        "nucleo", "objetivo_aprendizaje", "categorias",
    )

    class Meta:
        model = Planificacion
        fields = [
            "titulo", "nivel_educativo", "edad_recomendada", "duracion_minutos", "nucleo",
            "objetivo_aprendizaje", "descripcion", "categorias", "materiales", "archivo",
        ]
        labels = {
            "titulo": "Título de la planificación",
            "duracion_minutos": "Duración aproximada",
            "nucleo": "Ámbito o núcleo de aprendizaje",
            "descripcion": "Descripción breve",
            "categorias": "Categorías",
            "materiales": "Materiales requeridos",
            "archivo": "Planificación pedagógica adjunta",
        }
        help_texts = {
            "objetivo_aprendizaje": "Indica el objetivo de aprendizaje (OA) que se espera potenciar.",
            "descripcion": "Cuéntanos en qué consiste la experiencia, su desarrollo y contexto de aplicación.",
            "nucleo": "Selecciona el núcleo principal que aborda la planificación.",
        }
        widgets = {
            "titulo": forms.TextInput(
                attrs={"placeholder": "Ej.: El juego como oportunidad para explorar el entorno natural", "data-contador": "1"}
            ),
            "objetivo_aprendizaje": forms.Textarea(attrs={"rows": 3, "maxlength": 300}),
            "descripcion": forms.Textarea(attrs={"rows": 5, "maxlength": 1000}),
            "categorias": forms.CheckboxSelectMultiple,
            "materiales": forms.CheckboxSelectMultiple,
            "archivo": forms.FileInput(attrs={"accept": ".pdf,.docx"}),
        }

    def __init__(self, *args, enviar=False, **kwargs):
        super().__init__(*args, **kwargs)
        self.enviar = enviar

        # Núcleos agrupados por ámbito (<optgroup>) para facilitar la selección
        grupos = [("", "Selecciona un ámbito o núcleo")]
        for ambito in Ambito.objects.prefetch_related("nucleos"):
            grupos.append((ambito.nombre, [(n.pk, n.nombre) for n in ambito.nucleos.all()]))
        self.fields["nucleo"].choices = grupos

        self.fields["nivel_educativo"].choices = [("", "Selecciona un nivel")] + list(Planificacion.Nivel.choices)
        self.fields["edad_recomendada"].choices = [("", "Selecciona una edad")] + list(Planificacion.Edad.choices)
        self.fields["duracion_minutos"].choices = [("", "Selecciona duración")] + Planificacion.DURACIONES

        if enviar:
            for nombre in self.OBLIGATORIOS_ENVIO:
                self.fields[nombre].required = True

    def clean_archivo(self):
        archivo = self.cleaned_data.get("archivo")
        if isinstance(archivo, UploadedFile):  # solo se valida un archivo recién subido
            validar_archivo(archivo, EXTENSIONES_PLANIFICACION)
        return archivo

    def clean(self):
        datos = super().clean()
        if self.enviar and not datos.get("archivo") and not self.instance.archivo:
            self.add_error(
                "archivo", "Debes adjuntar la planificación en Word (.docx) o PDF para enviarla a revisión."
            )
        return datos


class AccionRevisionForm(forms.Form):
    """Decisión del Administrador sobre una propuesta (RF-15)."""

    accion = forms.ChoiceField(choices=[(a, a) for a in Planificacion.ACCIONES_REVISION])
    observacion = forms.CharField(
        required=False, max_length=1000, label="Observación para el colaborador",
        widget=forms.Textarea(attrs={"rows": 3, "maxlength": 1000,
                                     "placeholder": "Obligatoria al rechazar, solicitar cambios o retirar."}),
    )

    def clean(self):
        datos = super().clean()
        accion = datos.get("accion")
        if accion in Planificacion.ACCIONES_CON_MOTIVO and not datos.get("observacion", "").strip():
            self.add_error("observacion", "Debes escribir el motivo u observación para el colaborador.")
        return datos
