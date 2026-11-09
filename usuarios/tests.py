"""Pruebas de autenticación, registro, roles y gestión de usuarios."""

from django.test import Client
from django.urls import reverse

from core.models import RegistroAccion
from core.pruebas_utilidades import CLAVE, PruebaIdearia, crear_usuario, rut_valido
from usuarios.models import Usuario
from usuarios.validators import normalizar_rut, validar_rut


def datos_registro(**cambios):
    datos = {
        "first_name": "Valentina", "last_name": "Mora", "rut": rut_valido(),
        "email": "valentina@prueba.test", "fecha_nacimiento": "1995-04-10",
        "password1": CLAVE, "password2": CLAVE,
    }
    datos.update(cambios)
    return datos


class RegistroTests(PruebaIdearia):
    def test_cp001_registro_correcto(self):
        """CP-001: el registro crea un Educador/a, inicia sesión y redirige al catálogo."""
        respuesta = self.client.post(reverse("usuarios:registro"), datos_registro(), follow=True)
        usuario = Usuario.objects.get(email="valentina@prueba.test")
        self.assertEqual(usuario.rol, Usuario.Rol.EDUCADOR)
        self.assertRedirects(respuesta, reverse("planificaciones:catalogo"))
        self.assertContains(respuesta, "Registro realizado exitosamente")
        self.assertTrue(respuesta.context["user"].is_authenticated)

    def test_cp033_registro_sin_datos_obligatorios(self):
        """CP-033: un formulario vacío no crea usuario y marca los campos obligatorios."""
        respuesta = self.client.post(reverse("usuarios:registro"), {})
        self.assertEqual(respuesta.status_code, 200)
        self.assertEqual(Usuario.objects.count(), 0)
        for campo in ("first_name", "last_name", "rut", "email", "fecha_nacimiento", "password1"):
            self.assertIn(campo, respuesta.context["form"].errors)

    def test_cp033b_registro_correo_duplicado(self):
        """CP-033: no se permite registrar un correo ya existente (sin importar mayúsculas)."""
        crear_usuario(email="valentina@prueba.test")
        respuesta = self.client.post(reverse("usuarios:registro"), datos_registro(email="VALENTINA@prueba.test"))
        self.assertFormError(respuesta.context["form"], "email", "Ya existe una cuenta asociada a este correo.")

    def test_cp033c_registro_rut_invalido(self):
        """CP-033: un RUT con dígito verificador incorrecto es rechazado."""
        respuesta = self.client.post(reverse("usuarios:registro"), datos_registro(rut="12345678-0"))
        self.assertFormError(respuesta.context["form"], "rut", "El RUT ingresado no es válido.")

    def test_cp039_no_se_puede_escalar_rol_desde_el_registro(self):
        """CP-039: aunque se inyecte rol=ADMINISTRADOR en el POST, el usuario queda como Educador/a."""
        self.client.post(reverse("usuarios:registro"), datos_registro(rol="ADMINISTRADOR", is_superuser="on"))
        usuario = Usuario.objects.get(email="valentina@prueba.test")
        self.assertEqual(usuario.rol, Usuario.Rol.EDUCADOR)
        self.assertFalse(usuario.is_superuser)

    def test_cp037_contrasena_almacenada_con_hash(self):
        """CP-037: la contraseña se guarda con hash PBKDF2, nunca en texto plano."""
        self.client.post(reverse("usuarios:registro"), datos_registro())
        usuario = Usuario.objects.get(email="valentina@prueba.test")
        self.assertNotEqual(usuario.password, CLAVE)
        self.assertTrue(usuario.password.startswith("pbkdf2_sha256$"))
        self.assertTrue(usuario.check_password(CLAVE))

    def test_cp044_nombre_excesivamente_largo(self):
        """CP-044: textos que exceden el largo máximo son rechazados."""
        respuesta = self.client.post(reverse("usuarios:registro"), datos_registro(first_name="A" * 151))
        self.assertIn("first_name", respuesta.context["form"].errors)

    def test_registro_menor_de_edad(self):
        respuesta = self.client.post(reverse("usuarios:registro"), datos_registro(fecha_nacimiento="2015-01-01"))
        self.assertIn("fecha_nacimiento", respuesta.context["form"].errors)


