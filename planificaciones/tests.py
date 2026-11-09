"""Pruebas del catálogo, visor, propuestas del colaborador y revisión del administrador."""

import os

from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import override_settings
from django.urls import reverse

from core.models import RegistroAccion
from core.pruebas_utilidades import PruebaIdearia, crear_planificacion, crear_usuario, docx_subido, pdf_subido
from notificaciones.models import Notificacion
from planificaciones.models import Categoria, Material, Nucleo, Planificacion
from usuarios.models import Usuario

E = Planificacion.Estado


class CatalogoTests(PruebaIdearia):
    def setUp(self):
        super().setUp()
        self.colaboradora = crear_usuario(Usuario.Rol.COLABORADOR)
        self.educadora = crear_usuario()
        self.lupas = Material.objects.get(nombre="Lupas")
        self.pinturas = Material.objects.get(nombre="Pinturas")
        self.naturaleza = crear_planificacion(
            self.colaboradora, titulo="Pequeños exploradores", materiales=[self.lupas],
            nivel_educativo="NIVEL_MEDIO", edad_recomendada="3-4", duracion_minutos=45,
        )
        self.arte = crear_planificacion(
            self.colaboradora, titulo="Pintamos con esponjas", materiales=[self.pinturas, self.lupas],
            nivel_educativo="KINDER", edad_recomendada="5-6", duracion_minutos=20,
            nucleo=Nucleo.objects.get(nombre="Lenguajes Artísticos"), categorias=["Arte y creatividad"],
        )
        self.borrador = crear_planificacion(self.colaboradora, estado=E.BORRADOR, titulo="Idea en borrador")
        self.en_revision = crear_planificacion(self.colaboradora, estado=E.EN_REVISION, titulo="Idea en revisión")
        self.ingresar(self.educadora)

    def titulos(self, respuesta):
        return {p.titulo for p in respuesta.context["pagina"]}

    def test_cp016b_catalogo_solo_muestra_publicadas(self):
        """RF-16: el catálogo solo muestra propuestas en estado Publicada."""
        respuesta = self.client.get(reverse("planificaciones:catalogo"))
        self.assertEqual(self.titulos(respuesta), {"Pequeños exploradores", "Pintamos con esponjas"})

    def test_cp004_busqueda_por_palabra_clave(self):
        """CP-004: la palabra clave busca en título, descripción, OA, materiales y categorías."""
        self.assertEqual(self.titulos(self.client.get(reverse("planificaciones:catalogo"), {"q": "esponjas"})), {"Pintamos con esponjas"})
        self.assertEqual(self.titulos(self.client.get(reverse("planificaciones:catalogo"), {"q": "pinturas"})), {"Pintamos con esponjas"})

    def test_cp005_filtros_combinados(self):
        """CP-005: nivel + edad + duración devuelven solo las ideas que cumplen todo."""
        respuesta = self.client.get(
            reverse("planificaciones:catalogo"), {"nivel": "NIVEL_MEDIO", "edad": "3-4", "duracion": "media"}
        )
        self.assertEqual(self.titulos(respuesta), {"Pequeños exploradores"})
        self.assertEqual(len(respuesta.context["chips"]), 3)  # filtros activos visibles (RNF-12)
        respuesta = self.client.get(reverse("planificaciones:catalogo"), {"duracion": "corta"})
        self.assertEqual(self.titulos(respuesta), {"Pintamos con esponjas"})

    def test_cp006_filtro_por_materiales_disponibles(self):
        """CP-006: con solo 'Lupas' disponibles, no aparece la idea que también requiere pinturas."""
        respuesta = self.client.get(reverse("planificaciones:catalogo"), {"materiales": [self.lupas.pk]})
        self.assertEqual(self.titulos(respuesta), {"Pequeños exploradores"})

    def test_cp007_filtro_por_ambito_nucleo_y_categoria(self):
        """CP-007: filtros por ámbito, núcleo y categoría."""
        nucleo = Nucleo.objects.get(nombre="Lenguajes Artísticos")
        self.assertEqual(self.titulos(self.client.get(reverse("planificaciones:catalogo"), {"nucleo": nucleo.pk})), {"Pintamos con esponjas"})
        self.assertEqual(self.titulos(self.client.get(reverse("planificaciones:catalogo"), {"ambito": nucleo.ambito.pk})), {"Pintamos con esponjas"})
        categoria = Categoria.objects.get(nombre="Exploración y naturaleza")
        self.assertEqual(self.titulos(self.client.get(reverse("planificaciones:catalogo"), {"categoria": categoria.pk})), {"Pequeños exploradores"})

    def test_cp043_busqueda_sin_resultados(self):
        """CP-043: una búsqueda sin coincidencias muestra un mensaje claro."""
        respuesta = self.client.get(reverse("planificaciones:catalogo"), {"q": "astronomía cuántica"})
        self.assertEqual(respuesta.context["pagina"].paginator.count, 0)
        self.assertContains(respuesta, "No encontramos ideas con esos criterios")

    def test_cp053_parametros_manipulados_se_ignoran(self):
        """CP-053: valores inexistentes en la URL no provocan error 500."""
        respuesta = self.client.get(reverse("planificaciones:catalogo"), {"nivel": "UNIVERSIDAD", "nucleo": "abc", "page": "999"})
        self.assertEqual(respuesta.status_code, 200)

    def test_filtros_usan_cache_de_catalogos(self):
        """Optimización: los catálogos de los filtros se guardan en caché y se muestran igual."""
        from django.core.cache import cache

        respuesta = self.client.get(reverse("planificaciones:catalogo"))
        self.assertContains(respuesta, "Todos los ámbitos")
        self.assertContains(respuesta, "Comunicación Integral")
        self.assertIsNotNone(cache.get("catalogo:planificaciones.ambito"))
        nucleo = Nucleo.objects.get(nombre="Lenguajes Artísticos")
        respuesta = self.client.get(reverse("planificaciones:catalogo"), {"nucleo": nucleo.pk})
        self.assertContains(respuesta, f'<option value="{nucleo.pk}" selected>')

    def test_cp008_detalle_de_idea_publicada(self):
        """CP-008: el detalle muestra la información pedagógica completa."""
        respuesta = self.client.get(reverse("planificaciones:detalle", args=[self.naturaleza.pk]))
        self.assertContains(respuesta, "Pequeños exploradores")
        self.assertContains(respuesta, "Objetivo de aprendizaje")
        self.assertContains(respuesta, "Ver planificación")

    def test_cp047_idea_inexistente_o_no_publicada(self):
        """CP-047: ideas inexistentes o no publicadas responden 404 a un Educador/a."""
        self.assertEqual(self.client.get(reverse("planificaciones:detalle", args=[99999])).status_code, 404)
        self.assertEqual(self.client.get(reverse("planificaciones:detalle", args=[self.borrador.pk])).status_code, 404)
        self.assertEqual(self.client.get(reverse("planificaciones:detalle", args=[self.en_revision.pk])).status_code, 404)


