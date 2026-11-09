"""
Vistas del Profesional Colaborador/a (RF-12 a RF-14, RF-16 y RF-17 del Excel).

Solo usuarios con rol COLABORADOR (asignado al aprobarse su acreditación)
pueden crear propuestas. Cada colaborador solo ve y edita SUS propuestas:
si intenta abrir la de otro, recibe 404.
"""

from pathlib import Path

from django.contrib import messages
from django.db.models import Count
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.utils.text import get_valid_filename
from django.views.decorators.http import require_POST

from core.excepciones import TransicionInvalida
from core.validators import obtener_extension
from notificaciones.models import Notificacion
from notificaciones.servicios import notificar_administradores
from usuarios.permisos import colaborador_requerido

from .forms import PropuestaForm
from .models import Planificacion


@colaborador_requerido
def panel(request):
    propuestas = request.user.planificaciones.select_related("nucleo__ambito")
    conteos = {fila["estado"]: fila["total"] for fila in propuestas.values("estado").annotate(total=Count("id"))}
    return render(
        request,
        "planificaciones/colaborador/panel.html",
        {
            "conteos": [(valor, etiqueta, conteos.get(valor, 0)) for valor, etiqueta in Planificacion.Estado.choices],
            "total": sum(conteos.values()),
            "recientes": propuestas.order_by("-fecha_actualizacion")[:5],
            "por_corregir": propuestas.filter(estado=Planificacion.Estado.REQUIERE_CORRECCION),
        },
    )


@colaborador_requerido
def mis_propuestas(request):
    propuestas = request.user.planificaciones.select_related("nucleo__ambito").order_by("-fecha_actualizacion")
    estado = request.GET.get("estado", "")
    conteos = {fila["estado"]: fila["total"] for fila in propuestas.values("estado").annotate(total=Count("id"))}
    if estado in Planificacion.Estado.values:
        propuestas = propuestas.filter(estado=estado)
    return render(
        request,
        "planificaciones/colaborador/mis_propuestas.html",
        {
            "propuestas": propuestas,
            "estado_actual": estado,
            "pestanas": [(v, e, conteos.get(v, 0)) for v, e in Planificacion.Estado.choices if conteos.get(v)],
            "total": sum(conteos.values()),
        },
    )


@colaborador_requerido
def crear_propuesta(request):
    return _guardar_propuesta(request, Planificacion(colaborador=request.user))


@colaborador_requerido
def editar_propuesta(request, pk):
    propuesta = get_object_or_404(Planificacion, pk=pk, colaborador=request.user)
    if not propuesta.es_editable:
        messages.warning(
            request,
            f"La propuesta está en estado «{propuesta.get_estado_display()}» y no se puede editar.",
        )
        return redirect("planificaciones:mis_propuestas")
    return _guardar_propuesta(request, propuesta)


def _guardar_propuesta(request, propuesta):
    """Lógica común para crear y editar. El botón presionado define si se envía a revisión."""
    enviar = request.method == "POST" and request.POST.get("accion") == "enviar"
    archivo_anterior = propuesta.archivo.name if propuesta.archivo else ""

    if request.method == "POST":
        form = PropuestaForm(request.POST, request.FILES, instance=propuesta, enviar=enviar)
        if form.is_valid():
            propuesta = form.save(commit=False)
            nuevo_archivo = request.FILES.get("archivo")
            if nuevo_archivo:
                # Se guardan los datos del archivo; el nombre en disco es aleatorio (ver ruta_planificacion)
                propuesta.nombre_archivo = get_valid_filename(Path(nuevo_archivo.name).name)[:200]
                propuesta.tipo_archivo = obtener_extension(nuevo_archivo.name)
                propuesta.tamano_archivo = nuevo_archivo.size
            propuesta.save()
            form.save_m2m()
            if nuevo_archivo and archivo_anterior and archivo_anterior != propuesta.archivo.name:
                propuesta.archivo.storage.delete(archivo_anterior)

            if enviar:
                try:
                    propuesta.enviar_a_revision()
                except TransicionInvalida as error:
                    messages.warning(request, f"Se guardó como borrador, pero no se pudo enviar: {error}")
                    return redirect("planificaciones:editar_propuesta", pk=propuesta.pk)
                notificar_administradores(
                    Notificacion.Tipo.NUEVA_PROPUESTA,
                    f"{request.user.get_full_name()} envió a revisión «{propuesta.titulo}».",
                    reverse("planificaciones:admin_detalle", args=[propuesta.pk]),
                )
                messages.success(request, "Tu propuesta fue enviada a revisión. Te avisaremos cuando sea revisada.")
                return redirect("planificaciones:mis_propuestas")

            messages.success(request, "Borrador guardado correctamente.")
            return redirect("planificaciones:editar_propuesta", pk=propuesta.pk)
    else:
        form = PropuestaForm(instance=propuesta)

    return render(
        request,
        "planificaciones/colaborador/propuesta_form.html",
        {
            "form": form,
            "propuesta": propuesta,
            "recientes": request.user.planificaciones.order_by("-fecha_actualizacion")[:5],
        },
    )


@colaborador_requerido
@require_POST
def eliminar_propuesta(request, pk):
    propuesta = get_object_or_404(Planificacion, pk=pk, colaborador=request.user)
    if propuesta.estado != Planificacion.Estado.BORRADOR:
        messages.error(request, "Solo se pueden eliminar propuestas en estado Borrador.")
    else:
        if propuesta.archivo:
            propuesta.archivo.delete(save=False)
        propuesta.delete()
        messages.success(request, "Borrador eliminado.")
    return redirect("planificaciones:mis_propuestas")
