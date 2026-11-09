"""Pruebas generales: redirección por rol, seguridad HTTP, validadores y datos de demostración."""

import os
from io import StringIO
from unittest import mock

from django.core.exceptions import ValidationError
from django.core.files.uploadedfile import SimpleUploadedFile
from django.core.management import call_command
from django.db import connection
from django.urls import reverse

from core.pruebas_utilidades import PruebaIdearia, crear_usuario, docx_subido, pdf_subido
from core.validators import EXTENSIONES_PLANIFICACION, validar_archivo
from planificaciones.models import Planificacion
from usuarios.models import Usuario


class InicioYPanelTests(PruebaIdearia):
    def test_inicio_redirige_segun_rol(self):
        """RF-02: cada perfil llega a su pantalla principal."""
        self.assertRedirects(self.client.get("/"), reverse("usuarios:login"))
        self.ingresar(crear_usuario())
        self.assertRedirects(self.client.get("/"), reverse("planificaciones:catalogo"))
        self.ingresar(crear_usuario(Usuario.Rol.ADMINISTRADOR))
        self.assertRedirects(self.client.get("/"), reverse("core:panel_admin"))

    def test_cp027d_panel_admin_solo_para_administrador(self):
        """CP-027: Educador/a y Colaborador/a reciben 403 en el panel de administración."""
        for rol in (Usuario.Rol.EDUCADOR, Usuario.Rol.COLABORADOR):
            self.ingresar(crear_usuario(rol))
            self.assertEqual(self.client.get(reverse("core:panel_admin")).status_code, 403)
            self.assertEqual(self.client.get(reverse("core:auditoria")).status_code, 403)
        self.ingresar(crear_usuario(Usuario.Rol.ADMINISTRADOR))
        self.assertEqual(self.client.get(reverse("core:panel_admin")).status_code, 200)

    def test_menu_muestra_solo_opciones_del_rol(self):
        """RF-02: el Educador/a no ve opciones de administración en el menú."""
        self.ingresar(crear_usuario())
        html = self.client.get(reverse("planificaciones:catalogo")).content.decode()
        self.assertNotIn(reverse("core:panel_admin"), html)
        self.assertIn("Ser colaborador/a", html)


class CabecerasYErroresTests(PruebaIdearia):
    def test_cp040_cabeceras_de_seguridad(self):
        """CP-040: CSP, anti-clickjacking, nosniff y política de referer en las respuestas."""
        respuesta = self.client.get(reverse("usuarios:login"))
        self.assertIn("default-src 'self'", respuesta["Content-Security-Policy"])
        self.assertIn("frame-ancestors 'none'", respuesta["Content-Security-Policy"])
        self.assertEqual(respuesta["X-Frame-Options"], "DENY")
        self.assertEqual(respuesta["X-Content-Type-Options"], "nosniff")
        self.assertEqual(respuesta["Referrer-Policy"], "same-origin")

    def test_cp040b_pagina_404_sin_informacion_tecnica(self):
        """CP-040: los errores muestran una página propia, sin trazas ni rutas internas."""
        respuesta = self.client.get("/ruta-que-no-existe/")
        self.assertEqual(respuesta.status_code, 404)
        self.assertContains(respuesta, "No encontramos lo que buscas", status_code=404)
        self.assertNotContains(respuesta, "Traceback", status_code=404)
        self.assertNotContains(respuesta, "urlpatterns", status_code=404)

    def test_cp040c_pagina_403_propia(self):
        self.ingresar(crear_usuario())
        respuesta = self.client.get(reverse("core:panel_admin"))
        self.assertContains(respuesta, "No tienes permisos para acceder", status_code=403)


class ValidadorArchivosTests(PruebaIdearia):
    def test_pdf_y_docx_validos(self):
        self.assertEqual(validar_archivo(pdf_subido(), EXTENSIONES_PLANIFICACION), "pdf")
        self.assertEqual(validar_archivo(docx_subido(), EXTENSIONES_PLANIFICACION), "docx")

    def test_archivo_vacio(self):
        with self.assertRaises(ValidationError):
            validar_archivo(SimpleUploadedFile("plan.pdf", b"", "application/pdf"), EXTENSIONES_PLANIFICACION)

    def test_mime_que_no_coincide(self):
        with self.assertRaises(ValidationError):
            validar_archivo(SimpleUploadedFile("plan.pdf", b"%PDF-1.4 x", "text/html"), EXTENSIONES_PLANIFICACION)

    def test_zip_que_no_es_word(self):
        import io
        import zipfile

        memoria = io.BytesIO()
        with zipfile.ZipFile(memoria, "w") as z:
            z.writestr("otro.txt", "hola")
        falso = SimpleUploadedFile("plan.docx", memoria.getvalue(), "application/vnd.openxmlformats-officedocument.wordprocessingml.document")
        with self.assertRaises(ValidationError):
            validar_archivo(falso, EXTENSIONES_PLANIFICACION)

    def test_docx_con_macros_rechazado(self):
        import io
        import zipfile

        memoria = io.BytesIO()
        with zipfile.ZipFile(memoria, "w") as z:
            z.writestr("word/document.xml", "<w:document/>")
            z.writestr("word/vbaProject.bin", "macro")
        con_macros = SimpleUploadedFile("plan.docx", memoria.getvalue(), "application/vnd.openxmlformats-officedocument.wordprocessingml.document")
        with self.assertRaises(ValidationError):
            validar_archivo(con_macros, EXTENSIONES_PLANIFICACION)


class IntegracionBaseDatosTests(PruebaIdearia):
    def test_cp054_motor_de_base_de_datos(self):
        """CP-054: informa el motor usado por Django (sqlite en desarrollo, postgresql con Supabase)."""
        self.assertIn(connection.vendor, ("sqlite", "postgresql"))
        print(f"\n    [CP-054] Motor de base de datos en esta ejecución: {connection.vendor}")

    def test_catalogos_cargados_por_migracion(self):
        from planificaciones.models import Ambito, Nucleo

        self.assertEqual(Ambito.objects.count(), 3)
        self.assertEqual(Nucleo.objects.count(), 8)

    def test_comando_verificar_bd(self):
        """El comando de verificación informa el motor y no muestra credenciales."""
        crear_usuario(email="visible@prueba.test")
        salida = StringIO()
        call_command("verificar_bd", stdout=salida)
        texto = salida.getvalue()
        self.assertIn(f"Motor (connection.vendor): {connection.vendor}", texto)
        self.assertIn("Migraciones pendientes: 0", texto)
        self.assertIn("visible@prueba.test", texto)
        self.assertNotIn("PASSWORD", texto.upper().replace("CONTRASEÑA", ""))

    @mock.patch.dict(os.environ, {"DEMO_PASSWORD": "Clave-Demo-Prueba-1"})
    def test_comando_cargar_demo(self):
        salida = StringIO()
        call_command("cargar_demo", stdout=salida)
        self.assertEqual(Usuario.objects.filter(email__endswith="@idearia.test").count(), 5)
        self.assertEqual(Planificacion.objects.filter(estado=Planificacion.Estado.PUBLICADA).count(), 9)
        self.assertTrue(self.client.login(username="educadora@idearia.test", password="Clave-Demo-Prueba-1"))
