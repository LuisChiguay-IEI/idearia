"""
Modelo de usuario de Idearia.

Se usa AbstractUser (el usuario estándar de Django) con tres cambios:
1. Se inicia sesión con el correo electrónico (no con "username").
2. Se agregan RUT y fecha de nacimiento (RF-26).
3. Se agrega el campo "rol", que distingue Educador/a, Profesional
   Colaborador/a y Administrador/a en UNA sola tabla.

La contraseña la gestiona Django: se guarda con hash PBKDF2, nunca en texto plano.
El estado de la cuenta (activa / desactivada) usa el campo is_active de Django.
"""

from django.contrib.auth.models import AbstractUser, BaseUserManager
from django.db import models

from .validators import normalizar_rut, validar_rut


class UsuarioManager(BaseUserManager):
    """Crea usuarios usando el correo como identificador."""

    use_in_migrations = True

    def _crear(self, email, password, **campos):
        if not email:
            raise ValueError("El correo electrónico es obligatorio.")
        email = self.normalize_email(email).lower()
        if campos.get("rut"):
            campos["rut"] = normalizar_rut(campos["rut"])
        usuario = self.model(email=email, **campos)
        usuario.set_password(password)  # guarda el hash, no la contraseña
        usuario.save(using=self._db)
        return usuario

    def create_user(self, email, password=None, **campos):
        campos.setdefault("is_staff", False)
        campos.setdefault("is_superuser", False)
        campos.setdefault("rol", Usuario.Rol.EDUCADOR)
        return self._crear(email, password, **campos)

    def create_superuser(self, email, password=None, **campos):
        campos["is_staff"] = True
        campos["is_superuser"] = True
        campos["rol"] = Usuario.Rol.ADMINISTRADOR
        return self._crear(email, password, **campos)


class Usuario(AbstractUser):
    class Rol(models.TextChoices):
        EDUCADOR = "EDUCADOR", "Educador/a de Párvulos"
        COLABORADOR = "COLABORADOR", "Profesional Colaborador/a"
        ADMINISTRADOR = "ADMINISTRADOR", "Administrador/a"

    # Se elimina "username": el identificador es el correo.
    username = None
    email = models.EmailField("correo electrónico", unique=True)
    rut = models.CharField(
        "RUT",
        max_length=12,
        unique=True,
        validators=[validar_rut],
        help_text="Formato 12345678-9, sin puntos.",
    )
    fecha_nacimiento = models.DateField("fecha de nacimiento", null=True, blank=True)
    rol = models.CharField(
        "rol",
        max_length=20,
        choices=Rol.choices,
        default=Rol.EDUCADOR,
        db_index=True,  # se filtra por rol (permisos, listados del administrador)
    )

    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = ["first_name", "last_name", "rut"]

    objects = UsuarioManager()

    class Meta:
        verbose_name = "usuario"
        verbose_name_plural = "usuarios"
        ordering = ["first_name", "last_name"]

    def __str__(self):
        return f"{self.get_full_name() or self.email} ({self.email})"

    # --- Atajos para verificar el rol en vistas y plantillas -----------
    @property
    def es_educador(self):
        return self.rol == self.Rol.EDUCADOR

    @property
    def es_colaborador(self):
        return self.rol == self.Rol.COLABORADOR

    @property
    def es_administrador(self):
        return self.rol == self.Rol.ADMINISTRADOR or self.is_superuser

    @property
    def puede_interactuar(self):
        """Favoritos, valoraciones y comentarios: Educador/a y Colaborador/a."""
        return self.rol in (self.Rol.EDUCADOR, self.Rol.COLABORADOR)

    @property
    def iniciales(self):
        partes = [self.first_name[:1], self.last_name[:1]]
        return ("".join(partes) or self.email[:1]).upper()
