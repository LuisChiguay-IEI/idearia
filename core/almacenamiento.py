"""
Almacenamiento de archivos en la base de datos (tabla core_archivoalmacenado).

Django guarda los archivos de los FileField mediante una clase "Storage".
Por defecto usa el disco (carpeta media_protegida/). En un hosting como Render
el disco gratuito se borra al reiniciar, por lo que con ALMACENAMIENTO_ARCHIVOS="bd"
se usa esta clase: el contenido queda en Supabase, con la misma protección
(usuario propio, RLS, SSL) que el resto de los datos.

Los archivos nunca tienen URL pública: solo se entregan por las vistas
que comprueban sesión y permisos.
"""

from django.core.files.base import ContentFile
from django.core.files.storage import Storage
from django.utils.deconstruct import deconstructible


@deconstructible
class AlmacenamientoBD(Storage):
    def _modelo(self):
        from core.models import ArchivoAlmacenado  # import diferido (evita ciclos al iniciar Django)

        return ArchivoAlmacenado

    def _open(self, name, mode="rb"):
        archivo = self._modelo().objects.get(nombre=name)
        contenido = ContentFile(bytes(archivo.contenido), name=name)
        return contenido

    def _save(self, name, content):
        content.seek(0)
        datos = content.read()
        self._modelo().objects.update_or_create(
            nombre=name, defaults={"contenido": datos, "tamano": len(datos)}
        )
        return name

    def exists(self, name):
        return self._modelo().objects.filter(nombre=name).exists()

    def delete(self, name):
        self._modelo().objects.filter(nombre=name).delete()

    def size(self, name):
        return self._modelo().objects.values_list("tamano", flat=True).get(nombre=name)

    def url(self, name):
        raise NotImplementedError("Los archivos de Idearia no tienen URL pública.")