class VisorTests(PruebaIdearia):
    def setUp(self):
        super().setUp()
        self.colaboradora = crear_usuario(Usuario.Rol.COLABORADOR)
        self.educadora = crear_usuario()
        self.pdf = crear_planificacion(self.colaboradora)
        self.ingresar(self.educadora)

    def test_cp009_visor_pdf_dentro_de_idearia(self):
        """CP-009: el visor carga PDF.js y no ofrece enlace de descarga."""
        respuesta = self.client.get(reverse("planificaciones:visor", args=[self.pdf.pk]))
        self.assertContains(respuesta, 'id="visor-pdf"')
        self.assertNotContains(respuesta, "download")
        self.assertNotContains(respuesta, "Descargar")

    def test_cp034_pdf_requiere_cabecera_del_visor(self):
        """CP-034: abrir la URL del PDF directamente da 403; desde el visor se entrega inline y sin caché."""
        url = reverse("planificaciones:documento", args=[self.pdf.pk])
        self.assertEqual(self.client.get(url).status_code, 403)
        respuesta = self.client.get(url, HTTP_X_IDEARIA_VISOR="1")
        self.assertEqual(respuesta.status_code, 200)
        self.assertEqual(respuesta["Content-Type"], "application/pdf")
        self.assertTrue(respuesta["Content-Disposition"].startswith("inline"))
        self.assertIn("no-store", respuesta["Cache-Control"])
        self.assertTrue(b"".join(respuesta.streaming_content).startswith(b"%PDF-"))

    def test_cp034b_pdf_anonimo_redirige_al_login(self):
        self.client.logout()
        respuesta = self.client.get(reverse("planificaciones:documento", args=[self.pdf.pk]), HTTP_X_IDEARIA_VISOR="1")
        self.assertEqual(respuesta.status_code, 302)

    def test_cp010_visor_docx_convertido_a_html(self):
        """CP-010: una planificación Word se muestra como HTML dentro de Idearia."""
        p = crear_planificacion(self.colaboradora, titulo="Idea Word")
        archivo = docx_subido()
        p.archivo.save("plan.docx", archivo, save=False)
        p.tipo_archivo = "docx"
        p.save()
        respuesta = self.client.get(reverse("planificaciones:visor", args=[p.pk]))
        self.assertContains(respuesta, "Planificación Word de prueba")
        self.assertContains(respuesta, "visor-docx")

    def test_archivos_subidos_no_tienen_url_publica(self):
        """Seguridad: la carpeta de archivos no se sirve directamente."""
        respuesta = self.client.get("/media_protegida/" + self.pdf.archivo.name)
        self.assertEqual(respuesta.status_code, 404)


