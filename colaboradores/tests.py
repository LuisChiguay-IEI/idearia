"""Pruebas de la acreditación de Profesionales Colaboradores."""

from django.core.files.uploadedfile import SimpleUploadedFile
from django.db import IntegrityError, transaction
from django.urls import reverse

from colaboradores.models import SolicitudColaborador
from core.models import RegistroAccion
from core.pruebas_utilidades import PruebaIdearia, crear_usuario, docx_subido, pdf_subido
from notificaciones.models import Notificacion
from usuarios.models import Usuario

S = SolicitudColaborador.Estado


def datos_solicitud(**cambios):
    datos = {
        "titulo_profesional": "Educadora de Párvulos", "institucion": "Universidad de Prueba",
        "anio_titulacion": "2018", "documento_respaldo": pdf_subido("titulo.pdf"), "declaracion": "on",
    }
    datos.update(cambios)
    return datos


class SolicitudTests(PruebaIdearia):
    def setUp(self):
        super().setUp()
        self.educadora = crear_usuario()
        self.admin = crear_usuario(Usuario.Rol.ADMINISTRADOR)
        self.ingresar(self.educadora)
        self.url = reverse("colaboradores:nueva_solicitud")

    def test_cp014_solicitud_correcta(self):
        """CP-014: la solicitud queda Pendiente, con documento, y se notifica a los administradores."""
        respuesta = self.client.post(self.url, datos_solicitud())
        self.assertRedirects(respuesta, reverse("colaboradores:mi_solicitud"))
        solicitud = SolicitudColaborador.objects.get(usuario=self.educadora)
        self.assertEqual(solicitud.estado, S.PENDIENTE)
        self.assertTrue(solicitud.documento_respaldo.name.startswith("acreditaciones/"))
        self.assertTrue(Notificacion.objects.filter(usuario=self.admin, tipo=Notificacion.Tipo.NUEVA_SOLICITUD).exists())

    def test_cp033e_solicitud_sin_documento(self):
        """CP-033: sin documento ni declaración la solicitud no se registra."""
        datos = datos_solicitud()
        datos.pop("documento_respaldo")
        datos.pop("declaracion")
        respuesta = self.client.post(self.url, datos)
        self.assertIn("documento_respaldo", respuesta.context["form"].errors)
        self.assertIn("declaracion", respuesta.context["form"].errors)
        self.assertFalse(SolicitudColaborador.objects.exists())

    def test_cp030c_documento_de_acreditacion_formato_no_permitido(self):
        """CP-030: el certificado solo acepta PDF, JPG o PNG (RNF-04)."""
        respuesta = self.client.post(self.url, datos_solicitud(documento_respaldo=docx_subido("titulo.docx")))
        self.assertIn("Formato no permitido", str(respuesta.context["form"].errors["documento_respaldo"]))

    def test_anio_futuro_no_permitido(self):
        respuesta = self.client.post(self.url, datos_solicitud(anio_titulacion="2999"))
        self.assertIn("anio_titulacion", respuesta.context["form"].errors)

    def test_imagen_png_valida(self):
        png = SimpleUploadedFile("titulo.png", b"\x89PNG\r\n\x1a\n" + b"0" * 50, "image/png")
        self.client.post(self.url, datos_solicitud(documento_respaldo=png))
        self.assertTrue(SolicitudColaborador.objects.filter(usuario=self.educadora).exists())

    def test_cp050_segunda_solicitud_activa_bloqueada(self):
        """CP-050: con una solicitud en curso no se puede enviar otra (vista y base de datos)."""
        self.client.post(self.url, datos_solicitud())
        respuesta = self.client.post(self.url, datos_solicitud())
        self.assertRedirects(respuesta, reverse("colaboradores:mi_solicitud"))
        self.assertEqual(SolicitudColaborador.objects.filter(usuario=self.educadora).count(), 1)
        with self.assertRaises(IntegrityError), transaction.atomic():
            SolicitudColaborador.objects.create(
                usuario=self.educadora, titulo_profesional="X", institucion="Y", anio_titulacion=2018,
                documento_respaldo="acreditaciones/x.pdf", nombre_archivo="x.pdf",
            )

    def test_colaborador_no_puede_volver_a_solicitar(self):
        self.educadora.rol = Usuario.Rol.COLABORADOR
        self.educadora.save()
        self.assertEqual(self.client.get(self.url).status_code, 403)


