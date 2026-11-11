"""
Vistas del Profesional Colaborador/a.

Solo los usuarios con rol COLABORADOR pueden crear propuestas.

Cada colaborador puede ver y editar únicamente sus propias propuestas.
Si intenta acceder a una propuesta de otro usuario, recibe 404.

Además de la planificación Word/PDF, una propuesta puede incluir
opcionalmente una imagen de portada.

La imagen de portada:

- no es obligatoria;
- puede reemplazarse;
- puede eliminarse;
- si no existe, Idearia utiliza los íconos actuales del ámbito;
- será revisada por el Administrador junto con la planificación.
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


# =========================================================
# PANEL DEL COLABORADOR
# =========================================================

@colaborador_requerido
def panel(request):
    propuestas = request.user.planificaciones.select_related(
        "nucleo__ambito"
    )

    conteos = {
        fila["estado"]: fila["total"]
        for fila in propuestas.values("estado").annotate(
            total=Count("id")
        )
    }

    return render(
        request,
        "planificaciones/colaborador/panel.html",
        {
            "conteos": [
                (
                    valor,
                    etiqueta,
                    conteos.get(valor, 0),
                )
                for valor, etiqueta in Planificacion.Estado.choices
            ],

            "total": sum(
                conteos.values()
            ),

            "recientes": propuestas.order_by(
                "-fecha_actualizacion"
            )[:5],

            "por_corregir": propuestas.filter(
                estado=Planificacion.Estado.REQUIERE_CORRECCION
            ),
        },
    )


# =========================================================
# LISTADO DE PROPUESTAS
# =========================================================

@colaborador_requerido
def mis_propuestas(request):
    propuestas = (
        request.user
        .planificaciones
        .select_related("nucleo__ambito")
        .order_by("-fecha_actualizacion")
    )

    estado = request.GET.get(
        "estado",
        "",
    )

    conteos = {
        fila["estado"]: fila["total"]
        for fila in propuestas.values("estado").annotate(
            total=Count("id")
        )
    }

    if estado in Planificacion.Estado.values:
        propuestas = propuestas.filter(
            estado=estado
        )

    return render(
        request,
        "planificaciones/colaborador/mis_propuestas.html",
        {
            "propuestas": propuestas,

            "estado_actual": estado,

            "pestanas": [
                (
                    valor,
                    etiqueta,
                    conteos.get(valor, 0),
                )
                for valor, etiqueta
                in Planificacion.Estado.choices
                if conteos.get(valor)
            ],

            "total": sum(
                conteos.values()
            ),
        },
    )


# =========================================================
# CREAR PROPUESTA
# =========================================================

@colaborador_requerido
def crear_propuesta(request):
    propuesta = Planificacion(
        colaborador=request.user
    )

    return _guardar_propuesta(
        request,
        propuesta,
    )


# =========================================================
# EDITAR PROPUESTA
# =========================================================

@colaborador_requerido
def editar_propuesta(request, pk):
    propuesta = get_object_or_404(
        Planificacion,
        pk=pk,
        colaborador=request.user,
    )

    if not propuesta.es_editable:
        messages.warning(
            request,
            (
                "La propuesta está en estado "
                f"«{propuesta.get_estado_display()}» "
                "y no se puede editar."
            ),
        )

        return redirect(
            "planificaciones:mis_propuestas"
        )

    return _guardar_propuesta(
        request,
        propuesta,
    )


# =========================================================
# CREAR / EDITAR
# =========================================================

def _guardar_propuesta(request, propuesta):
    """
    Lógica común para crear y editar una propuesta.

    Permite administrar:

    - planificación Word/PDF;
    - imagen de portada opcional;
    - reemplazo de archivos;
    - eliminación voluntaria de la imagen;
    - envío a revisión.

    El botón presionado determina si la propuesta se guarda
    como borrador o se envía al Administrador.
    """

    enviar = (
        request.method == "POST"
        and request.POST.get("accion") == "enviar"
    )

    # -----------------------------------------------------
    # GUARDAMOS LOS NOMBRES DE LOS ARCHIVOS ANTERIORES
    # -----------------------------------------------------
    #
    # Esto permite eliminar correctamente el archivo físico
    # cuando el colaborador lo reemplaza o lo quita.
    # -----------------------------------------------------

    archivo_anterior = (
        propuesta.archivo.name
        if propuesta.archivo
        else ""
    )

    imagen_anterior = (
        propuesta.imagen_portada.name
        if propuesta.imagen_portada
        else ""
    )

    # =====================================================
    # POST
    # =====================================================

    if request.method == "POST":

        form = PropuestaForm(
            request.POST,
            request.FILES,
            instance=propuesta,
            enviar=enviar,
        )

        if form.is_valid():

            propuesta = form.save(
                commit=False
            )

            # -------------------------------------------------
            # PLANIFICACIÓN WORD / PDF
            # -------------------------------------------------

            nuevo_archivo = request.FILES.get(
                "archivo"
            )

            if nuevo_archivo:

                propuesta.nombre_archivo = (
                    get_valid_filename(
                        Path(
                            nuevo_archivo.name
                        ).name
                    )[:200]
                )

                propuesta.tipo_archivo = (
                    obtener_extension(
                        nuevo_archivo.name
                    )
                )

                propuesta.tamano_archivo = (
                    nuevo_archivo.size
                )

            # -------------------------------------------------
            # IMAGEN DE PORTADA
            # -------------------------------------------------

            nueva_imagen = request.FILES.get(
                "imagen_portada"
            )

            quitar_imagen = (
                form.cleaned_data.get(
                    "quitar_imagen_portada",
                    False,
                )
            )

            # -------------------------------------------------
            # SI EL COLABORADOR QUIERE QUITAR LA IMAGEN
            # -------------------------------------------------

            if quitar_imagen:

                propuesta.imagen_portada = ""

                propuesta.nombre_imagen = ""

                propuesta.tipo_imagen = ""

                propuesta.tamano_imagen = None

            # -------------------------------------------------
            # SI SUBE UNA NUEVA IMAGEN
            # -------------------------------------------------

            elif nueva_imagen:

                propuesta.nombre_imagen = (
                    get_valid_filename(
                        Path(
                            nueva_imagen.name
                        ).name
                    )[:200]
                )

                propuesta.tipo_imagen = (
                    obtener_extension(
                        nueva_imagen.name
                    )
                )

                propuesta.tamano_imagen = (
                    nueva_imagen.size
                )

            # -------------------------------------------------
            # GUARDAR PROPUESTA
            # -------------------------------------------------

            propuesta.save()

            form.save_m2m()

            # -------------------------------------------------
            # ELIMINAR PLANIFICACIÓN ANTERIOR SI FUE REEMPLAZADA
            # -------------------------------------------------

            if (
                nuevo_archivo
                and archivo_anterior
                and archivo_anterior
                != propuesta.archivo.name
            ):
                propuesta.archivo.storage.delete(
                    archivo_anterior
                )

            # -------------------------------------------------
            # ELIMINAR IMAGEN ANTERIOR
            # -------------------------------------------------
            #
            # Se elimina si:
            #
            # - el usuario decidió quitarla;
            # - fue reemplazada por una nueva.
            # -------------------------------------------------

            if imagen_anterior:

                imagen_actual = (
                    propuesta.imagen_portada.name
                    if propuesta.imagen_portada
                    else ""
                )

                if (
                    quitar_imagen
                    or (
                        nueva_imagen
                        and imagen_anterior
                        != imagen_actual
                    )
                ):
                    propuesta.imagen_portada.storage.delete(
                        imagen_anterior
                    )

            # =================================================
            # ENVIAR A REVISIÓN
            # =================================================

            if enviar:

                try:
                    propuesta.enviar_a_revision()

                except TransicionInvalida as error:

                    messages.warning(
                        request,
                        (
                            "Se guardó como borrador, "
                            "pero no se pudo enviar: "
                            f"{error}"
                        ),
                    )

                    return redirect(
                        "planificaciones:editar_propuesta",
                        pk=propuesta.pk,
                    )

                # ---------------------------------------------
                # NOTIFICAR A LOS ADMINISTRADORES
                # ---------------------------------------------

                notificar_administradores(
                    Notificacion.Tipo.NUEVA_PROPUESTA,
                    (
                        f"{request.user.get_full_name()} "
                        "envió a revisión "
                        f"«{propuesta.titulo}»."
                    ),
                    reverse(
                        "planificaciones:admin_detalle",
                        args=[
                            propuesta.pk
                        ],
                    ),
                )

                messages.success(
                    request,
                    (
                        "Tu propuesta fue enviada a revisión. "
                        "La planificación y la imagen de portada, "
                        "si agregaste una, serán revisadas antes "
                        "de su publicación."
                    ),
                )

                return redirect(
                    "planificaciones:mis_propuestas"
                )

            # =================================================
            # GUARDAR BORRADOR
            # =================================================

            messages.success(
                request,
                "Borrador guardado correctamente.",
            )

            return redirect(
                "planificaciones:editar_propuesta",
                pk=propuesta.pk,
            )

    # =====================================================
    # GET
    # =====================================================

    else:

        form = PropuestaForm(
            instance=propuesta
        )

    # =====================================================
    # MOSTRAR FORMULARIO
    # =====================================================

    return render(
        request,
        "planificaciones/colaborador/propuesta_form.html",
        {
            "form": form,

            "propuesta": propuesta,

            "recientes": (
                request.user
                .planificaciones
                .order_by(
                    "-fecha_actualizacion"
                )[:5]
            ),
        },
    )


# =========================================================
# ELIMINAR BORRADOR
# =========================================================

@colaborador_requerido
@require_POST
def eliminar_propuesta(request, pk):

    propuesta = get_object_or_404(
        Planificacion,
        pk=pk,
        colaborador=request.user,
    )

    if (
        propuesta.estado
        != Planificacion.Estado.BORRADOR
    ):

        messages.error(
            request,
            (
                "Solo se pueden eliminar propuestas "
                "en estado Borrador."
            ),
        )

    else:

        # -------------------------------------------------
        # ELIMINAR PLANIFICACIÓN ADJUNTA
        # -------------------------------------------------

        if propuesta.archivo:
            propuesta.archivo.delete(
                save=False
            )

        # -------------------------------------------------
        # ELIMINAR IMAGEN DE PORTADA
        # -------------------------------------------------

        if propuesta.imagen_portada:
            propuesta.imagen_portada.delete(
                save=False
            )

        # -------------------------------------------------
        # ELIMINAR REGISTRO
        # -------------------------------------------------

        propuesta.delete()

        messages.success(
            request,
            "Borrador eliminado.",
        )

    return redirect(
        "planificaciones:mis_propuestas"
    )