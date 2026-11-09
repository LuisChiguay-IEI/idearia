"""
Cabeceras HTTP de seguridad adicionales.

Content-Security-Policy (CSP) indica al navegador desde dónde puede cargar
scripts, estilos e imágenes. Con "script-src 'self'" un script inyectado
en un comentario no se ejecuta (protección contra XSS).

En desarrollo (DEBUG=True) se usa el modo "Report-Only": el navegador solo
avisa en la consola, para no romper la página de errores de Django.
"""

from django.conf import settings

POLITICA_CSP = "; ".join(
    [
        "default-src 'self'",
        "script-src 'self'",
        "style-src 'self' https://fonts.googleapis.com",
        "font-src 'self' https://fonts.gstatic.com",
        "img-src 'self' data: blob:",
        "worker-src 'self' blob:",
        "connect-src 'self'",
        "object-src 'none'",
        "frame-ancestors 'none'",
        "base-uri 'self'",
        "form-action 'self'",
    ]
)


class CabecerasSeguridadMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        response = self.get_response(request)
        # El admin técnico de Django usa estilos en línea: se excluye de la CSP.
        if not request.path.startswith("/" + settings.ADMIN_URL):
            cabecera = (
                "Content-Security-Policy-Report-Only"
                if settings.DEBUG
                else "Content-Security-Policy"
            )
            response.headers.setdefault(cabecera, POLITICA_CSP)
        response.headers.setdefault(
            "Permissions-Policy", "camera=(), microphone=(), geolocation=()"
        )
        return response
