"""
Búsqueda y filtros del catálogo (RF-01 a RF-05, RF-16).

Regla principal: el catálogo SOLO muestra propuestas en estado Publicada.
"""

from django.db.models import Avg, Count, F, Q

from .models import Material, Planificacion

CAMPOS_FILTRO = ("q", "nivel", "edad", "ambito", "nucleo", "oa", "duracion", "materiales", "categoria")


def buscar_planificaciones(datos):
    """Recibe los datos limpios del FiltroCatalogoForm y devuelve el QuerySet filtrado."""
    consulta = Planificacion.objects.filter(estado=Planificacion.Estado.PUBLICADA)

    texto = (datos.get("q") or "").strip()
    if texto:
        # Subconsulta: evita filas duplicadas al buscar también en materiales y categorías
        coincidencias = Planificacion.objects.filter(
            Q(titulo__icontains=texto)
            | Q(descripcion__icontains=texto)
            | Q(objetivo_aprendizaje__icontains=texto)
            | Q(materiales__nombre__icontains=texto)
            | Q(categorias__nombre__icontains=texto)
        ).values("pk")
        consulta = consulta.filter(pk__in=coincidencias)

    if datos.get("nivel"):
        consulta = consulta.filter(nivel_educativo__in=datos["nivel"])
    if datos.get("edad"):
        consulta = consulta.filter(edad_recomendada__in=datos["edad"])
    if datos.get("ambito"):
        consulta = consulta.filter(nucleo__ambito=datos["ambito"])
    if datos.get("nucleo"):
        consulta = consulta.filter(nucleo=datos["nucleo"])
    if datos.get("oa"):
        consulta = consulta.filter(objetivo_aprendizaje__icontains=datos["oa"].strip())

    if datos.get("duracion"):
        rangos = Q()
        if "corta" in datos["duracion"]:
            rangos |= Q(duracion_minutos__lt=30)
        if "media" in datos["duracion"]:
            rangos |= Q(duracion_minutos__gte=30, duracion_minutos__lte=60)
        if "larga" in datos["duracion"]:
            rangos |= Q(duracion_minutos__gt=60)
        consulta = consulta.filter(rangos)

    if datos.get("materiales"):
        # "Lo que puedo hacer con lo que tengo": se excluyen las ideas que
        # requieren algún material que NO fue marcado.
        no_disponibles = Material.objects.exclude(pk__in=[m.pk for m in datos["materiales"]])
        consulta = consulta.exclude(materiales__in=no_disponibles)

    if datos.get("categoria"):
        consulta = consulta.filter(
            pk__in=Planificacion.objects.filter(categorias=datos["categoria"]).values("pk")
        )

    consulta = consulta.annotate(
        promedio=Avg("valoraciones__puntuacion"),
        total_valoraciones=Count("valoraciones", distinct=True),
    ).select_related("colaborador", "nucleo__ambito").prefetch_related("categorias")

    orden = datos.get("orden") or "recientes"
    if orden == "valoradas":
        consulta = consulta.order_by(F("promedio").desc(nulls_last=True), "-total_valoraciones", "titulo")
    elif orden == "titulo":
        consulta = consulta.order_by("titulo")
    else:
        consulta = consulta.order_by("-fecha_publicacion", "-pk")
    return consulta


def filtros_activos(parametros, form):
    """
    Lista de filtros aplicados para mostrarlos como "chips" (RNF-12).
    Cada chip trae la URL que quita SOLO ese filtro (1 clic).
    """
    chips = []
    for nombre in CAMPOS_FILTRO:
        for valor in parametros.getlist(nombre):
            if not valor:
                continue
            etiqueta = _etiqueta(form.fields[nombre], nombre, valor)
            if etiqueta is None:
                continue
            copia = parametros.copy()
            copia.setlist(nombre, [v for v in parametros.getlist(nombre) if v != valor])
            copia.pop("page", None)
            chips.append({"etiqueta": etiqueta, "url": "?" + copia.urlencode()})
    return chips


def _etiqueta(campo, nombre, valor):
    if nombre in ("q", "oa"):
        return f"«{valor}»"
    if hasattr(campo, "queryset"):
        objeto = campo.queryset.filter(pk=valor).first() if valor.isdigit() else None
        return str(objeto) if objeto else None
    return dict(campo.choices).get(valor)
