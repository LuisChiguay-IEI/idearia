from django.contrib import admin

from .models import Ambito, Categoria, Material, Nucleo, Planificacion, PlanificacionCategoria


class NucleoInline(admin.TabularInline):
    model = Nucleo
    extra = 0


@admin.register(Ambito)
class AmbitoAdmin(admin.ModelAdmin):
    list_display = ("nombre", "orden", "icono")
    inlines = [NucleoInline]


@admin.register(Categoria)
class CategoriaAdmin(admin.ModelAdmin):
    search_fields = ("nombre",)


@admin.register(Material)
class MaterialAdmin(admin.ModelAdmin):
    search_fields = ("nombre",)


class PlanificacionCategoriaInline(admin.TabularInline):
    model = PlanificacionCategoria
    extra = 0


@admin.register(Planificacion)
class PlanificacionAdmin(admin.ModelAdmin):
    list_display = ("titulo", "colaborador", "estado", "nivel_educativo", "fecha_envio", "fecha_publicacion")
    list_filter = ("estado", "nivel_educativo", "edad_recomendada", "nucleo__ambito")
    search_fields = ("titulo", "colaborador__email", "colaborador__first_name")
    filter_horizontal = ("materiales",)
    inlines = [PlanificacionCategoriaInline]
    # El archivo no se reemplaza desde el admin técnico (la carga valida formato y contenido en el formulario del colaborador)
    readonly_fields = ("archivo", "nombre_archivo", "tipo_archivo", "tamano_archivo", "fecha_creacion",
                       "fecha_actualizacion", "fecha_envio", "fecha_publicacion")
