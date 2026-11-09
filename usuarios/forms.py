"""Formularios de registro, inicio de sesión y administración de usuarios."""

from datetime import date

from django import forms
from django.conf import settings
from django.contrib.auth.forms import (
    AdminUserCreationForm,
    AuthenticationForm,
    UserChangeForm,
    UserCreationForm,
)
from django.core.cache import cache
from django.core.exceptions import ValidationError

from .models import Usuario
from .validators import normalizar_rut, validar_rut


class RegistroForm(UserCreationForm):
    """Registro de Educador/a de Párvulos (RF-26). El rol NO viene del formulario."""

    class Meta:
        model = Usuario
        fields = ("first_name", "last_name", "rut", "email", "fecha_nacimiento")
        labels = {
            "first_name": "Nombres",
            "last_name": "Apellidos",
            "email": "Correo electrónico",
        }
        widgets = {
            "fecha_nacimiento": forms.DateInput(attrs={"type": "date"}, format="%Y-%m-%d"),
            "email": forms.EmailInput(attrs={"placeholder": "tu@correo.cl", "autocomplete": "email"}),
            "rut": forms.TextInput(attrs={"placeholder": "12345678-9"}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for nombre in ("first_name", "last_name", "fecha_nacimiento"):
            self.fields[nombre].required = True
        self.fields["password1"].help_text = (
            "Mínimo 8 caracteres. No puede ser solo números ni una contraseña común."
        )

    def clean_email(self):
        email = self.cleaned_data["email"].strip().lower()
        if Usuario.objects.filter(email__iexact=email).exists():
            raise ValidationError("Ya existe una cuenta asociada a este correo.")
        return email

    def clean_rut(self):
        rut = normalizar_rut(self.cleaned_data["rut"])
        validar_rut(rut)
        if Usuario.objects.filter(rut=rut).exists():
            raise ValidationError("Ya existe una cuenta asociada a este RUT.")
        return rut

    def clean_fecha_nacimiento(self):
        fecha = self.cleaned_data["fecha_nacimiento"]
        hoy = date.today()
        if fecha > hoy:
            raise ValidationError("La fecha de nacimiento no puede ser futura.")
        edad = hoy.year - fecha.year - ((hoy.month, hoy.day) < (fecha.month, fecha.day))
        if edad < 18:
            raise ValidationError("Debes ser mayor de 18 años para registrarte.")
        if edad > 100:
            raise ValidationError("Revisa la fecha de nacimiento ingresada.")
        return fecha

    def save(self, commit=True):
        usuario = super().save(commit=False)
        usuario.rol = Usuario.Rol.EDUCADOR  # todo registro nuevo es Educador/a
        if commit:
            usuario.save()
        return usuario


class LoginForm(AuthenticationForm):
    """
    Inicio de sesión con correo y contraseña.
    Tras LOGIN_MAX_INTENTOS fallos (mismo correo + IP) se bloquea temporalmente.
    """

    error_messages = {
        "invalid_login": "Correo o contraseña incorrectos.",
        "inactive": "Correo o contraseña incorrectos.",
        "bloqueado": "Demasiados intentos fallidos. Intenta nuevamente en %(minutos)s minutos.",
    }

    def __init__(self, request=None, *args, **kwargs):
        super().__init__(request, *args, **kwargs)
        self.fields["username"].label = "Correo electrónico"
        self.fields["username"].widget = forms.EmailInput(
            attrs={"autofocus": True, "autocomplete": "email", "placeholder": "tu@correo.cl"}
        )
        self.fields["password"].widget.attrs["placeholder"] = "Ingresa tu contraseña"

    def clean_username(self):
        return self.cleaned_data["username"].strip().lower()

    def _clave_intentos(self):
        ip = self.request.META.get("REMOTE_ADDR", "") if self.request else ""
        return f"login-fallido:{self.cleaned_data.get('username', '')}:{ip}"

    def clean(self):
        clave = self._clave_intentos()
        if cache.get(clave, 0) >= settings.LOGIN_MAX_INTENTOS:
            raise ValidationError(
                self.error_messages["bloqueado"],
                code="bloqueado",
                params={"minutos": settings.LOGIN_BLOQUEO_MINUTOS},
            )
        try:
            datos = super().clean()
        except ValidationError:
            cache.set(clave, cache.get(clave, 0) + 1, settings.LOGIN_BLOQUEO_MINUTOS * 60)
            raise
        cache.delete(clave)
        return datos


class FiltroUsuariosForm(forms.Form):
    q = forms.CharField(required=False, max_length=100, label="Buscar")
    rol = forms.ChoiceField(
        required=False, choices=[("", "Todos los roles")] + list(Usuario.Rol.choices)
    )
    estado = forms.ChoiceField(
        required=False,
        choices=[("", "Todos"), ("activo", "Activos"), ("inactivo", "Desactivados")],
    )


# --- Formularios del admin técnico de Django ---------------------------
class UsuarioCreacionAdminForm(AdminUserCreationForm):
    class Meta:
        model = Usuario
        fields = ("email", "first_name", "last_name", "rut", "rol")


class UsuarioCambioAdminForm(UserChangeForm):
    class Meta:
        model = Usuario
        fields = "__all__"
