"""
Conversión de planificaciones Word (.docx) a HTML para verlas dentro de Idearia.

Se usa la librería "mammoth", que lee el documento como datos (nunca ejecuta
macros ni código). Luego se limpia el HTML para que solo queden enlaces
web normales e imágenes incrustadas.
"""

import re

import mammoth

_SCRIPTS = re.compile(r"<script.*?>.*?</script>", re.IGNORECASE | re.DOTALL)
_ENLACES_NO_WEB = re.compile(r'href="(?!https?://|mailto:|#)[^"]*"', re.IGNORECASE)
_IMAGENES_EXTERNAS = re.compile(r'src="(?!data:image/(?:png|jpe?g|gif);base64,)[^"]*"', re.IGNORECASE)
_EVENTOS = re.compile(r"\son\w+=\"[^\"]*\"", re.IGNORECASE)


def sanear_html(html):
    html = _SCRIPTS.sub("", html)
    html = _EVENTOS.sub("", html)
    html = _ENLACES_NO_WEB.sub('href="#"', html)
    html = _IMAGENES_EXTERNAS.sub('src=""', html)
    return html


def docx_a_html(archivo):
    """Recibe el FileField de la planificación y devuelve HTML seguro."""
    with archivo.open("rb") as documento:
        resultado = mammoth.convert_to_html(documento)
    return sanear_html(resultado.value)