class RevisionSolicitudTests(PruebaIdearia):
    def setUp(self):
        super().setUp()
        self.educadora = crear_usuario()
        self.admin = crear_usuario(Usuario.Rol.ADMINISTRADOR)
        self.solicitud = SolicitudColaborador(
            usuario=self.educadora, titulo_profesional="Educadora de Párvulos",
            institucion="Universidad de Prueba", anio_titulacion=2018, nombre_archivo="titulo.pdf",
        )
        self.solicitud.documento_respaldo.save("titulo.pdf", pdf_subido(), save=False)
        self.solicitud.save()
        self.ingresar(self.admin)
        self.url = reverse("colaboradores:admin_resolver", args=[self.solicitud.pk])

    def test_cp015_aprobar_solicitud_habilita_colaborador(self):
        """CP-015: al aprobar, el usuario pasa a rol Colaborador, se notifica y se audita."""
        self.client.post(self.url, {"accion": "revisar"})
        self.solicitud.refresh_from_db()
        self.assertEqual(self.solicitud.estado, S.EN_REVISION)
        self.client.post(self.url, {"accion": "aprobar"})
        self.solicitud.refresh_from_db()
        self.educadora.refresh_from_db()
        self.assertEqual(self.solicitud.estado, S.APROBADA)
        self.assertEqual(self.educadora.rol, Usuario.Rol.COLABORADOR)
        self.assertEqual(self.solicitud.revisado_por, self.admin)
        self.assertTrue(Notificacion.objects.filter(usuario=self.educadora, tipo=Notificacion.Tipo.SOLICITUD_APROBADA).exists())
        self.assertTrue(RegistroAccion.objects.filter(accion=RegistroAccion.Accion.APROBAR_SOLICITUD, usuario=self.admin).exists())
        # Ahora puede crear propuestas
        self.client.force_login(self.educadora)
        self.assertEqual(self.client.get(reverse("planificaciones:crear_propuesta")).status_code, 200)

    def test_rechazo_exige_observacion(self):
        """RF-19: rechazar sin motivo no cambia el estado; con motivo queda Rechazada."""
        self.client.post(self.url, {"accion": "rechazar"})
        self.solicitud.refresh_from_db()
        self.assertEqual(self.solicitud.estado, S.PENDIENTE)
        self.client.post(self.url, {"accion": "rechazar", "observacion": "Documento ilegible."})
        self.solicitud.refresh_from_db()
        self.educadora.refresh_from_db()
        self.assertEqual(self.solicitud.estado, S.RECHAZADA)
        self.assertEqual(self.educadora.rol, Usuario.Rol.EDUCADOR)
        self.assertTrue(Notificacion.objects.filter(usuario=self.educadora, tipo=Notificacion.Tipo.SOLICITUD_RECHAZADA).exists())

    def test_solicitud_ya_procesada_no_se_resuelve_dos_veces(self):
        """ADM-02 E3: una solicitud procesada no admite una nueva decisión."""
        self.client.post(self.url, {"accion": "rechazar", "observacion": "Documento ilegible."})
        self.client.post(self.url, {"accion": "aprobar"})
        self.solicitud.refresh_from_db()
        self.educadora.refresh_from_db()
        self.assertEqual(self.solicitud.estado, S.RECHAZADA)
        self.assertEqual(self.educadora.rol, Usuario.Rol.EDUCADOR)

    def test_cp027c_educador_no_accede_a_revision_de_solicitudes(self):
        """CP-027: la revisión de solicitudes es exclusiva del Administrador."""
        self.client.force_login(crear_usuario())
        self.assertEqual(self.client.get(reverse("colaboradores:admin_lista")).status_code, 403)
        self.assertEqual(self.client.post(self.url, {"accion": "aprobar"}).status_code, 403)

    def test_cp041_documento_solo_para_dueno_y_administrador(self):
        """CP-041: el certificado lo ven su dueño y el administrador; otro usuario recibe 404 (RNF-03)."""
        url = reverse("colaboradores:documento", args=[self.solicitud.pk])
        self.assertEqual(self.client.get(url).status_code, 200)
        self.client.force_login(self.educadora)
        self.assertEqual(self.client.get(url).status_code, 200)
        self.client.force_login(crear_usuario())
        self.assertEqual(self.client.get(url).status_code, 404)
