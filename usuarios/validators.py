"""Validación del RUT chileno (algoritmo módulo 11)."""

import re

from django.core.exceptions import ValidationError

PATRON_RUT = re.compile(r"^\d{7,8}-[\dK]$")


def normalizar_rut(valor):
    """Convierte '12.345.678-5' o '123456785' en '12345678-5'."""
    limpio = re.sub(r"[^0-9kK]", "", str(valor or "")).upper()
    if len(limpio) < 2:
        return limpio
    return f"{limpio[:-1]}-{limpio[-1]}"


def calcular_digito_verificador(cuerpo):
    """Calcula el dígito verificador de un RUT (sin puntos ni guion)."""
    suma = 0
    multiplicador = 2
    for digito in reversed(str(cuerpo)):
        suma += int(digito) * multiplicador
        multiplicador = 2 if multiplicador == 7 else multiplicador + 1
    resto = 11 - (suma % 11)
    if resto == 11:
        return "0"
    if resto == 10:
        return "K"
    return str(resto)


def validar_rut(valor):
    """Lanza ValidationError si el RUT no tiene formato válido o su dígito no coincide."""
    rut = normalizar_rut(valor)
    if not PATRON_RUT.match(rut):
        raise ValidationError("El RUT debe tener el formato 12345678-9.", code="rut_formato")
    cuerpo, digito = rut.split("-")
    if calcular_digito_verificador(cuerpo) != digito:
        raise ValidationError("El RUT ingresado no es válido.", code="rut_invalido")
