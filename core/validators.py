"""
Validación de archivos subidos en Idearia.

Se validan:

- planificaciones pedagógicas;
- documentos de acreditación profesional;
- imágenes opcionales de portada.

Las validaciones comprueban:

1. Extensión permitida.
2. Tamaño del archivo.
3. Tipo MIME informado por el navegador.
4. Firma real del contenido.

Esto evita, por ejemplo, que alguien cambie el nombre de un archivo
ejecutable a "imagen.jpg" o "planificacion.pdf" para intentar subirlo.

Los archivos nunca se ejecutan.
Solo se almacenan y procesan como datos.
"""

import zipfile
from pathlib import Path

from django.conf import settings
from django.core.exceptions import ValidationError


# ---------------------------------------------------------
# FORMATOS PERMITIDOS
# ---------------------------------------------------------

# Planificación pedagógica adjunta.
EXTENSIONES_PLANIFICACION = (
    "pdf",
    "docx",
)

# Documentos utilizados para acreditar al Profesional Colaborador.
EXTENSIONES_ACREDITACION = (
    "pdf",
    "jpg",
    "png",
)

# Imagen opcional que el colaborador puede asociar a su propuesta.
#
# Si no se sube ninguna imagen, Idearia continuará mostrando
# automáticamente el ícono correspondiente al ámbito.
EXTENSIONES_IMAGEN_PORTADA = (
    "jpg",
    "png",
)


# ---------------------------------------------------------
# FIRMAS REALES DE ARCHIVOS
# ---------------------------------------------------------
#
# No basta con comprobar la extensión.
#
# Ejemplo:
#
# archivo.exe -> renombrado como -> imagen.jpg
#
# seguiría teniendo una firma interna distinta y sería rechazado.
# ---------------------------------------------------------

FIRMAS = {
    "pdf": (
        b"%PDF-",
    ),

    "docx": (
        b"PK\x03\x04",
    ),

    "png": (
        b"\x89PNG\r\n\x1a\n",
    ),

    "jpg": (
        b"\xff\xd8\xff",
    ),
}


# ---------------------------------------------------------
# TIPOS MIME PERMITIDOS
# ---------------------------------------------------------

TIPOS_MIME = {
    "pdf": (
        "application/pdf",
    ),

    "docx": (
        "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        "application/octet-stream",
        "application/zip",
    ),

    "png": (
        "image/png",
    ),

    "jpg": (
        "image/jpeg",
        "image/pjpeg",
    ),
}


# ---------------------------------------------------------
# TAMAÑO MÁXIMO
# ---------------------------------------------------------

def tamano_maximo_bytes():
    """
    Obtiene el tamaño máximo permitido desde settings.py.

    Actualmente Idearia utiliza TAMANO_MAXIMO_ARCHIVO_MB,
    configurable mediante variables de entorno.
    """
    return settings.TAMANO_MAXIMO_ARCHIVO_MB * 1024 * 1024


# ---------------------------------------------------------
# EXTENSIÓN
# ---------------------------------------------------------

def obtener_extension(nombre):
    """
    Obtiene y normaliza la extensión de un archivo.

    .jpeg se considera equivalente a .jpg.
    """
    extension = Path(nombre or "").suffix.lower().lstrip(".")

    if extension == "jpeg":
        return "jpg"

    return extension


# ---------------------------------------------------------
# VALIDACIÓN PRINCIPAL
# ---------------------------------------------------------

def validar_archivo(archivo, extensiones_permitidas):
    """
    Valida un archivo subido mediante UploadedFile.

    Comprueba:

    - extensión;
    - tamaño;
    - MIME;
    - firma real;
    - estructura interna cuando corresponde.

    Devuelve la extensión normalizada si el archivo es válido.

    Si encuentra un problema lanza ValidationError.
    """

    formatos = ", ".join(
        f".{extension}"
        for extension in extensiones_permitidas
    )

    extension = obtener_extension(archivo.name)

    # -----------------------------------------------------
    # 1. EXTENSIÓN
    # -----------------------------------------------------

    if extension not in extensiones_permitidas:
        raise ValidationError(
            f"Formato no permitido. Formatos aceptados: {formatos}.",
            code="extension",
        )

    # -----------------------------------------------------
    # 2. TAMAÑO
    # -----------------------------------------------------

    if archivo.size == 0:
        raise ValidationError(
            "El archivo está vacío.",
            code="vacio",
        )

    if archivo.size > tamano_maximo_bytes():
        raise ValidationError(
            (
                "El archivo supera el tamaño máximo de "
                f"{settings.TAMANO_MAXIMO_ARCHIVO_MB} MB."
            ),
            code="tamano",
        )

    # -----------------------------------------------------
    # 3. TIPO MIME
    # -----------------------------------------------------

    tipo = getattr(
        archivo,
        "content_type",
        None,
    )

    if tipo and tipo not in TIPOS_MIME[extension]:
        raise ValidationError(
            "El tipo de archivo no corresponde a su extensión.",
            code="mime",
        )

    # -----------------------------------------------------
    # 4. FIRMA REAL DEL ARCHIVO
    # -----------------------------------------------------

    archivo.seek(0)

    cabecera = archivo.read(8)

    archivo.seek(0)

    if not any(
        cabecera.startswith(firma)
        for firma in FIRMAS[extension]
    ):
        raise ValidationError(
            "El contenido del archivo no corresponde a su extensión.",
            code="firma",
        )

    # -----------------------------------------------------
    # VALIDACIÓN ESPECIAL PARA DOCX
    # -----------------------------------------------------
    #
    # Un documento .docx realmente es un archivo ZIP.
    #
    # También comprobamos que no contenga macros.
    # -----------------------------------------------------

    if extension == "docx":
        try:
            with zipfile.ZipFile(archivo) as zip_docx:
                nombres = set(
                    zip_docx.namelist()
                )

        except zipfile.BadZipFile:
            raise ValidationError(
                "El documento Word está dañado.",
                code="docx_danado",
            )

        finally:
            archivo.seek(0)

        if "word/document.xml" not in nombres:
            raise ValidationError(
                "El archivo no es un documento Word válido.",
                code="docx",
            )

        if any(
            nombre.lower().endswith("vbaproject.bin")
            for nombre in nombres
        ):
            raise ValidationError(
                "No se permiten documentos con macros.",
                code="macros",
            )

    return extension