def datos_propuesta(**cambios):
    datos = {
        "titulo": "Jugamos con la luz y las sombras",
        "nivel_educativo": "KINDER", "edad_recomendada": "5-6", "duracion_minutos": "45",
        "nucleo": Nucleo.objects.get(nombre="Exploración del Entorno Natural").pk,
        "objetivo_aprendizaje": "Formular explicaciones sobre la luz y la sombra.",
        "descripcion": "Experimentos con linternas.",
        "categorias": [Categoria.objects.get(nombre="Exploración y naturaleza").pk],
    }
    datos.update(cambios)
    return datos


class PropuestaColaboradorTests(PruebaIdearia):
    def setUp(self):
        super().setUp()
        self.colaboradora = crear_usuario(Usuario.Rol.COLABORADOR)
        self.admin = crear_usuario(Usuario.Rol.ADMINISTRADOR)
        self.ingresar(self.colaboradora)
        self.url = reverse("planificaciones:crear_propuesta")

    def test_cp016_guardar_borrador_incompleto(self):
        """CP-016: con solo el título se guarda como Borrador (RF-14)."""
        self.client.post(self.url, {"titulo": "Idea en preparación", "accion": "guardar"})
        p = Planificacion.objects.get(titulo="Idea en preparación")
        self.assertEqual(p.estado, E.BORRADOR)
        self.assertEqual(p.colaborador, self.colaboradora)

    def test_cp017_envio_a_revision_con_archivo(self):
        """CP-017 / CP-056: con datos completos y PDF, queda En revisión; archivo guardado y referenciado."""
        respuesta = self.client.post(self.url, datos_propuesta(archivo=pdf_subido("Mi planificación.pdf"), accion="enviar"))
        self.assertRedirects(respuesta, reverse("planificaciones:mis_propuestas"))
        p = Planificacion.objects.get(titulo="Jugamos con la luz y las sombras")
        self.assertEqual(p.estado, E.EN_REVISION)
        self.assertIsNotNone(p.fecha_envio)
        # Integración archivo <-> base de datos
        self.assertTrue(p.archivo.name.startswith("planificaciones/"))
        self.assertNotIn("Mi planificación", p.archivo.name)  # nombre en disco aleatorio
        self.assertEqual(p.nombre_archivo, "Mi_planificación.pdf")
        self.assertEqual(p.tipo_archivo, "pdf")
        self.assertEqual(p.tamano_archivo, p.archivo.size)
        self.assertTrue(os.path.exists(p.archivo.path))
        # Notificación a administradores (RF-17)
        self.assertTrue(Notificacion.objects.filter(usuario=self.admin, tipo=Notificacion.Tipo.NUEVA_PROPUESTA).exists())

    def test_cp017b_envio_sin_archivo_es_rechazado(self):
        """CP-017 / RF-13: no se puede enviar a revisión sin planificación adjunta."""
        respuesta = self.client.post(self.url, datos_propuesta(accion="enviar"))
        self.assertIn("archivo", respuesta.context["form"].errors)
        self.assertFalse(Planificacion.objects.filter(estado=E.EN_REVISION).exists())

    def test_cp033d_envio_sin_campos_obligatorios(self):
        """CP-033: al enviar, los campos pedagógicos son obligatorios."""
        respuesta = self.client.post(self.url, {"titulo": "Incompleta", "accion": "enviar", "archivo": pdf_subido()})
        errores = respuesta.context["form"].errors
        for campo in ("descripcion", "nivel_educativo", "nucleo", "objetivo_aprendizaje", "duracion_minutos", "categorias"):
            self.assertIn(campo, errores)

    def test_cp030_archivo_extension_no_permitida(self):
        """CP-030: un .exe es rechazado."""
        exe = SimpleUploadedFile("virus.exe", b"MZ\x90\x00" + b"0" * 100, "application/octet-stream")
        respuesta = self.client.post(self.url, datos_propuesta(archivo=exe, accion="enviar"))
        self.assertIn("Formato no permitido", str(respuesta.context["form"].errors["archivo"]))

    def test_cp030b_formato_doc_antiguo_no_permitido(self):
        """CP-030: el formato .doc (Word 97-2003) no se acepta (decisión documentada)."""
        doc = SimpleUploadedFile("plan.doc", b"\xd0\xcf\x11\xe0" + b"0" * 100, "application/msword")
        respuesta = self.client.post(self.url, datos_propuesta(archivo=doc, accion="enviar"))
        self.assertIn("archivo", respuesta.context["form"].errors)

    def test_cp031_contenido_falso_con_extension_valida(self):
        """CP-031: un ejecutable renombrado a .pdf es detectado por su firma."""
        falso = SimpleUploadedFile("plan.pdf", b"MZ\x90\x00 esto no es un pdf", "application/pdf")
        respuesta = self.client.post(self.url, datos_propuesta(archivo=falso, accion="enviar"))
        self.assertIn("no corresponde a su extensión", str(respuesta.context["form"].errors["archivo"]))

    @override_settings(TAMANO_MAXIMO_ARCHIVO_MB=1)
    def test_cp032_archivo_demasiado_grande(self):
        """CP-032: un archivo sobre el máximo permitido es rechazado (se usa 1 MB para la prueba)."""
        grande = SimpleUploadedFile("plan.pdf", b"%PDF-1.4\n" + b"0" * (1024 * 1024 + 10), "application/pdf")
        respuesta = self.client.post(self.url, datos_propuesta(archivo=grande, accion="enviar"))
        self.assertIn("supera el tamaño máximo", str(respuesta.context["form"].errors["archivo"]))

    def test_cp044b_titulo_excesivamente_largo(self):
        """CP-044: un título de más de 120 caracteres es rechazado."""
        respuesta = self.client.post(self.url, {"titulo": "A" * 121, "accion": "guardar"})
        self.assertIn("titulo", respuesta.context["form"].errors)

    def test_cp036_no_puede_editar_propuesta_ajena(self):
        """CP-036: un colaborador que intenta editar la propuesta de otro recibe 404."""
        otra = crear_planificacion(crear_usuario(Usuario.Rol.COLABORADOR), estado=E.BORRADOR)
        respuesta = self.client.get(reverse("planificaciones:editar_propuesta", args=[otra.pk]))
        self.assertEqual(respuesta.status_code, 404)

    def test_cp027b_educador_no_puede_crear_propuestas(self):
        """CP-027: un Educador/a que entra a /colaborador/propuestas/nueva/ recibe 403."""
        self.ingresar(crear_usuario())
        self.assertEqual(self.client.get(self.url).status_code, 403)

    def test_propuesta_en_revision_no_se_edita(self):
        """COL-06: una propuesta ya enviada no se puede editar ni reenviar."""
        p = crear_planificacion(self.colaboradora, estado=E.EN_REVISION)
        respuesta = self.client.get(reverse("planificaciones:editar_propuesta", args=[p.pk]))
        self.assertRedirects(respuesta, reverse("planificaciones:mis_propuestas"))

    def test_reemplazar_archivo_elimina_el_anterior(self):
        p = crear_planificacion(self.colaboradora, estado=E.BORRADOR)
        ruta_anterior = p.archivo.path
        self.client.post(
            reverse("planificaciones:editar_propuesta", args=[p.pk]),
            datos_propuesta(titulo=p.titulo, archivo=docx_subido(), accion="guardar"),
        )
        p.refresh_from_db()
        self.assertEqual(p.tipo_archivo, "docx")
        self.assertFalse(os.path.exists(ruta_anterior))


