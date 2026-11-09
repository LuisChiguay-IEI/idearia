"""
Configuración de Django para Idearia.

Generado con 'django-admin startproject' (Django 5.2) y adaptado para:
- leer valores sensibles desde el archivo .env (python-dotenv);
- usar SQLite en desarrollo o PostgreSQL de Supabase según DB_ENGINE;
- aplicar las medidas de seguridad del proyecto.

Las credenciales NUNCA se escriben en este archivo.
"""

import os
from pathlib import Path

from django.contrib.messages import constants as mensajes
from django.core.exceptions import ImproperlyConfigured
from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent.parent

# Carga las variables definidas en .env (si el archivo existe).
load_dotenv(BASE_DIR / ".env")


def env_bool(nombre, por_defecto=False):
    """Lee una variable de entorno como booleano ("True", "1", "si"...)."""
    valor = os.getenv(nombre)
    if valor is None or valor.strip() == "":
        return por_defecto
    return valor.strip().lower() in ("1", "true", "si", "sí", "yes", "on")


def env_lista(nombre, por_defecto=""):
    """Lee una variable separada por comas como lista."""
    return [v.strip() for v in os.getenv(nombre, por_defecto).split(",") if v.strip()]


# ---------------------------------------------------------------
# Seguridad básica
# ---------------------------------------------------------------
SECRET_KEY = os.getenv("SECRET_KEY", "")
if not SECRET_KEY:
    raise ImproperlyConfigured(
        "Falta SECRET_KEY en el archivo .env. Copia .env.example como .env y genera una clave."
    )

# Por seguridad, DEBUG es False salvo que .env diga lo contrario.
DEBUG = env_bool("DEBUG", False)

ALLOWED_HOSTS = env_lista("ALLOWED_HOSTS", "127.0.0.1,localhost")
CSRF_TRUSTED_ORIGINS = env_lista("CSRF_TRUSTED_ORIGINS")


# ---------------------------------------------------------------
# Aplicaciones
# ---------------------------------------------------------------
INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    # Aplicaciones de Idearia
    "core",
    "usuarios",
    "colaboradores",
    "planificaciones",
    "interacciones",
    "notificaciones",
]

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
    # Agrega Content-Security-Policy y Permissions-Policy a cada respuesta
    "core.middleware.CabecerasSeguridadMiddleware",
]

ROOT_URLCONF = "config.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [BASE_DIR / "templates"],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
                "notificaciones.context_processors.notificaciones_no_leidas",
            ],
        },
    },
]

WSGI_APPLICATION = "config.wsgi.application"


# ---------------------------------------------------------------
# Base de datos
# DB_ENGINE="sqlite"   -> archivo local db.sqlite3
# DB_ENGINE="supabase" -> PostgreSQL de Supabase (Session pooler, con SSL)
# ---------------------------------------------------------------
DB_ENGINE = os.getenv("DB_ENGINE", "sqlite").strip().lower()

if DB_ENGINE in ("supabase", "postgresql", "postgres"):
    faltantes = [v for v in ("DB_HOST", "DB_USER", "DB_PASSWORD") if not os.getenv(v)]
    if faltantes:
        raise ImproperlyConfigured(
            "DB_ENGINE indica PostgreSQL/Supabase, pero faltan en .env: " + ", ".join(faltantes)
        )
    DATABASES = {
        "default": {
            "ENGINE": "django.db.backends.postgresql",
            "NAME": os.getenv("DB_NAME", "postgres"),
            "USER": os.getenv("DB_USER"),
            "PASSWORD": os.getenv("DB_PASSWORD"),
            "HOST": os.getenv("DB_HOST"),
            "PORT": os.getenv("DB_PORT", "5432"),
            "OPTIONS": {"sslmode": os.getenv("DB_SSLMODE", "require")},
            # 0 = abrir y cerrar la conexión en cada petición (recomendado con el pooler de Supabase)
            "CONN_MAX_AGE": int(os.getenv("DB_CONN_MAX_AGE", "0")),
        }
    }
elif DB_ENGINE == "sqlite":
    DATABASES = {
        "default": {
            "ENGINE": "django.db.backends.sqlite3",
            "NAME": BASE_DIR / "db.sqlite3",
        }
    }
else:
    raise ImproperlyConfigured('DB_ENGINE debe ser "sqlite" o "supabase".')


