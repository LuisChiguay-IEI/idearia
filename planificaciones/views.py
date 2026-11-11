"""
Vistas del catálogo para usuarios con sesión
(Educador/a, Colaborador/a, Administrador/a).

Incluye:

- catálogo de ideas;
- detalle de planificación;
- visor interno de planificación;
- entrega protegida de documentos PDF;
- entrega protegida de imágenes de portada.
"""

from pathlib import Path

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


# =========================================================
# CATÁLOGO
# =========================================================

@login_required
def catalogo(request):
    """
    Muestra las ideas pedagógicas publicadas.

    Permite:

    - búsqueda;
    - filtros;
    - paginación;
    - favoritos.
    """

    form = FiltroCatalogoForm(
        request.GET
    )

    # Si alguien manipula manualmente la URL con valores
    # inválidos, esos valores simplemente se ignoran.
    form.is_valid()

    resultados = buscar_planificaciones(
        form.cleaned_data
    )

    pagina = Paginator(
        resultados,
        9,
    ).get_page(
        request.GET.get("page")
    )

    favoritos = set(
        Favorito.objects.filter(
            usuario=request.user
        ).values_list(
            "planificacion_id",
            flat=True,
        )
    )

    return render(
        request,
        "planificaciones/catalogo.html",
        {
            "form": form,
            "pagina": pagina,
            "chips": filtros_activos(
                request.GET,
                form,
            ),
            "favoritos": favoritos,
        },
    )


# =========================================================
# OBTENER PLANIFICACIÓN VISIBLE
# =========================================================

def _obtener_visible(request, pk):
    """
    Devuelve una planificación solamente si el usuario
    tiene permiso para verla.

    Si no tiene permiso, responde con 404 para no revelar
    que la propuesta existe.
    """

    planificacion = get_object_or_404(
        Planificacion.objects.select_related(
            "colaborador",
            "nucleo__ambito",
            "revisado_por",
        ),
        pk=pk,
    )

    if not planificacion.puede_ver(
        request.user
    ):
        raise Http404(
            "La idea no existe o ya no está disponible."
        )

    return planificacion


# =========================================================
# DETALLE DE LA IDEA
# =========================================================

@login_required
def detalle(request, pk):
    """
    Muestra el detalle completo de una propuesta pedagógica.
    """

    planificacion = _obtener_visible(
        request,
        pk,
    )

    comentarios = (
        planificacion
        .comentarios
        .select_related("usuario")
    )

    if not request.user.es_administrador:
        comentarios = comentarios.filter(
            estado=Comentario.Estado.VISIBLE
        )

    resumen = planificacion.valoraciones.aggregate(
        promedio=Avg("puntuacion"),
        total=Count("id"),
    )

    mi_valoracion = Valoracion.objects.filter(
        usuario=request.user,
        planificacion=planificacion,
    ).first()

    return render(
        request,
        "planificaciones/detalle.html",
        {
            "p": planificacion,

            "comentarios": comentarios,

            "resumen": resumen,

            "mi_valoracion": mi_valoracion,

            "es_favorito": Favorito.objects.filter(
                usuario=request.user,
                planificacion=planificacion,
            ).exists(),

            "form_valoracion": ValoracionForm(
                initial={
                    "puntuacion": getattr(
                        mi_valoracion,
                        "puntuacion",
                        None,
                    )
                }
            ),

            "form_comentario": ComentarioForm(),

            "es_autor": (
                planificacion.colaborador_id
                == request.user.pk
            ),
        },
    )


# =========================================================
# IMAGEN DE PORTADA
# =========================================================

@login_required
def imagen_portada(request, pk):
    """
    Entrega la imagen de portada de una propuesta.

    La imagen NO posee una URL pública directa.

    Antes de entregar el archivo se comprueba:

    - que el usuario tenga una sesión iniciada;
    - que tenga permiso para ver la planificación;
    - que realmente exista una imagen asociada;
    - que el formato corresponda a JPG o PNG.

    Esto permite utilizar las imágenes tanto:

    - en el catálogo;
    - en el detalle;
    - en la revisión administrativa;
    - en la vista del propio colaborador.

    Las propuestas no publicadas continúan protegidas:
    solamente pueden verlas su autor y los Administradores.
    """

    planificacion = _obtener_visible(
        request,
        pk,
    )

    if not planificacion.imagen_portada:
        raise Http404(
            "Esta propuesta no tiene imagen de portada."
        )

    tipos = {
        "jpg": "image/jpeg",
        "jpeg": "image/jpeg",
        "png": "image/png",
    }

    extension = (
        planificacion.tipo_imagen
        or Path(
            planificacion.imagen_portada.name
        ).suffix.lower().lstrip(".")
    )

    content_type = tipos.get(
        extension
    )

    if not content_type:
        raise Http404(
            "Formato de imagen no válido."
        )

    try:
        archivo = planificacion.imagen_portada.open(
            "rb"
        )

    except (FileNotFoundError, OSError):
        raise Http404(
            "La imagen de portada no está disponible."
        )

    respuesta = FileResponse(
        archivo,
        content_type=content_type,
    )

    respuesta["Content-Disposition"] = (
        f'inline; filename="portada.{extension}"'
    )

    # Evita que una imagen reemplazada siga apareciendo
    # desde la caché del navegador.
    respuesta["Cache-Control"] = (
        "no-store, private"
    )

    # Evita que el navegador intente interpretar
    # el archivo como otro tipo de contenido.
    respuesta["X-Content-Type-Options"] = (
        "nosniff"
    )

    return respuesta


# =========================================================
# VISOR DE PLANIFICACIÓN
# =========================================================

@login_required
def visor(request, pk):
    """
    Visualización de la planificación dentro de Idearia.

    No presenta una opción directa de descarga.
    """

    planificacion = _obtener_visible(
        request,
        pk,
    )

    if not planificacion.archivo:
        raise Http404(
            "Esta propuesta no tiene planificación adjunta."
        )

    contenido_docx = None

    if planificacion.tipo_archivo == "docx":
        contenido_docx = docx_a_html(
            planificacion.archivo
        )

    return render(
        request,
        "planificaciones/visor.html",
        {
            "p": planificacion,
            "contenido_docx": contenido_docx,
        },
    )


# =========================================================
# DOCUMENTO PDF PROTEGIDO
# =========================================================

@login_required
def documento_pdf(request, pk):
    """
    Entrega los bytes del PDF solamente al visor de Idearia.

    Seguridad:

    - exige sesión iniciada;
    - verifica permisos sobre la propuesta;
    - exige la cabecera X-Idearia-Visor;
    - abrir directamente la URL devuelve 403;
    - el archivo se entrega en modo inline;
    - no se almacena en caché.
    """

    planificacion = _obtener_visible(
        request,
        pk,
    )

    if (
        not planificacion.archivo
        or planificacion.tipo_archivo != "pdf"
    ):
        raise Http404

    if (
        request.headers.get(
            CABECERA_VISOR
        )
        != "1"
    ):
        raise PermissionDenied(
            "La planificación solo puede visualizarse desde Idearia."
        )

    respuesta = FileResponse(
        planificacion.archivo.open("rb"),
        content_type="application/pdf",
    )

    respuesta["Content-Disposition"] = (
        'inline; filename="planificacion.pdf"'
    )

    respuesta["Cache-Control"] = (
        "no-store, private"
    )

    respuesta["X-Content-Type-Options"] = (
        "nosniff"
    )

    return respuesta