"""Utilidades compartidas."""

from django.shortcuts import redirect
from django.utils.http import url_has_allowed_host_and_scheme


def redireccion_segura(request, url, por_defecto):
    """
    Redirige solo a direcciones internas de Idearia.
    Evita la vulnerabilidad "open redirect" (que un enlace manipulado
    envíe al usuario a un sitio externo malicioso).
    """
    if url and url_has_allowed_host_and_scheme(
        url, allowed_hosts={request.get_host()}, require_https=request.is_secure()
    ):
        return redirect(url)
    return redirect(por_defecto)
