"""
Favoritos (RF-07/08), valoraciones y comentarios (RF-09/10).
Solo sobre ideas PUBLICADAS y solo para Educador/a o Colaborador/a.
"""

from django.contrib import messages
from django.core.paginator import Paginator
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.views.decorators.http import require_POST

from core.auditoria import registrar_accion
from core.models import RegistroAccion
from core.utils import redireccion_segura
from planificaciones.models import Planificacion
from usuarios.permisos import administrador_requerido, interaccion_requerida

from .forms import ComentarioForm, ValoracionForm
from .models import Comentario, Favorito, Valoracion


def _publicada(pk):
    return get_object_or_404(Planificacion, pk=pk, estado=Planificacion.Estado.PUBLICADA)


def planificacion_url(planificacion):
    return reverse("planificaciones:detalle", args=[planificacion.pk])


@interaccion_requerida
@require_POST
def favorito(request, pk):
    if request.POST.get("accion") == "quitar":
        # Quitar funciona aunque la idea ya no esté publicada
        Favorito.objects.filter(usuario=request.user, planificacion_id=pk).delete()
        messages.info(request, "La idea se quitó de tus favoritos.")
        return redireccion_segura(request, request.POST.get("volver"), reverse("interacciones:mis_favoritos"))

    planificacion = _publicada(pk)
    # get_or_create: si ya existe, no se duplica (además hay una restricción única en la BD)
    _, creado = Favorito.objects.get_or_create(usuario=request.user, planificacion=planificacion)
    messages.success(request, "Idea guardada en tus favoritos." if creado else "Esta idea ya estaba en tus favoritos.")
    return redireccion_segura(request, request.POST.get("volver"), planificacion_url(planificacion))


@interaccion_requerida
@require_POST
def valorar(request, pk):
    planificacion = _publicada(pk)
    if planificacion.colaborador_id == request.user.pk:
        messages.error(request, "No puedes valorar tu propia propuesta.")
        return redirect(planificacion_url(planificacion))
    form = ValoracionForm(request.POST)
    if form.is_valid():
        # update_or_create: una sola valoración por usuario; si vuelve a valorar, se actualiza
        _, creada = Valoracion.objects.update_or_create(
            usuario=request.user,
            planificacion=planificacion,
            defaults={"puntuacion": form.cleaned_data["puntuacion"]},
        )
        messages.success(request, "¡Gracias por tu valoración!" if creada else "Tu valoración fue actualizada.")
    else:
        messages.error(request, form.errors["puntuacion"][0])
    return redirect(planificacion_url(planificacion) + "#valoracion")


@interaccion_requerida
@require_POST
def comentar(request, pk):
    planificacion = _publicada(pk)
    form = ComentarioForm(request.POST)
    if form.is_valid():
        comentario = form.save(commit=False)
        comentario.usuario = request.user
        comentario.planificacion = planificacion
        comentario.save()
        messages.success(request, "Tu comentario fue publicado.")
    else:
        messages.error(request, form.errors["contenido"][0])
    return redirect(planificacion_url(planificacion) + "#comentarios")


@administrador_requerido
@require_POST
def moderar_comentario(request, pk):
    comentario = get_object_or_404(Comentario, pk=pk)
    if comentario.estado == Comentario.Estado.VISIBLE:
        comentario.estado = Comentario.Estado.OCULTO
        accion = RegistroAccion.Accion.OCULTAR_COMENTARIO
        messages.success(request, "Comentario ocultado.")
    else:
        comentario.estado = Comentario.Estado.VISIBLE
        accion = RegistroAccion.Accion.MOSTRAR_COMENTARIO
        messages.success(request, "Comentario visible nuevamente.")
    comentario.save(update_fields=["estado"])
    registrar_accion(request, accion, comentario, comentario.contenido[:120])
    return redirect(planificacion_url(comentario.planificacion) + "#comentarios")


@interaccion_requerida
def mis_favoritos(request):
    favoritos = (
        Favorito.objects.filter(usuario=request.user)
        .select_related("planificacion__colaborador", "planificacion__nucleo__ambito")
        .order_by("-fecha_registro")
    )
    pagina = Paginator(favoritos, 9).get_page(request.GET.get("page"))
    return render(request, "interacciones/favoritos.html", {"pagina": pagina})
