from django.contrib import admin

from .models import Comentario, Favorito, Valoracion


@admin.register(Favorito)
class FavoritoAdmin(admin.ModelAdmin):
    list_display = ("usuario", "planificacion", "fecha_registro")


@admin.register(Valoracion)
class ValoracionAdmin(admin.ModelAdmin):
    list_display = ("usuario", "planificacion", "puntuacion", "fecha_valoracion")
    list_filter = ("puntuacion",)


@admin.register(Comentario)
class ComentarioAdmin(admin.ModelAdmin):
    list_display = ("usuario", "planificacion", "estado", "fecha_comentario")
    list_filter = ("estado",)
    search_fields = ("contenido", "usuario__email")
