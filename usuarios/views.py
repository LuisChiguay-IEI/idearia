"""Vistas de autenticación (RF-01) y gestión de usuarios del Administrador (RF-20)."""

from django.contrib import messages
from django.contrib.auth import login
from django.contrib.auth.views import LoginView, LogoutView
from django.core.paginator import Paginator
from django.db.models import Q
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_POST

from core.auditoria import registrar_accion
from core.models import RegistroAccion
from core.utils import redireccion_segura

from .forms import FiltroUsuariosForm, LoginForm, RegistroForm
from .models import Usuario
from .permisos import administrador_requerido


class IngresarView(LoginView):
    """Login de Django (protegido con CSRF y hash de contraseñas)."""

    template_name = "usuarios/login.html"
    authentication_form = LoginForm
    redirect_authenticated_user = True


class SalirView(LogoutView):
    """Cerrar sesión. En Django 5 solo acepta POST (evita cierres por enlaces maliciosos)."""


def registro(request):
    if request.user.is_authenticated:
        return redirect("core:inicio")
    if request.method == "POST":
        form = RegistroForm(request.POST)
        if form.is_valid():
            usuario = form.save()
            login(request, usuario)
            messages.success(request, "¡Registro realizado exitosamente! Bienvenido/a a Idearia.")
            return redirect("planificaciones:catalogo")
    else:
        form = RegistroForm()
    return render(request, "usuarios/registro.html", {"form": form})


@administrador_requerido
def admin_lista(request):
    form = FiltroUsuariosForm(request.GET)
    form.is_valid()
    datos = form.cleaned_data
    usuarios = Usuario.objects.all().order_by("-date_joined")
    if datos.get("q"):
        q = datos["q"]
        usuarios = usuarios.filter(
            Q(first_name__icontains=q)
            | Q(last_name__icontains=q)
            | Q(email__icontains=q)
            | Q(rut__icontains=q)
        )
    if datos.get("rol"):
        usuarios = usuarios.filter(rol=datos["rol"])
    if datos.get("estado") == "activo":
        usuarios = usuarios.filter(is_active=True)
    elif datos.get("estado") == "inactivo":
        usuarios = usuarios.filter(is_active=False)

    pagina = Paginator(usuarios, 15).get_page(request.GET.get("page"))
    return render(request, "usuarios/admin_lista.html", {"form": form, "pagina": pagina})


@administrador_requerido
@require_POST
def admin_cambiar_estado(request, pk):
    usuario = get_object_or_404(Usuario, pk=pk)
    if usuario == request.user:
        messages.error(request, "No puedes desactivar tu propia cuenta.")
    elif usuario.is_superuser and not request.user.is_superuser:
        messages.error(request, "Solo un superusuario puede modificar a otro superusuario.")
    else:
        usuario.is_active = not usuario.is_active
        usuario.save(update_fields=["is_active"])
        accion = (
            RegistroAccion.Accion.ACTIVAR_USUARIO
            if usuario.is_active
            else RegistroAccion.Accion.DESACTIVAR_USUARIO
        )
        registrar_accion(request, accion, usuario, usuario.email)
        estado = "reactivada" if usuario.is_active else "desactivada"
        messages.success(request, f"La cuenta de {usuario.get_full_name()} fue {estado}.")
    return redireccion_segura(request, request.POST.get("volver"), "usuarios:admin_lista")
