"""
Revisión de propuestas por el Administrador (RF-15, RF-16, RF-25 del Excel).

Cada decisión: cambia el estado, notifica al colaborador y queda en el
registro de acciones (auditoría).
"""

from django.contrib import messages
from django.core.paginator import Paginator
from django.db.models import Count, Q
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.views.decorators.http import require_POST

from colaboradores.models import SolicitudColaborador
from core.auditoria import registrar_accion
from core.excepciones import TransicionInvalida
from core.models import RegistroAccion
from notificaciones.models import Notificacion
from notificaciones.servicios import notificar
from usuarios.permisos import administrador_requerido

from .forms import AccionRevisionForm
from .models import Planificacion

# acción -> (tipo de notificación, acción de auditoría, mensaje para el colaborador, texto de éxito)
EFECTOS = {
    "aprobar": (
        Notificacion.Tipo.PROPUESTA_APROBADA, RegistroAccion.Accion.APROBAR_PROPUESTA,
        "Tu propuesta «{titulo}» fue aprobada y pronto será publicada.", "Propuesta aprobada.",
    ),
    "rechazar": (
        Notificacion.Tipo.PROPUESTA_RECHAZADA, RegistroAccion.Accion.RECHAZAR_PROPUESTA,
        "Tu propuesta «{titulo}» fue rechazada. Motivo: {obs}", "Propuesta rechazada.",
    ),
    "corregir": (
        Notificacion.Tipo.CORRECCION_SOLICITADA, RegistroAccion.Accion.SOLICITAR_CORRECCION,
        "Se solicitaron correcciones en «{titulo}»: {obs}", "Se solicitaron correcciones al colaborador.",
    ),
    "publicar": (
        Notificacion.Tipo.PROPUESTA_PUBLICADA, RegistroAccion.Accion.PUBLICAR_PROPUESTA,
        "¡Tu propuesta «{titulo}» ya está publicada en Idearia!", "Propuesta publicada en el catálogo.",
    ),
    "retirar": (
        Notificacion.Tipo.PROPUESTA_RETIRADA, RegistroAccion.Accion.RETIRAR_PROPUESTA,
        "Tu propuesta «{titulo}» fue retirada del catálogo. Motivo: {obs}", "Propuesta retirada del catálogo.",
    ),
    "republicar": (
        Notificacion.Tipo.PROPUESTA_PUBLICADA, RegistroAccion.Accion.REPUBLICAR_PROPUESTA,
        "Tu propuesta «{titulo}» volvió a publicarse.", "Propuesta publicada nuevamente.",
    ),
}

ESTADOS_REVISION = [e for e in Planificacion.Estado.choices if e[0] != Planificacion.Estado.BORRADOR]


@administrador_requerido
def revision(request):
    """Lista de propuestas (izquierda) + detalle de la seleccionada (derecha)."""
    base = Planificacion.objects.exclude(estado=Planificacion.Estado.BORRADOR).select_related(
        "colaborador", "nucleo__ambito", "revisado_por"
    )
    conteos = {f["estado"]: f["total"] for f in base.values("estado").annotate(total=Count("id"))}

    estado = request.GET.get("estado", Planificacion.Estado.EN_REVISION)
    lista = base if estado == "TODAS" else base.filter(estado=estado)
    q = request.GET.get("q", "").strip()
    if q:
        lista = lista.filter(
            Q(titulo__icontains=q)
            | Q(colaborador__first_name__icontains=q)
            | Q(colaborador__last_name__icontains=q)
            | Q(colaborador__email__icontains=q)
        )
    lista = lista.order_by("-fecha_envio", "-pk")
    pagina = Paginator(lista, 8).get_page(request.GET.get("page"))

    seleccion = None
    if request.GET.get("id", "").isdigit():
        seleccion = base.filter(pk=request.GET["id"]).first()
    if seleccion is None and pagina.object_list:
        seleccion = pagina.object_list[0]

    contexto = {
        "pagina": pagina,
        "estado_actual": estado,
        "q": q,
        "pestanas": [(v, e, conteos.get(v, 0)) for v, e in ESTADOS_REVISION],
        "total": sum(conteos.values()),
        "seleccion": seleccion,
        "form": AccionRevisionForm(),
    }
    if seleccion:
        contexto["faltantes"] = seleccion.campos_faltantes()
        contexto["acreditacion"] = seleccion.colaborador.solicitudes_colaborador.filter(
            estado=SolicitudColaborador.Estado.APROBADA
        ).first()
        contexto["acciones_disponibles"] = [
            accion for accion, (origenes, _) in Planificacion.ACCIONES_REVISION.items()
            if seleccion.estado in origenes
        ]
    return render(request, "planificaciones/admin/revision.html", contexto)


@administrador_requerido
def detalle_revision(request, pk):
    """Enlace directo (usado en notificaciones): abre la revisión con la propuesta seleccionada."""
    propuesta = get_object_or_404(Planificacion.objects.exclude(estado=Planificacion.Estado.BORRADOR), pk=pk)
    return redirect(f"{reverse('planificaciones:admin_revision')}?estado={propuesta.estado}&id={propuesta.pk}")


@administrador_requerido
@require_POST
def accion_revision(request, pk):
    propuesta = get_object_or_404(Planificacion.objects.exclude(estado=Planificacion.Estado.BORRADOR), pk=pk)
    form = AccionRevisionForm(request.POST)
    if not form.is_valid():
        for errores in form.errors.values():
            for error in errores:
                messages.error(request, error)
        return redirect("planificaciones:admin_detalle", pk=propuesta.pk)

    accion = form.cleaned_data["accion"]
    observacion = form.cleaned_data["observacion"].strip()
    try:
        propuesta.aplicar_accion_revision(accion, request.user, observacion)
    except TransicionInvalida as error:
        messages.error(request, str(error))
        return redirect("planificaciones:admin_detalle", pk=propuesta.pk)

    tipo, accion_auditoria, plantilla, exito = EFECTOS[accion]
    enlace = (
        reverse("planificaciones:editar_propuesta", args=[propuesta.pk])
        if accion == "corregir"
        else reverse("planificaciones:mis_propuestas")
    )
    notificar(propuesta.colaborador, tipo, plantilla.format(titulo=propuesta.titulo, obs=observacion), enlace)
    registrar_accion(request, accion_auditoria, propuesta, f"{propuesta.titulo} | {observacion}")
    messages.success(request, exito)
    return redirect("planificaciones:admin_detalle", pk=propuesta.pk)