# ---------------------------------------------------------------
# Autenticación
# ---------------------------------------------------------------
# Modelo de usuario propio: inicia sesión con correo y tiene un campo "rol".
AUTH_USER_MODEL = "usuarios.Usuario"

LOGIN_URL = "usuarios:login"
LOGIN_REDIRECT_URL = "core:inicio"
LOGOUT_REDIRECT_URL = "usuarios:login"

# Django guarda las contraseñas con hash PBKDF2 (nunca en texto plano).
AUTH_PASSWORD_VALIDATORS = [
    {"NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator"},
    {
        "NAME": "django.contrib.auth.password_validation.MinimumLengthValidator",
        "OPTIONS": {"min_length": 8},
    },
    {"NAME": "django.contrib.auth.password_validation.CommonPasswordValidator"},
    {"NAME": "django.contrib.auth.password_validation.NumericPasswordValidator"},
]

# Bloqueo temporal de inicio de sesión tras varios intentos fallidos
LOGIN_MAX_INTENTOS = 5
LOGIN_BLOQUEO_MINUTOS = 15

# La sesión dura 8 horas (una jornada) y la cookie no es accesible desde JavaScript.
SESSION_COOKIE_AGE = 60 * 60 * 8
SESSION_COOKIE_HTTPONLY = True


# ---------------------------------------------------------------
# Idioma y zona horaria
# ---------------------------------------------------------------
LANGUAGE_CODE = "es-cl"
TIME_ZONE = "America/Santiago"
USE_I18N = True
USE_TZ = True


# ---------------------------------------------------------------
# Archivos estáticos (CSS, JS, imágenes del sitio)
# ---------------------------------------------------------------
STATIC_URL = "static/"
STATICFILES_DIRS = [BASE_DIR / "static"]
STATIC_ROOT = BASE_DIR / "staticfiles"

# ---------------------------------------------------------------
# Archivos subidos (planificaciones y acreditaciones)
# Se guardan en una carpeta que NO tiene URL pública: solo se entregan
# mediante vistas que comprueban sesión y permisos.
# ---------------------------------------------------------------
MEDIA_ROOT = BASE_DIR / "media_protegida"
TAMANO_MAXIMO_ARCHIVO_MB = int(os.getenv("TAMANO_MAXIMO_ARCHIVO_MB", "10"))

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

# Clases CSS para los mensajes de Django
MESSAGE_TAGS = {mensajes.ERROR: "error"}

# Ruta del admin técnico de Django (configurable para no exponer /admin/)
ADMIN_URL = os.getenv("ADMIN_URL", "admin-django/")


# ---------------------------------------------------------------
# Cabeceras de seguridad (siempre activas)
# ---------------------------------------------------------------
SECURE_CONTENT_TYPE_NOSNIFF = True
SECURE_REFERRER_POLICY = "same-origin"
X_FRAME_OPTIONS = "DENY"

# ---------------------------------------------------------------
# Producción: HTTPS obligatorio cuando DEBUG=False
# ---------------------------------------------------------------
if not DEBUG:
    SECURE_SSL_REDIRECT = env_bool("SECURE_SSL_REDIRECT", True)
    SESSION_COOKIE_SECURE = True
    CSRF_COOKIE_SECURE = True
    SECURE_HSTS_SECONDS = int(os.getenv("SECURE_HSTS_SECONDS", "31536000"))
    SECURE_HSTS_INCLUDE_SUBDOMAINS = True
    if env_bool("USAR_PROXY_HTTPS", False):
        SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")


# ---------------------------------------------------------------
# Registro (logs): errores y acciones relevantes en logs/idearia.log
# ---------------------------------------------------------------
LOGS_DIR = BASE_DIR / "logs"
LOGS_DIR.mkdir(exist_ok=True)

LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "simple": {"format": "{asctime} [{levelname}] {name}: {message}", "style": "{"},
    },
    "handlers": {
        "consola": {"class": "logging.StreamHandler", "formatter": "simple"},
        "archivo": {
            "class": "logging.FileHandler",
            "filename": LOGS_DIR / "idearia.log",
            "encoding": "utf-8",
            "formatter": "simple",
        },
    },
    "loggers": {
        "idearia": {"handlers": ["consola", "archivo"], "level": "INFO", "propagate": False},
        "django.request": {"handlers": ["archivo"], "level": "WARNING", "propagate": True},
        "django.security": {"handlers": ["archivo"], "level": "WARNING", "propagate": True},
    },
}