class RevisionAdministradorTests(PruebaIdearia):
    def setUp(self):
        super().setUp()
        self.colaboradora = crear_usuario(Usuario.Rol.COLABORADOR)
        self.admin = crear_usuario(Usuario.Rol.ADMINISTRADOR)
        self.propuesta = crear_planificacion(self.colaboradora, estado=E.EN_REVISION, titulo="Propuesta en revisión")
        self.ingresar(self.admin)

    def accion(self, accion, observacion=""):
        return self.client.post(
            reverse("planificaciones:admin_accion", args=[self.propuesta.pk]),
            {"accion": accion, "observacion": observacion},
        )

    def estado(self):
        self.propuesta.refresh_from_db()
        return self.propuesta.estado

    def test_cp018_cp019_aprobar_y_publicar(self):
        """CP-018 / CP-019 / CP-023 / CP-025: aprobar y publicar; aparece en el catálogo, notifica y audita."""
        self.accion("aprobar")
        self.assertEqual(self.estado(), E.APROBADA)
        self.client.force_login(crear_usuario())
        self.assertNotContains(self.client.get(reverse("planificaciones:catalogo")), "Propuesta en revisión")
        self.ingresar(self.admin)
        self.accion("publicar")
        self.assertEqual(self.estado(), E.PUBLICADA)
        self.assertIsNotNone(self.propuesta.fecha_publicacion)
        self.client.force_login(crear_usuario())
        self.assertContains(self.client.get(reverse("planificaciones:catalogo")), "Propuesta en revisión")
        tipos = set(Notificacion.objects.filter(usuario=self.colaboradora).values_list("tipo", flat=True))
        self.assertEqual(tipos, {Notificacion.Tipo.PROPUESTA_APROBADA, Notificacion.Tipo.PROPUESTA_PUBLICADA})
        acciones = set(RegistroAccion.objects.values_list("accion", flat=True))
        self.assertTrue({RegistroAccion.Accion.APROBAR_PROPUESTA, RegistroAccion.Accion.PUBLICAR_PROPUESTA} <= acciones)
        self.assertEqual(RegistroAccion.objects.first().usuario, self.admin)

    def test_cp021_rechazo_exige_motivo(self):
        """CP-021: sin motivo no se rechaza; con motivo queda Rechazada y guarda la observación."""
        self.accion("rechazar")
        self.assertEqual(self.estado(), E.EN_REVISION)
        self.accion("rechazar", "No corresponde a Educación Parvularia.")
        self.assertEqual(self.estado(), E.RECHAZADA)
        self.assertEqual(self.propuesta.observacion_revision, "No corresponde a Educación Parvularia.")

    def test_cp048_propuesta_rechazada_no_se_puede_editar(self):
        """CP-048: una propuesta Rechazada es definitiva para el colaborador."""
        self.accion("rechazar", "Motivo")
        self.client.force_login(self.colaboradora)
        respuesta = self.client.get(reverse("planificaciones:editar_propuesta", args=[self.propuesta.pk]))
        self.assertRedirects(respuesta, reverse("planificaciones:mis_propuestas"))
        with self.assertRaises(Exception):
            self.propuesta.enviar_a_revision()

    def test_cp020_solicitar_correccion_y_reenviar(self):
        """CP-020: el administrador pide cambios; el colaborador corrige y reenvía (vuelve a En revisión)."""
        self.accion("corregir", "Precisa el objetivo de aprendizaje.")
        self.assertEqual(self.estado(), E.REQUIERE_CORRECCION)
        self.assertTrue(Notificacion.objects.filter(usuario=self.colaboradora, tipo=Notificacion.Tipo.CORRECCION_SOLICITADA).exists())
        self.client.force_login(self.colaboradora)
        respuesta = self.client.post(
            reverse("planificaciones:editar_propuesta", args=[self.propuesta.pk]),
            datos_propuesta(titulo="Propuesta corregida", accion="enviar"),
        )
        self.assertRedirects(respuesta, reverse("planificaciones:mis_propuestas"))
        self.assertEqual(self.estado(), E.EN_REVISION)

    def test_cp022_retirar_publicacion(self):
        """CP-022: una idea retirada deja de aparecer en el catálogo."""
        self.accion("aprobar")
        self.accion("publicar")
        self.accion("retirar", "Contenido duplicado.")
        self.assertEqual(self.estado(), E.RETIRADA)
        self.client.force_login(crear_usuario())
        self.assertNotContains(self.client.get(reverse("planificaciones:catalogo")), "Propuesta en revisión")

    def test_cp052_transicion_invalida(self):
        """CP-052: no se puede publicar una propuesta que no fue aprobada."""
        respuesta = self.accion("publicar")
        self.assertEqual(self.estado(), E.EN_REVISION)
        mensajes = [str(m) for m in respuesta.wsgi_request._messages]
        self.assertTrue(any("No se puede realizar esta acción" in m for m in mensajes))

    def test_cp029_educador_no_puede_ejecutar_acciones_admin(self):
        """CP-029: un Educador/a que envía el POST de aprobación recibe 403 y nada cambia."""
        self.client.force_login(crear_usuario())
        respuesta = self.accion("aprobar")
        self.assertEqual(respuesta.status_code, 403)
        self.assertEqual(self.estado(), E.EN_REVISION)

    def test_cp029b_colaborador_no_puede_aprobar_su_propuesta(self):
        self.client.force_login(self.colaboradora)
        self.assertEqual(self.accion("aprobar").status_code, 403)
        self.assertEqual(self.estado(), E.EN_REVISION)

    def test_no_se_aprueba_con_datos_faltantes(self):
        """ADM-05/06: una propuesta incompleta no puede aprobarse."""
        self.propuesta.objetivo_aprendizaje = ""
        self.propuesta.save()
        self.accion("aprobar")
        self.assertEqual(self.estado(), E.EN_REVISION)

    def test_pantalla_de_revision_muestra_propuesta(self):
        respuesta = self.client.get(reverse("planificaciones:admin_revision"))
        self.assertContains(respuesta, "Propuesta en revisión")
        self.assertEqual(respuesta.context["seleccion"], self.propuesta)
