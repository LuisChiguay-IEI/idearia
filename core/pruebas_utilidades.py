"""
Funciones de apoyo para las pruebas automatizadas (no se usan en producción).

Cada prueba usa una carpeta temporal para los archivos subidos, así no
se mezclan con los datos reales.
"""

import shutil
import tempfile

from django.core.cache import cache
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase, override_settings
from django.utils import timezone

from planificaciones.models import Categoria, Nucleo, Planificacion
from usuarios.models import Usuario
from usuarios.validators import calcular_digito_verificador

from .documentos_demo import generar_docx, generar_pdf

CLAVE = "ClaveSegura-2026"
_contador_rut = [20000000]


def rut_valido():
    _contador_rut[0] += 1
    cuerpo = str(_contador_rut[0])
    return f"{cuerpo}-{calcular_digito_verificador(cuerpo)}"


def crear_usuario(rol=Usuario.Rol.EDUCADOR, email=None, **campos):
    email = email or f"{rol.lower()}{_contador_rut[0]}@prueba.test"
    return Usuario.objects.create_user(
        email=email, password=CLAVE, first_name=campos.pop("first_name", "Ana"),
        last_name=campos.pop("last_name", "Prueba"), rut=rut_valido(), rol=rol, **campos,
    )


def pdf_subido(nombre="planificacion.pdf"):
    return SimpleUploadedFile(nombre, generar_pdf("Planificación de prueba", [("Objetivo", "Explorar")]), "application/pdf")


def docx_subido(nombre="planificacion.docx"):
    return SimpleUploadedFile(
        nombre, generar_docx("Planificación Word de prueba", [("Inicio", "Saludo inicial")]),
        "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
    )


def crear_planificacion(colaborador, estado=Planificacion.Estado.PUBLICADA, **campos):
    """Crea una propuesta completa (con archivo PDF) en el estado indicado."""
    datos = {
        "titulo": "Exploramos la naturaleza",
        "descripcion": "Experiencia sensorial al aire libre.",
        "nivel_educativo": Planificacion.Nivel.NIVEL_MEDIO,
        "edad_recomendada": Planificacion.Edad.E3_4,
        "nucleo": Nucleo.objects.get(nombre="Exploración del Entorno Natural"),
        "objetivo_aprendizaje": "Explorar elementos naturales con los sentidos.",
        "duracion_minutos": 45,
    }
    datos.update(campos)
    categorias = datos.pop("categorias", ["Exploración y naturaleza"])
    materiales = datos.pop("materiales", [])
    p = Planificacion(colaborador=colaborador, estado=estado, **datos)
    archivo = pdf_subido()
    p.archivo.save("planificacion.pdf", archivo, save=False)
    p.nombre_archivo, p.tipo_archivo, p.tamano_archivo = "planificacion.pdf", "pdf", archivo.size
    if estado != Planificacion.Estado.BORRADOR:
        p.fecha_envio = timezone.now()
    if estado == Planificacion.Estado.PUBLICADA:
        p.fecha_publicacion = timezone.now()
    p.save()
    p.categorias.set(Categoria.objects.filter(nombre__in=categorias))
    if materiales:
        p.materiales.set(materiales)
    return p


class PruebaIdearia(TestCase):
    """Base de las pruebas: carpeta temporal para archivos y caché limpia."""

    @classmethod
    def setUpClass(cls):
        cls._carpeta_media = tempfile.mkdtemp(prefix="idearia_pruebas_")
        # Las pruebas siempre guardan archivos en una carpeta temporal (no en la BD ni en media_protegida)
        cls._override = override_settings(
            MEDIA_ROOT=cls._carpeta_media,
            STORAGES={
                "default": {"BACKEND": "django.core.files.storage.FileSystemStorage"},
                "staticfiles": {"BACKEND": "django.contrib.staticfiles.storage.StaticFilesStorage"},
            },
        )
        cls._override.enable()
        super().setUpClass()

    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()
        cls._override.disable()
        shutil.rmtree(cls._carpeta_media, ignore_errors=True)

    def setUp(self):
        cache.clear()

    def ingresar(self, usuario):
        self.client.force_login(usuario)