class LoginTests(PruebaIdearia):
    def setUp(self):
        super().setUp()
        self.usuario = crear_usuario(email="educadora@prueba.test")

    def test_cp002_login_correcto(self):
        """CP-002: credenciales válidas inician sesión (el correo no distingue mayúsculas)."""
        respuesta = self.client.post(
            reverse("usuarios:login"), {"username": "EDUCADORA@prueba.test", "password": CLAVE}
        )
        self.assertRedirects(respuesta, reverse("core:inicio"), target_status_code=302)
        self.assertEqual(int(self.client.session["_auth_user_id"]), self.usuario.pk)

    def test_cp026_login_incorrecto(self):
        """CP-026: contraseña incorrecta -> mensaje genérico y sin sesión."""
        respuesta = self.client.post(reverse("usuarios:login"), {"username": "educadora@prueba.test", "password": "mala"})
        self.assertEqual(respuesta.status_code, 200)
        self.assertContains(respuesta, "Correo o contraseña incorrectos.")
        self.assertNotIn("_auth_user_id", self.client.session)

    def test_cp038_bloqueo_tras_intentos_fallidos(self):
        """CP-038: tras 5 intentos fallidos, incluso la contraseña correcta es bloqueada temporalmente."""
        for _ in range(5):
            self.client.post(reverse("usuarios:login"), {"username": "educadora@prueba.test", "password": "mala"})
        respuesta = self.client.post(reverse("usuarios:login"), {"username": "educadora@prueba.test", "password": CLAVE})
        self.assertContains(respuesta, "Demasiados intentos fallidos")
        self.assertNotIn("_auth_user_id", self.client.session)

    def test_cp049_usuario_desactivado_no_puede_ingresar(self):
        """CP-049: una cuenta desactivada no puede iniciar sesión (mismo mensaje genérico)."""
        self.usuario.is_active = False
        self.usuario.save()
        respuesta = self.client.post(reverse("usuarios:login"), {"username": "educadora@prueba.test", "password": CLAVE})
        self.assertContains(respuesta, "Correo o contraseña incorrectos.")
        self.assertNotIn("_auth_user_id", self.client.session)

    def test_cp003_logout_solo_por_post(self):
        """CP-003: cerrar sesión exige POST; GET no cierra la sesión."""
        self.ingresar(self.usuario)
        self.assertEqual(self.client.get(reverse("usuarios:logout")).status_code, 405)
        respuesta = self.client.post(reverse("usuarios:logout"))
        self.assertRedirects(respuesta, reverse("usuarios:login"))
        self.assertNotIn("_auth_user_id", self.client.session)

    def test_cp035_post_sin_token_csrf_es_rechazado(self):
        """CP-035: un formulario enviado sin token CSRF recibe 403."""
        cliente = Client(enforce_csrf_checks=True)
        respuesta = cliente.post(reverse("usuarios:login"), {"username": "educadora@prueba.test", "password": CLAVE})
        self.assertEqual(respuesta.status_code, 403)


class PermisosAdministracionUsuariosTests(PruebaIdearia):
    def setUp(self):
        super().setUp()
        self.admin = crear_usuario(Usuario.Rol.ADMINISTRADOR, email="admin@prueba.test")
        self.educadora = crear_usuario(email="edu@prueba.test")

    def test_cp027_educador_no_accede_a_gestion_de_usuarios(self):
        """CP-027: un Educador/a que escribe la URL de administración recibe 403."""
        self.ingresar(self.educadora)
        self.assertEqual(self.client.get(reverse("usuarios:admin_lista")).status_code, 403)

    def test_cp028_anonimo_es_enviado_al_login(self):
        """CP-028: sin sesión, una URL protegida redirige al inicio de sesión."""
        respuesta = self.client.get(reverse("usuarios:admin_lista"))
        self.assertRedirects(respuesta, f"{reverse('usuarios:login')}?next={reverse('usuarios:admin_lista')}")

    def test_cp024_admin_desactiva_y_reactiva_usuario(self):
        """CP-024 / CP-025: el administrador desactiva y reactiva cuentas; queda auditado."""
        self.ingresar(self.admin)
        url = reverse("usuarios:admin_cambiar_estado", args=[self.educadora.pk])
        self.client.post(url)
        self.educadora.refresh_from_db()
        self.assertFalse(self.educadora.is_active)
        self.client.post(url)
        self.educadora.refresh_from_db()
        self.assertTrue(self.educadora.is_active)
        acciones = list(RegistroAccion.objects.values_list("accion", flat=True))
        self.assertIn(RegistroAccion.Accion.DESACTIVAR_USUARIO, acciones)
        self.assertIn(RegistroAccion.Accion.ACTIVAR_USUARIO, acciones)

    def test_admin_no_puede_desactivarse_a_si_mismo(self):
        self.ingresar(self.admin)
        self.client.post(reverse("usuarios:admin_cambiar_estado", args=[self.admin.pk]))
        self.admin.refresh_from_db()
        self.assertTrue(self.admin.is_active)

    def test_redireccion_externa_es_ignorada(self):
        """Seguridad: el parámetro 'volver' no permite redirigir a otro sitio (open redirect)."""
        self.ingresar(self.admin)
        respuesta = self.client.post(
            reverse("usuarios:admin_cambiar_estado", args=[self.educadora.pk]), {"volver": "https://sitio-malicioso.test/"}
        )
        self.assertRedirects(respuesta, reverse("usuarios:admin_lista"))


class RutTests(PruebaIdearia):
    def test_rut_valido_e_invalido(self):
        validar_rut("11.111.111-1")
        self.assertEqual(normalizar_rut("12.345.678-5"), "12345678-5")
        with self.assertRaises(Exception):
            validar_rut("12345678-9")
