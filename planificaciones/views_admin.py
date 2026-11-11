"""
Revisión de propuestas por el Administrador.

Cada decisión:

- cambia el estado de la propuesta;
- notifica al Profesional Colaborador;
- queda registrada en la auditoría.

Flujo principal actualizado:

EN_REVISION
    -> aprobar
    -> PUBLICADA

Por lo tanto, aprobar una propuesta nueva también la publica
directamente en el catálogo de Idearia.
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


# =========================================================
# EFECTOS DE CADA ACCIÓN ADMINISTRATIVA
# =========================================================
#
# acción:
# (
#     tipo de notificación,
#     acción registrada en auditoría,
#     mensaje para el colaborador,
#     mensaje de éxito para el administrador,
# )
# =========================================================

EFECTOS = {

    # -----------------------------------------------------
    # APROBAR = APROBAR + PUBLICAR
    # -----------------------------------------------------

    "aprobar": (
        Notificacion.Tipo.PROPUESTA_PUBLICADA,
        RegistroAccion.Accion.APROBAR_PROPUESTA,
        (
            "¡Tu propuesta «{titulo}» fue aprobada y publicada "
            "en el catálogo de Idearia!"
        ),
        "Propuesta aprobada y publicada en el catálogo.",
    ),

    # -----------------------------------------------------
    # RECHAZAR
    # -----------------------------------------------------

    "rechazar": (
        Notificacion.Tipo.PROPUESTA_RECHAZADA,
        RegistroAccion.Accion.RECHAZAR_PROPUESTA,
        (
            "Tu propuesta «{titulo}» fue rechazada. "
            "Motivo: {obs}"
        ),
        "Propuesta rechazada.",
    ),

    # -----------------------------------------------------
    # SOLICITAR CORRECCIÓN
    # -----------------------------------------------------

    "corregir": (
        Notificacion.Tipo.CORRECCION_SOLICITADA,
        RegistroAccion.Accion.SOLICITAR_CORRECCION,
        (
            "Se solicitaron correcciones en «{titulo}»: "
            "{obs}"
        ),
        "Se solicitaron correcciones al colaborador.",
    ),

    # -----------------------------------------------------
    # PUBLICAR
    # -----------------------------------------------------
    #
    # Esta acción se mantiene únicamente por compatibilidad
    # con propuestas antiguas que hayan quedado en APROBADA.
    # -----------------------------------------------------

    "publicar": (
        Notificacion.Tipo.PROPUESTA_PUBLICADA,
        RegistroAccion.Accion.PUBLICAR_PROPUESTA,
        (
            "¡Tu propuesta «{titulo}» ya está publicada "
            "en Idearia!"
        ),
        "Propuesta publicada en el catálogo.",
    ),

    # -----------------------------------------------------
    # RETIRAR
    # -----------------------------------------------------

    "retirar": (
        Notificacion.Tipo.PROPUESTA_RETIRADA,
        RegistroAccion.Accion.RETIRAR_PROPUESTA,
        (
            "Tu propuesta «{titulo}» fue retirada del catálogo. "
            "Motivo: {obs}"
        ),
        "Propuesta retirada del catálogo.",
    ),

    # -----------------------------------------------------
    # VOLVER A PUBLICAR
    # -----------------------------------------------------

    "republicar": (
        Notificacion.Tipo.PROPUESTA_PUBLICADA,
        RegistroAccion.Accion.REPUBLICAR_PROPUESTA,
        (
            "Tu propuesta «{titulo}» volvió a publicarse "
            "en el catálogo de Idearia."
        ),
        "Propuesta publicada nuevamente.",
    ),
}


# =========================================================
# ESTADOS VISIBLES EN ADMINISTRACIÓN
# =========================================================

ESTADOS_REVISION = [
    estado
    for estado in Planificacion.Estado.choices
    if estado[0] != Planificacion.Estado.BORRADOR
]


# =========================================================
# LISTADO Y REVISIÓN
# =========================================================

@administrador_requerido
def revision(request):
    """
    Muestra:

    - listado de propuestas a la izquierda;
    - detalle de la seleccionada a la derecha;
    - filtros por estado;
    - búsqueda por título o colaborador.
    """

    base = (
        Planificacion.objects
        .exclude(
            estado=Planificacion.Estado.BORRADOR
        )
        .select_related(
            "colaborador",
            "nucleo__ambito",
            "revisado_por",
        )
    )

    conteos = {
        fila["estado"]: fila["total"]
        for fila in (
            base.values("estado")
            .annotate(total=Count("id"))
        )
    }

    estado = request.GET.get(
        "estado",
        Planificacion.Estado.EN_REVISION,
    )

    if estado == "TODAS":
        lista = base
    else:
        lista = base.filter(
            estado=estado
        )

    q = request.GET.get(
        "q",
        "",
    ).strip()

    if q:

        lista = lista.filter(

            Q(
                titulo__icontains=q
            )

            | Q(
                colaborador__first_name__icontains=q
            )

            | Q(
                colaborador__last_name__icontains=q
            )

            | Q(
                colaborador__email__icontains=q
            )

        )

    lista = lista.order_by(
        "-fecha_envio",
        "-pk",
    )

    pagina = Paginator(
        lista,
        8,
    ).get_page(
        request.GET.get("page")
    )


    # -----------------------------------------------------
    # PROPUESTA SELECCIONADA
    # -----------------------------------------------------

    seleccion = None

    identificador = request.GET.get(
        "id",
        "",
    )

    if identificador.isdigit():

        seleccion = base.filter(
            pk=identificador
        ).first()

    if (
        seleccion is None
        and pagina.object_list
    ):

        seleccion = (
            pagina.object_list[0]
        )


    # -----------------------------------------------------
    # CONTEXTO GENERAL
    # -----------------------------------------------------

    contexto = {

        "pagina":
            pagina,

        "estado_actual":
            estado,

        "q":
            q,

        "pestanas": [
            (
                valor,
                etiqueta,
                conteos.get(valor, 0),
            )
            for valor, etiqueta
            in ESTADOS_REVISION
        ],

        "total":
            sum(conteos.values()),

        "seleccion":
            seleccion,

        "form":
            AccionRevisionForm(),

    }


    # -----------------------------------------------------
    # DATOS DE LA PROPUESTA SELECCIONADA
    # -----------------------------------------------------

    if seleccion:

        contexto[
            "faltantes"
        ] = seleccion.campos_faltantes()

        contexto[
            "acreditacion"
        ] = (
            seleccion
            .colaborador
            .solicitudes_colaborador
            .filter(
                estado=SolicitudColaborador.Estado.APROBADA
            )
            .first()
        )

        contexto[
            "acciones_disponibles"
        ] = [

            accion

            for accion, (
                origenes,
                destino,
            )

            in Planificacion.ACCIONES_REVISION.items()

            if seleccion.estado in origenes

        ]

    return render(
        request,
        "planificaciones/admin/revision.html",
        contexto,
    )


# =========================================================
# ENLACE DIRECTO A UNA PROPUESTA
# =========================================================

@administrador_requerido
def detalle_revision(
    request,
    pk,
):
    """
    Enlace directo utilizado, por ejemplo,
    desde una notificación administrativa.
    """

    propuesta = get_object_or_404(

        Planificacion.objects.exclude(
            estado=Planificacion.Estado.BORRADOR
        ),

        pk=pk,

    )

    return redirect(
        (
            f"{reverse('planificaciones:admin_revision')}"
            f"?estado={propuesta.estado}"
            f"&id={propuesta.pk}"
        )
    )


# =========================================================
# APLICAR ACCIÓN DE REVISIÓN
# =========================================================

@administrador_requerido
@require_POST
def accion_revision(
    request,
    pk,
):
    """
    Aplica una decisión del Administrador.

    En el flujo actual:

    aprobar
        -> publica inmediatamente la propuesta.

    corregir
        -> devuelve la propuesta al colaborador.

    rechazar
        -> marca la propuesta como rechazada.

    retirar
        -> elimina una publicación del catálogo.

    republicar
        -> vuelve a mostrar una propuesta retirada.

    publicar
        -> se conserva para propuestas antiguas en APROBADA.
    """

    propuesta = get_object_or_404(

        Planificacion.objects.exclude(
            estado=Planificacion.Estado.BORRADOR
        ),

        pk=pk,

    )

    form = AccionRevisionForm(
        request.POST
    )


    # -----------------------------------------------------
    # VALIDAR FORMULARIO
    # -----------------------------------------------------

    if not form.is_valid():

        for errores in form.errors.values():

            for error in errores:

                messages.error(
                    request,
                    error,
                )

        return redirect(
            "planificaciones:admin_detalle",
            pk=propuesta.pk,
        )


    accion = form.cleaned_data[
        "accion"
    ]

    observacion = (
        form.cleaned_data[
            "observacion"
        ].strip()
    )


    # -----------------------------------------------------
    # APLICAR CAMBIO DE ESTADO
    # -----------------------------------------------------

    try:

        propuesta.aplicar_accion_revision(
            accion,
            request.user,
            observacion,
        )

    except TransicionInvalida as error:

        messages.error(
            request,
            str(error),
        )

        return redirect(
            "planificaciones:admin_detalle",
            pk=propuesta.pk,
        )


    # -----------------------------------------------------
    # EFECTOS POSTERIORES
    # -----------------------------------------------------

    (
        tipo_notificacion,
        accion_auditoria,
        plantilla,
        mensaje_exito,
    ) = EFECTOS[
        accion
    ]


    # -----------------------------------------------------
    # ENLACE DE LA NOTIFICACIÓN
    # -----------------------------------------------------

    if accion == "corregir":

        enlace = reverse(
            "planificaciones:editar_propuesta",
            args=[
                propuesta.pk
            ],
        )

    elif propuesta.estado == Planificacion.Estado.PUBLICADA:

        enlace = reverse(
            "planificaciones:detalle",
            args=[
                propuesta.pk
            ],
        )

    else:

        enlace = reverse(
            "planificaciones:mis_propuestas"
        )


    # -----------------------------------------------------
    # NOTIFICAR AL COLABORADOR
    # -----------------------------------------------------

    notificar(

        propuesta.colaborador,

        tipo_notificacion,

        plantilla.format(
            titulo=propuesta.titulo,
            obs=observacion,
        ),

        enlace,

    )


    # -----------------------------------------------------
    # AUDITORÍA
    # -----------------------------------------------------

    if accion == "aprobar":

        descripcion_auditoria = (
            f"{propuesta.titulo} | "
            "Propuesta aprobada y publicada directamente"
        )

    elif observacion:

        descripcion_auditoria = (
            f"{propuesta.titulo} | "
            f"{observacion}"
        )

    else:

        descripcion_auditoria = (
            propuesta.titulo
        )


    registrar_accion(
        request,
        accion_auditoria,
        propuesta,
        descripcion_auditoria,
    )


    # -----------------------------------------------------
    # MENSAJE PARA EL ADMINISTRADOR
    # -----------------------------------------------------

    messages.success(
        request,
        mensaje_exito,
    )


    return redirect(
        "planificaciones:admin_detalle",
        pk=propuesta.pk,
    )