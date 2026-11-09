from datetime import date

from django import forms
from django.core.exceptions import ValidationError

from core.validators import EXTENSIONES_ACREDITACION, validar_archivo

from .models import SolicitudColaborador


class SolicitudColaboradorForm(forms.ModelForm):
    """Solicitud de acreditación (RF-10). RUT y nombre se toman de la cuenta del usuario."""

    declaracion = forms.BooleanField(
        label="Declaro que la información y el documento adjunto son verídicos.",
        error_messages={"required": "Debes aceptar la declaración para enviar la solicitud."},
    )

    class Meta:
        model = SolicitudColaborador
        fields = ["titulo_profesional", "institucion", "anio_titulacion", "documento_respaldo"]
        labels = {"documento_respaldo": "Certificado de título o documento de respaldo"}
        help_texts = {
            "documento_respaldo": "PDF, JPG o PNG. Tamaño máximo 10 MB.",
            "titulo_profesional": "Ej.: Educadora de Párvulos",
        }
        widgets = {
            "titulo_profesional": forms.TextInput(attrs={"placeholder": "Educador/a de Párvulos"}),
            "institucion": forms.TextInput(attrs={"placeholder": "Universidad o instituto"}),
            "anio_titulacion": forms.NumberInput(attrs={"min": 1960, "max": date.today().year}),
            "documento_respaldo": forms.FileInput(attrs={"accept": ".pdf,.jpg,.jpeg,.png"}),
        }

    def clean_anio_titulacion(self):
        anio = self.cleaned_data["anio_titulacion"]
        if anio < 1960 or anio > date.today().year:
            raise ValidationError(f"Ingresa un año entre 1960 y {date.today().year}.")
        return anio

    def clean_documento_respaldo(self):
        documento = self.cleaned_data.get("documento_respaldo")
        if documento:
            validar_archivo(documento, EXTENSIONES_ACREDITACION)
        return documento


class ResolverSolicitudForm(forms.Form):
    accion = forms.ChoiceField(choices=[("revisar", "revisar"), ("aprobar", "aprobar"), ("rechazar", "rechazar")])
    observacion = forms.CharField(
        required=False, max_length=1000, label="Observación",
        widget=forms.Textarea(attrs={"rows": 3, "maxlength": 1000,
                                     "placeholder": "Obligatoria si rechazas la solicitud."}),
    )

    def clean(self):
        datos = super().clean()
        if datos.get("accion") == "rechazar" and not datos.get("observacion", "").strip():
            self.add_error("observacion", "Debes indicar el motivo del rechazo.")
        return datos
