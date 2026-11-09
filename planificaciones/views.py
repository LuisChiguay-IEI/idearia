"""
Vistas del catálogo para usuarios con sesión (Educador/a, Colaborador/a, Administrador/a):
búsqueda, detalle y visor de planificación (RF-03 a RF-06).
"""

from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied
from django.core.paginator import Paginator
from django.db.models import Avg, Count
from django.http import FileResponse, Http404
from django.shortcuts import get_object_or_404, render

from interacciones.forms import ComentarioForm, ValoracionForm
from interacciones.models import Comentario, Favorito, Valoracion

from .busqueda import buscar_planificaciones, filtros_activos
from .forms import FiltroCatalogoForm
from .models import Planificacion
from .visor import docx_a_html

CABECERA_VISOR = "X-Idearia-Visor"


@login_required
def catalogo(request):
    form = FiltroCatalogoForm(request.GET)
    form.is_valid()  # los valores inválidos (ej. URL manipulada) simplemente se ignoran
    resultados = buscar_planificaciones(form.cleaned_data)
    pagina = Paginator(resultados, 9).get_page(request.GET.get("page"))
    favoritos = set(
        Favorito.objects.filter(usuario=request.user).values_list("planificacion_id", flat=True)
    )
    return render(
        request,
        "planificaciones/catalogo.html",
        {
            "form": form,
            "pagina": pagina,
            "chips": filtros_activos(request.GET, form),
            "favoritos": favoritos,
        },
    )


def _obtener_visible(request, pk):
    """Devuelve la planificación si el usuario puede verla; si no, 404 (no revela que existe)."""
    planificacion = get_object_or_404(
        Planificacion.objects.select_related("colaborador", "nucleo__ambito", "revisado_por"), pk=pk
    )
    if not planificacion.puede_ver(request.user):
        raise Http404("La idea no existe o ya no está disponible.")
    return planificacion


@login_required
def detalle(request, pk):
    planificacion = _obtener_visible(request, pk)
    comentarios = planificacion.comentarios.select_related("usuario")
    if not request.user.es_administrador:
        comentarios = comentarios.filter(estado=Comentario.Estado.VISIBLE)
    resumen = planificacion.valoraciones.aggregate(promedio=Avg("puntuacion"), total=Count("id"))
    mi_valoracion = Valoracion.objects.filter(usuario=request.user, planificacion=planificacion).first()
    return render(
        request,
        "planificaciones/detalle.html",
        {
            "p": planificacion,
            "comentarios": comentarios,
            "resumen": resumen,
            "mi_valoracion": mi_valoracion,
            "es_favorito": Favorito.objects.filter(usuario=request.user, planificacion=planificacion).exists(),
            "form_valoracion": ValoracionForm(initial={"puntuacion": getattr(mi_valoracion, "puntuacion", None)}),
            "form_comentario": ComentarioForm(),
            "es_autor": planificacion.colaborador_id == request.user.pk,
        },
    )


@login_required
def visor(request, pk):
    """Visualización de la planificación dentro de Idearia, sin opción de descarga (RF-06)."""
    planificacion = _obtener_visible(request, pk)
    if not planificacion.archivo:
        raise Http404("Esta propuesta no tiene planificación adjunta.")
    contenido_docx = None
    if planificacion.tipo_archivo == "docx":
        contenido_docx = docx_a_html(planificacion.archivo)
    return render(
        request,
        "planificaciones/visor.html",
        {"p": planificacion, "contenido_docx": contenido_docx},
    )


@login_required
def documento_pdf(request, pk):
    """
    Entrega los bytes del PDF SOLO al visor de Idearia.
    - Exige sesión y permiso de lectura.
    - Exige la cabecera X-Idearia-Visor (abrir la URL directamente devuelve 403).
    - Content-Disposition "inline" + Cache-Control "no-store".
    """
    planificacion = _obtener_visible(request, pk)
    if not planificacion.archivo or planificacion.tipo_archivo != "pdf":
        raise Http404
    if request.headers.get(CABECERA_VISOR) != "1":
        raise PermissionDenied("La planificación solo puede visualizarse desde Idearia.")
    respuesta = FileResponse(planificacion.archivo.open("rb"), content_type="application/pdf")
    respuesta["Content-Disposition"] = 'inline; filename="planificacion.pdf"'
    respuesta["Cache-Control"] = "no-store, private"
    return respuesta
