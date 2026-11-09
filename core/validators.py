"""
Validación de archivos subidos (planificaciones y documentos de acreditación).

Se comprueban cuatro cosas, porque cada una por sí sola se puede falsificar:
1. Extensión permitida.
2. Tamaño (no vacío y bajo el máximo configurado).
3. Tipo MIME informado por el navegador.
4. "Firma" real del contenido: los primeros bytes del archivo
   (un .exe renombrado a .pdf NO empieza con %PDF-).

Los archivos nunca se ejecutan: solo se guardan y se leen como bytes.
"""

import zipfile
from pathlib import Path

from django.conf import settings
from django.core.exceptions import ValidationError

# Formatos permitidos para la planificación pedagógica (RF-13)
EXTENSIONES_PLANIFICACION = ("pdf", "docx")
# Formatos permitidos para el documento de acreditación (RNF-04)
EXTENSIONES_ACREDITACION = ("pdf", "jpg", "png")

FIRMAS = {
    "pdf": (b"%PDF-",),
    "docx": (b"PK\x03\x04",),  # un .docx es un archivo ZIP
    "png": (b"\x89PNG\r\n\x1a\n",),
    "jpg": (b"\xff\xd8\xff",),
}

TIPOS_MIME = {
    "pdf": ("application/pdf",),
    "docx": (
        "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        "application/octet-stream",
        "application/zip",
    ),
    "png": ("image/png",),
    "jpg": ("image/jpeg", "image/pjpeg"),
}


def tamano_maximo_bytes():
    return settings.TAMANO_MAXIMO_ARCHIVO_MB * 1024 * 1024


def obtener_extension(nombre):
    extension = Path(nombre or "").suffix.lower().lstrip(".")
    return "jpg" if extension == "jpeg" else extension


def validar_archivo(archivo, extensiones_permitidas):
    """
    Valida un archivo subido (UploadedFile). Devuelve la extensión normalizada.
    Lanza ValidationError con un mensaje claro para el usuario.
    """
    formatos = ", ".join(f".{e}" for e in extensiones_permitidas)
    extension = obtener_extension(archivo.name)

    # 1. Extensión
    if extension not in extensiones_permitidas:
        raise ValidationError(
            f"Formato no permitido. Formatos aceptados: {formatos}.", code="extension"
        )

    # 2. Tamaño
    if archivo.size == 0:
        raise ValidationError("El archivo está vacío.", code="vacio")
    if archivo.size > tamano_maximo_bytes():
        raise ValidationError(
            f"El archivo supera el tamaño máximo de {settings.TAMANO_MAXIMO_ARCHIVO_MB} MB.",
            code="tamano",
        )

    # 3. Tipo MIME declarado por el navegador (si viene informado)
    tipo = getattr(archivo, "content_type", None)
    if tipo and tipo not in TIPOS_MIME[extension]:
        raise ValidationError(
            "El tipo de archivo no corresponde a su extensión.", code="mime"
        )

    # 4. Firma del contenido (primeros bytes)
    archivo.seek(0)
    cabecera = archivo.read(8)
    archivo.seek(0)
    if not any(cabecera.startswith(firma) for firma in FIRMAS[extension]):
        raise ValidationError(
            "El contenido del archivo no corresponde a su extensión.", code="firma"
        )

    # Un .docx válido es un ZIP con word/document.xml y sin macros (vbaProject.bin)
    if extension == "docx":
        try:
            with zipfile.ZipFile(archivo) as zip_docx:
                nombres = set(zip_docx.namelist())
        except zipfile.BadZipFile:
            raise ValidationError("El documento Word está dañado.", code="docx_danado")
        finally:
            archivo.seek(0)
        if "word/document.xml" not in nombres:
            raise ValidationError("El archivo no es un documento Word válido.", code="docx")
        if any(n.lower().endswith("vbaproject.bin") for n in nombres):
            raise ValidationError("No se permiten documentos con macros.", code="macros")

    return extension
