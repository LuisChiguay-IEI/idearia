"""
Almacenamiento protegido de archivos de Idearia.

Modos disponibles:

- disco: desarrollo local mediante FileSystemStorage.
- bd: todos los archivos se guardan en PostgreSQL/Supabase.
- hibrido: las portadas se guardan como objetos en Supabase Storage y
  el resto de los archivos continúa en PostgreSQL.

El modo híbrido permite demostrar almacenamiento relacional y almacenamiento
de objetos en la nube sin exponer URLs públicas. Las vistas de Idearia siguen
comprobando sesión y permisos antes de entregar cada archivo.
"""

import mimetypes
from pathlib import PurePosixPath

from django.conf import settings
from django.core.files.base import ContentFile
from django.core.files.storage import Storage
from django.utils.deconstruct import deconstructible
from supabase import create_client


@deconstructible
class AlmacenamientoBD(Storage):
    """Guarda el contenido binario en la tabla core_archivoalmacenado."""

    def _modelo(self):
        from core.models import ArchivoAlmacenado

        return ArchivoAlmacenado

    def _open(self, name, mode="rb"):
        archivo = self._modelo().objects.get(nombre=name)
        return ContentFile(bytes(archivo.contenido), name=name)

    def _save(self, name, content):
        content.seek(0)
        datos = content.read()
        self._modelo().objects.update_or_create(
            nombre=name,
            defaults={
                "contenido": datos,
                "tamano": len(datos),
            },
        )
        return name

    def exists(self, name):
        return self._modelo().objects.filter(nombre=name).exists()

    def delete(self, name):
        self._modelo().objects.filter(nombre=name).delete()

    def size(self, name):
        return self._modelo().objects.values_list(
            "tamano",
            flat=True,
        ).get(nombre=name)

    def url(self, name):
        raise NotImplementedError(
            "Los archivos protegidos de Idearia no tienen URL pública."
        )


@deconstructible
class AlmacenamientoSupabase(Storage):
    """
    Guarda objetos en un bucket privado de Supabase Storage.

    Se usa únicamente desde el backend de Django con una Secret Key.
    Esa clave nunca se expone al navegador ni se guarda en Git.
    """

    def __init__(self):
        self._cliente_supabase = None
        self._bucket_supabase = None

    def _bucket(self):
        if self._bucket_supabase is None:
            self._cliente_supabase = create_client(
                settings.SUPABASE_URL,
                settings.SUPABASE_SECRET_KEY,
            )
            self._bucket_supabase = self._cliente_supabase.storage.from_(
                settings.SUPABASE_STORAGE_BUCKET
            )
        return self._bucket_supabase

    @staticmethod
    def _partes(name):
        ruta = PurePosixPath(name)
        carpeta = "" if str(ruta.parent) == "." else str(ruta.parent)
        return carpeta, ruta.name

    def _metadata(self, name):
        carpeta, archivo_buscado = self._partes(name)
        resultados = self._bucket().list(
            carpeta,
            {
                "limit": 100,
                "offset": 0,
                "search": archivo_buscado,
            },
        )

        for item in resultados or []:
            if isinstance(item, dict):
                nombre = item.get("name")
            else:
                nombre = getattr(item, "name", None)

            if nombre == archivo_buscado:
                return item

        return None

    def _open(self, name, mode="rb"):
        datos = self._bucket().download(name)
        return ContentFile(datos, name=name)

    def _save(self, name, content):
        content.seek(0)
        datos = content.read()

        tipo_mime = (
            getattr(content, "content_type", None)
            or mimetypes.guess_type(name)[0]
            or "application/octet-stream"
        )

        self._bucket().upload(
            path=name,
            file=datos,
            file_options={
                "content-type": tipo_mime,
                "cache-control": "300",
                "upsert": "false",
            },
        )

        return name

    def exists(self, name):
        return self._metadata(name) is not None

    def delete(self, name):
        if self.exists(name):
            self._bucket().remove([name])

    def size(self, name):
        item = self._metadata(name)

        if item is None:
            raise FileNotFoundError(name)

        metadata = (
            item.get("metadata", {})
            if isinstance(item, dict)
            else getattr(item, "metadata", {}) or {}
        )

        if isinstance(metadata, dict) and metadata.get("size") is not None:
            return int(metadata["size"])

        return len(self._bucket().download(name))

    def url(self, name):
        raise NotImplementedError(
            "Las portadas están en un bucket privado y no tienen URL pública."
        )


@deconstructible
class AlmacenamientoHibrido(Storage):
    """
    En producción:

    - portadas/* -> Supabase Storage (objetos no relacionales);
    - demás archivos -> PostgreSQL mediante AlmacenamientoBD.

    Para compatibilidad, una portada antigua que todavía esté almacenada
    en PostgreSQL se puede seguir leyendo y eliminando.
    """

    PREFIJO_PORTADAS = "portadas/"

    def __init__(self):
        self.bd = AlmacenamientoBD()
        self.supabase = AlmacenamientoSupabase()

    @classmethod
    def _es_portada(cls, name):
        return str(name).replace("\\", "/").startswith(cls.PREFIJO_PORTADAS)

    def _open(self, name, mode="rb"):
        if self._es_portada(name):
            # Intentamos descargar directamente desde Supabase Storage.
            # Así evitamos una petición previa de "exists" por cada imagen,
            # reduciendo a la mitad las llamadas remotas del catálogo.
            try:
                return self.supabase.open(name, mode)
            except Exception:
                # Compatibilidad con portadas antiguas que todavía están
                # almacenadas en PostgreSQL.
                if self.bd.exists(name):
                    return self.bd.open(name, mode)
                raise

        return self.bd.open(name, mode)

    def _save(self, name, content):
        if self._es_portada(name):
            return self.supabase.save(name, content)

        return self.bd.save(name, content)

    def exists(self, name):
        if self._es_portada(name):
            return self.supabase.exists(name) or self.bd.exists(name)

        return self.bd.exists(name)

    def delete(self, name):
        if self._es_portada(name):
            if self.supabase.exists(name):
                self.supabase.delete(name)
            if self.bd.exists(name):
                self.bd.delete(name)
            return

        self.bd.delete(name)

    def size(self, name):
        if self._es_portada(name):
            if self.supabase.exists(name):
                return self.supabase.size(name)
            return self.bd.size(name)

        return self.bd.size(name)

    def url(self, name):
        raise NotImplementedError(
            "Los archivos protegidos de Idearia no tienen URL pública."
        )
