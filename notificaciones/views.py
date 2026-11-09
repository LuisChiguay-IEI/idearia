from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_POST

from core.utils import redireccion_segura

from .models import Notificacion


@login_required
def lista(request):
    notificaciones = request.user.notificaciones.all()
    pagina = Paginator(notificaciones, 15).get_page(request.GET.get("page"))
    return render(request, "notificaciones/lista.html", {"pagina": pagina})


@login_required
def abrir(request, pk):
    """Marca la notificación como leída y lleva al enlace (solo rutas internas)."""
    notificacion = get_object_or_404(Notificacion, pk=pk, usuario=request.user)
    if not notificacion.leida:
        notificacion.leida = True
        notificacion.save(update_fields=["leida"])
    return redireccion_segura(request, notificacion.enlace, "notificaciones:lista")


@login_required
@require_POST
def marcar_leidas(request):
    total = request.user.notificaciones.filter(leida=False).update(leida=True)
    messages.success(request, f"{total} notificación(es) marcada(s) como leída(s).")
    return redirect("notificaciones:lista")
