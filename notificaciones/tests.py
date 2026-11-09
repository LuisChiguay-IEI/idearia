from django.urls import reverse

from core.pruebas_utilidades import PruebaIdearia, crear_usuario
from notificaciones.models import Notificacion
from notificaciones.servicios import notificar


class NotificacionesTests(PruebaIdearia):
    def setUp(self):
        super().setUp()
        self.usuario = crear_usuario()
        self.otro = crear_usuario()
        self.mia = notificar(self.usuario, Notificacion.Tipo.SOLICITUD_APROBADA, "Mensaje para mí", "/ideas/")
        notificar(self.otro, Notificacion.Tipo.SOLICITUD_RECHAZADA, "Mensaje ajeno")
        self.ingresar(self.usuario)

    def test_cp023_cada_usuario_ve_solo_sus_notificaciones(self):
        """CP-023: la lista muestra solo las notificaciones del usuario y el contador de no leídas."""
        respuesta = self.client.get(reverse("notificaciones:lista"))
        self.assertContains(respuesta, "Mensaje para mí")
        self.assertNotContains(respuesta, "Mensaje ajeno")
        self.assertEqual(respuesta.context["notificaciones_sin_leer"], 1)

    def test_abrir_marca_como_leida(self):
        respuesta = self.client.get(reverse("notificaciones:abrir", args=[self.mia.pk]))
        self.assertRedirects(respuesta, "/ideas/", fetch_redirect_response=False)
        self.mia.refresh_from_db()
        self.assertTrue(self.mia.leida)

    def test_no_abre_notificacion_ajena(self):
        ajena = Notificacion.objects.get(usuario=self.otro)
        self.assertEqual(self.client.get(reverse("notificaciones:abrir", args=[ajena.pk])).status_code, 404)

    def test_enlace_externo_no_redirige(self):
        """Seguridad: una notificación con enlace externo no lleva fuera de Idearia."""
        externa = notificar(self.usuario, Notificacion.Tipo.SOLICITUD_APROBADA, "x", "https://malicioso.test/")
        respuesta = self.client.get(reverse("notificaciones:abrir", args=[externa.pk]))
        self.assertRedirects(respuesta, reverse("notificaciones:lista"))

    def test_marcar_todas_como_leidas(self):
        self.client.post(reverse("notificaciones:marcar_leidas"))
        self.assertFalse(Notificacion.objects.filter(usuario=self.usuario, leida=False).exists())
