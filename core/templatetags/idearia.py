"""Etiquetas de plantilla propias de Idearia."""

from django import template
from django.templatetags.static import static
from django.utils.html import format_html

register = template.Library()


@register.simple_tag
def icono(nombre, clase=""):
    """Inserta un ícono SVG del archivo static/img/iconos.svg. Uso: {% icono "buscar" %}"""
    return format_html(
        '<svg class="icono {}" aria-hidden="true" focusable="false"><use href="{}#i-{}"></use></svg>',
        clase,
        static("img/iconos.svg"),
        nombre,
    )


@register.inclusion_tag("core/_estrellas.html")
def estrellas(promedio):
    """Muestra 5 estrellas según el promedio (redondeado)."""
    valor = int(round(promedio or 0))
    return {"llenas": range(valor), "vacias": range(5 - valor), "promedio": promedio or 0}


@register.simple_tag(takes_context=True)
def activo(context, *nombres_url):
    """Devuelve 'activo' si la página actual corresponde a alguno de los nombres de URL."""
    request = context.get("request")
    coincidencia = getattr(request, "resolver_match", None)
    if coincidencia and coincidencia.view_name in nombres_url:
        return "activo"
    return ""


@register.filter
def tema(planificacion):
    """Clase de color según el ámbito de la idea (tema-1, tema-2, tema-3)."""
    if planificacion.nucleo_id:
        return f"tema-{planificacion.nucleo.ambito.orden}"
    return "tema-0"


@register.filter
def icono_ambito(planificacion):
    if planificacion.nucleo_id:
        return planificacion.nucleo.ambito.icono
    return "bombilla"
