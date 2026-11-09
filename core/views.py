"""Inicio, panel del Administrador y registro de acciones."""

from django.core.paginator import Paginator
from django.db.models import Count
from django.shortcuts import redirect, render

from colaboradores.models import SolicitudColaborador
from planificaciones.models import Planificacion
from usuarios.models import Usuario
from usuarios.permisos import administrador_requerido

from .models import RegistroAccion


def inicio(request):
    """Lleva a cada usuario a la pantalla que corresponde a su rol (RF-02)."""
    if not request.user.is_authenticated:
        return redirect("usuarios:login")
    if request.user.es_administrador:
        return redirect("core:panel_admin")
    return redirect("planificaciones:catalogo")


@administrador_requerido
def panel_admin(request):
    estados_activos = SolicitudColaborador.ESTADOS_ACTIVOS
    usuarios_por_rol = {
        fila["rol"]: fila["total"]
        for fila in Usuario.objects.values("rol").annotate(total=Count("id"))
    }
    contexto = {
        "propuestas_en_revision": Planificacion.objects.filter(
            estado=Planificacion.Estado.EN_REVISION
        ).count(),
        "solicitudes_activas": SolicitudColaborador.objects.filter(
            estado__in=estados_activos
        ).count(),
        "ideas_publicadas": Planificacion.objects.filter(
            estado=Planificacion.Estado.PUBLICADA
        ).count(),
        "usuarios_activos": Usuario.objects.filter(is_active=True).count(),
        "usuarios_por_rol": [
            (etiqueta, usuarios_por_rol.get(valor, 0)) for valor, etiqueta in Usuario.Rol.choices
        ],
        "ultimas_propuestas": Planificacion.objects.filter(estado=Planificacion.Estado.EN_REVISION)
        .select_related("colaborador", "nucleo__ambito")
        .order_by("fecha_envio")[:5],
        "ultimas_solicitudes": SolicitudColaborador.objects.filter(estado__in=estados_activos)
        .select_related("usuario")
        .order_by("fecha_solicitud")[:5],
        "ultimas_acciones": RegistroAccion.objects.select_related("usuario")[:8],
    }
    return render(request, "core/panel_admin.html", contexto)


@administrador_requerido
def auditoria(request):
    registros = RegistroAccion.objects.select_related("usuario")
    accion = request.GET.get("accion", "")
    if accion in RegistroAccion.Accion.values:
        registros = registros.filter(accion=accion)
    pagina = Paginator(registros, 20).get_page(request.GET.get("page"))
    return render(
        request,
        "core/auditoria.html",
        {"pagina": pagina, "acciones": RegistroAccion.Accion.choices, "accion_actual": accion},
    )
