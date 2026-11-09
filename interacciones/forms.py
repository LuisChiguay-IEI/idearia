from django import forms
from django.core.exceptions import ValidationError

from .models import Comentario


class ValoracionForm(forms.Form):
    puntuacion = forms.TypedChoiceField(
        label="Tu valoración",
        choices=[(i, f"{i} estrella{'s' if i > 1 else ''}") for i in range(1, 6)],
        coerce=int,
        widget=forms.RadioSelect,
        error_messages={"required": "Selecciona entre 1 y 5 estrellas.",
                        "invalid_choice": "La valoración debe estar entre 1 y 5."},
    )


class ComentarioForm(forms.ModelForm):
    class Meta:
        model = Comentario
        fields = ["contenido"]
        labels = {"contenido": "Tu comentario"}
        widgets = {
            "contenido": forms.Textarea(
                attrs={"rows": 3, "maxlength": 1000,
                       "placeholder": "Comparte cómo aplicaste esta idea o una sugerencia respetuosa..."}
            )
        }

    def clean_contenido(self):
        contenido = self.cleaned_data["contenido"].strip()
        if len(contenido) < 3:
            raise ValidationError("El comentario es demasiado corto.")
        return contenido
