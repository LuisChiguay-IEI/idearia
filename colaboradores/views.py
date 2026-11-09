"""
Acreditación de Profesionales Colaboradores (RF-10, RF-11).

Flujo: el Educador envía su solicitud -> el Administrador la revisa ->
al aprobarla, el usuario pasa a rol Colaborador y puede crear propuestas.
"""

from pathlib import Path

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.db.models import Count
from django.http import FileResponse, Http404
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.utils.text import get_valid_filename
from django.views.decorators.http import require_POST

from core.auditoria import registrar_accion
from core.excepciones import TransicionInvalida
from core.models import RegistroAccion
from notificaciones.models import Notificacion
from notificaciones.servicios import notificar, notificar_administradores
from usuarios.permisos import administrador_requerido, educador_requerido

from .forms import ResolverSolicitudForm, SolicitudColaboradorForm
from .models import SolicitudColaborador

TIPOS_CONTENIDO = {".pdf": "application/pdf", ".png": "image/png", ".jpg": "image/jpeg", ".jpeg": "image/jpeg"}


def informacion(request):
    """Página pública "Zona colaborador": explica cómo aportar contenido."""
    return render(request, "colaboradores/informacion.html")


@login_required
def mi_solicitud(request):
    if request.user.es_administrador:
        return redirect("colaboradores:admin_lista")
    solicitudes = request.user.solicitudes_colaborador.all()
    return render(
        request,
        "colaboradores/mi_solicitud.html",
        {"solicitudes": solicitudes, "actual": solicitudes.first()},
    )


@educador_requerido
def nueva_solicitud(request):
    if request.user.solicitudes_colaborador.filter(estado__in=SolicitudColaborador.ESTADOS_ACTIVOS).exists():
        messages.info(request, "Ya tienes una solicitud en curso. Te avisaremos cuando sea revisada.")
        return redirect("colaboradores:mi_solicitud")

    if request.method == "POST":
        form = SolicitudColaboradorForm(request.POST, request.FILES)
        if form.is_valid():
            solicitud = form.save(commit=False)
            solicitud.usuario = request.user
            solicitud.nombre_archivo = get_valid_filename(Path(solicitud.documento_respaldo.name).name)[:200]
            solicitud.save()
            notificar_administradores(
                Notificacion.Tipo.NUEVA_SOLICITUD,
                f"{request.user.get_full_name()} solicitó acreditarse como Profesional Colaborador/a.",
                reverse("colaboradores:admin_detalle", args=[solicitud.pk]),
            )
            messages.success(request, "Tu solicitud fue enviada. Un administrador revisará tus antecedentes.")
            return redirect("colaboradores:mi_solicitud")
    else:
        form = SolicitudColaboradorForm()
    return render(request, "colaboradores/solicitud_form.html", {"form": form})


@login_required
def documento(request, pk):
    """Documento de acreditación: solo su dueño o un Administrador (RNF-03)."""
    solicitud = get_object_or_404(SolicitudColaborador, pk=pk)
    if not (request.user.es_administrador or solicitud.usuario_id == request.user.pk):
        raise Http404
    extension = Path(solicitud.documento_respaldo.name).suffix.lower()
    respuesta = FileResponse(
        solicitud.documento_respaldo.open("rb"),
        content_type=TIPOS_CONTENIDO.get(extension, "application/octet-stream"),
    )
    respuesta["Content-Disposition"] = f'inline; filename="acreditacion{extension}"'
    respuesta["Cache-Control"] = "no-store, private"
    return respuesta


@administrador_requerido
def admin_lista(request):
    todas = SolicitudColaborador.objects.select_related("usuario")
    conteos = {f["estado"]: f["total"] for f in todas.values("estado").annotate(total=Count("id"))}
    estado = request.GET.get("estado", "ACTIVAS")
    if estado == "ACTIVAS":
        lista = todas.filter(estado__in=SolicitudColaborador.ESTADOS_ACTIVOS)
    elif estado in SolicitudColaborador.Estado.values:
        lista = todas.filter(estado=estado)
    else:
        lista = todas
    pagina = Paginator(lista.order_by("fecha_solicitud" if estado == "ACTIVAS" else "-fecha_solicitud"), 15).get_page(
        request.GET.get("page")
    )
    activas = sum(conteos.get(e, 0) for e in SolicitudColaborador.ESTADOS_ACTIVOS)
    return render(
        request,
        "colaboradores/admin_lista.html",
        {
            "pagina": pagina,
            "estado_actual": estado,
            "pestanas": [("ACTIVAS", "Por revisar", activas)]
            + [(v, e, conteos.get(v, 0)) for v, e in SolicitudColaborador.Estado.choices]
            + [("TODAS", "Todas", sum(conteos.values()))],
        },
    )


@administrador_requerido
def admin_detalle(request, pk):
    solicitud = get_object_or_404(SolicitudColaborador.objects.select_related("usuario", "revisado_por"), pk=pk)
    return render(
        request,
        "colaboradores/admin_detalle.html",
        {
            "s": solicitud,
            "form": ResolverSolicitudForm(),
            "anteriores": solicitud.usuario.solicitudes_colaborador.exclude(pk=solicitud.pk),
            "es_pdf": solicitud.documento_respaldo.name.lower().endswith(".pdf"),
        },
    )


@administrador_requerido
@require_POST
def admin_resolver(request, pk):
    solicitud = get_object_or_404(SolicitudColaborador.objects.select_related("usuario"), pk=pk)
    form = ResolverSolicitudForm(request.POST)
    if not form.is_valid():
        for errores in form.errors.values():
            for error in errores:
                messages.error(request, error)
        return redirect("colaboradores:admin_detalle", pk=pk)

    accion = form.cleaned_data["accion"]
    observacion = form.cleaned_data["observacion"].strip()
    try:
        if accion == "revisar":
            solicitud.tomar_en_revision(request.user)
            registrar_accion(request, RegistroAccion.Accion.REVISAR_SOLICITUD, solicitud, solicitud.usuario.email)
            messages.success(request, "La solicitud quedó en revisión.")
        else:
            aprobar = accion == "aprobar"
            solicitud.resolver(request.user, aprobar, observacion)
            if aprobar:
                notificar(
                    solicitud.usuario,
                    Notificacion.Tipo.SOLICITUD_APROBADA,
                    "¡Tu acreditación fue aprobada! Ya puedes crear y enviar propuestas pedagógicas.",
                    reverse("planificaciones:panel_colaborador"),
                )
                registrar_accion(request, RegistroAccion.Accion.APROBAR_SOLICITUD, solicitud, solicitud.usuario.email)
                messages.success(request, f"{solicitud.usuario.get_full_name()} ahora es Profesional Colaborador/a.")
            else:
                notificar(
                    solicitud.usuario,
                    Notificacion.Tipo.SOLICITUD_RECHAZADA,
                    f"Tu solicitud de acreditación fue rechazada. Motivo: {observacion}",
                    reverse("colaboradores:mi_solicitud"),
                )
                registrar_accion(
                    request, RegistroAccion.Accion.RECHAZAR_SOLICITUD, solicitud,
                    f"{solicitud.usuario.email} | {observacion}",
                )
                messages.success(request, "La solicitud fue rechazada y se notificó al usuario.")
    except TransicionInvalida as error:
        messages.error(request, str(error))
    return redirect("colaboradores:admin_detalle", pk=pk)
