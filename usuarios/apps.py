from django.apps import AppConfig


class UsuariosConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "usuarios"
    verbose_name = "Usuarios"

    def ready(self):
        # Conecta las señales que registran inicios de sesión en el log
        from . import senales  # noqa: F401
