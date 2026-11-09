"""Pruebas de favoritos, valoraciones y comentarios."""

from django.db import IntegrityError, transaction
from django.urls import reverse

from core.pruebas_utilidades import PruebaIdearia, crear_planificacion, crear_usuario
from interacciones.models import Comentario, Favorito, Valoracion
from planificaciones.models import Planificacion
from usuarios.models import Usuario


class InteraccionesTests(PruebaIdearia):
    def setUp(self):
        super().setUp()
        self.colaboradora = crear_usuario(Usuario.Rol.COLABORADOR)
        self.educadora = crear_usuario()
        self.idea = crear_planificacion(self.colaboradora, titulo="Idea publicada")
        self.ingresar(self.educadora)

    def favorito(self, accion):
        return self.client.post(reverse("interacciones:favorito", args=[self.idea.pk]), {"accion": accion})

    def test_cp011_agregar_y_quitar_favorito(self):
        """CP-011: agregar a favoritos, verlo en la lista y quitarlo (RF-07/08)."""
        self.favorito("agregar")
        respuesta = self.client.get(reverse("interacciones:mis_favoritos"))
        self.assertContains(respuesta, "Idea publicada")
        self.favorito("quitar")
        self.assertFalse(Favorito.objects.filter(usuario=self.educadora).exists())

    def test_cp045_favorito_no_se_duplica(self):
        """CP-045: dos clics en 'agregar' dejan un solo registro; la BD impide duplicados."""
        self.favorito("agregar")
        self.favorito("agregar")
        self.assertEqual(Favorito.objects.filter(usuario=self.educadora, planificacion=self.idea).count(), 1)
        with self.assertRaises(IntegrityError), transaction.atomic():
            Favorito.objects.create(usuario=self.educadora, planificacion=self.idea)

    def test_cp012_valorar_idea(self):
        """CP-012: la valoración se guarda y se refleja en el detalle."""
        self.client.post(reverse("interacciones:valorar", args=[self.idea.pk]), {"puntuacion": "4"})
        self.assertEqual(Valoracion.objects.get(usuario=self.educadora).puntuacion, 4)
        respuesta = self.client.get(reverse("planificaciones:detalle", args=[self.idea.pk]))
        self.assertEqual(respuesta.context["resumen"]["total"], 1)

    def test_cp046_doble_valoracion_actualiza(self):
        """CP-046: valorar dos veces actualiza la valoración (1 registro); la BD impide duplicados."""
        url = reverse("interacciones:valorar", args=[self.idea.pk])
        self.client.post(url, {"puntuacion": "5"})
        self.client.post(url, {"puntuacion": "2"})
        self.assertEqual(Valoracion.objects.filter(usuario=self.educadora).count(), 1)
        self.assertEqual(Valoracion.objects.get(usuario=self.educadora).puntuacion, 2)
        with self.assertRaises(IntegrityError), transaction.atomic():
            Valoracion.objects.create(usuario=self.educadora, planificacion=self.idea, puntuacion=3)

    def test_valoracion_fuera_de_rango(self):
        """La puntuación debe estar entre 1 y 5 (formulario y restricción CHECK en la BD)."""
        self.client.post(reverse("interacciones:valorar", args=[self.idea.pk]), {"puntuacion": "9"})
        self.assertFalse(Valoracion.objects.exists())
        otra = crear_usuario()
        with self.assertRaises(IntegrityError), transaction.atomic():
            Valoracion.objects.create(usuario=otra, planificacion=self.idea, puntuacion=9)

    def test_cp051_autor_no_valora_su_propuesta(self):
        """CP-051: el autor no puede valorar su propia propuesta."""
        self.client.force_login(self.colaboradora)
        self.client.post(reverse("interacciones:valorar", args=[self.idea.pk]), {"puntuacion": "5"})
        self.assertFalse(Valoracion.objects.exists())

    def test_cp013_comentar_idea(self):
        """CP-013: un comentario válido se publica y aparece en el detalle."""
        self.client.post(reverse("interacciones:comentar", args=[self.idea.pk]), {"contenido": "La apliqué y funcionó muy bien."})
        respuesta = self.client.get(reverse("planificaciones:detalle", args=[self.idea.pk]))
        self.assertContains(respuesta, "La apliqué y funcionó muy bien.")

    def test_comentario_vacio_no_se_publica(self):
        """EDU-08 E3: comentario vacío o solo espacios no se publica."""
        self.client.post(reverse("interacciones:comentar", args=[self.idea.pk]), {"contenido": "   "})
        self.assertFalse(Comentario.objects.exists())

    def test_cp044c_comentario_excesivamente_largo(self):
        """CP-044: un comentario de más de 1000 caracteres es rechazado."""
        self.client.post(reverse("interacciones:comentar", args=[self.idea.pk]), {"contenido": "a" * 1001})
        self.assertFalse(Comentario.objects.exists())

    def test_cp042_comentario_con_script_se_muestra_escapado(self):
        """CP-042: un intento de XSS en un comentario se muestra como texto, no se ejecuta."""
        self.client.post(reverse("interacciones:comentar", args=[self.idea.pk]), {"contenido": "<script>alert('x')</script>"})
        respuesta = self.client.get(reverse("planificaciones:detalle", args=[self.idea.pk]))
        self.assertNotContains(respuesta, "<script>alert('x')</script>")
        self.assertContains(respuesta, "&lt;script&gt;alert(&#x27;x&#x27;)&lt;/script&gt;")

    def test_no_se_interactua_con_ideas_no_publicadas(self):
        """Solo se puede marcar favorito, valorar o comentar ideas publicadas."""
        borrador = crear_planificacion(self.colaboradora, estado=Planificacion.Estado.BORRADOR)
        self.assertEqual(self.client.post(reverse("interacciones:favorito", args=[borrador.pk]), {"accion": "agregar"}).status_code, 404)
        self.assertEqual(self.client.post(reverse("interacciones:comentar", args=[borrador.pk]), {"contenido": "Hola mundo"}).status_code, 404)

    def test_administrador_no_marca_favoritos(self):
        """Matriz de permisos: el Administrador no usa favoritos ni valoraciones."""
        self.client.force_login(crear_usuario(Usuario.Rol.ADMINISTRADOR))
        self.assertEqual(self.favorito("agregar").status_code, 403)

    def test_administrador_oculta_comentario(self):
        """Moderación: un comentario oculto deja de verse para los educadores."""
        comentario = Comentario.objects.create(usuario=self.educadora, planificacion=self.idea, contenido="Comentario inapropiado")
        self.client.force_login(crear_usuario(Usuario.Rol.ADMINISTRADOR))
        self.client.post(reverse("interacciones:moderar_comentario", args=[comentario.pk]))
        self.client.force_login(self.educadora)
        self.assertNotContains(self.client.get(reverse("planificaciones:detalle", args=[self.idea.pk])), "Comentario inapropiado")

    def test_get_no_modifica_datos(self):
        """Las acciones que modifican datos solo aceptan POST."""
        self.assertEqual(self.client.get(reverse("interacciones:favorito", args=[self.idea.pk])).status_code, 405)
