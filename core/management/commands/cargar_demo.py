"""
Carga datos de demostración para presentar Idearia.

Uso:
    .\\.venv\\Scripts\\python.exe manage.py cargar_demo
    .\\.venv\\Scripts\\python.exe manage.py cargar_demo --reiniciar

La contraseña de los usuarios de prueba se lee de DEMO_PASSWORD (.env).
Todos los correos usan el dominio reservado ".test" (no son cuentas reales).
"""

import os
from datetime import timedelta

from django.core.files.base import ContentFile
from django.core.management.base import BaseCommand, CommandError
from django.db import transaction
from django.utils import timezone
from django.utils.text import slugify

from colaboradores.models import SolicitudColaborador
from core.documentos_demo import generar_docx, generar_pdf
from interacciones.models import Comentario, Favorito, Valoracion
from planificaciones.models import Categoria, Material, Nucleo, Planificacion
from usuarios.models import Usuario
from usuarios.validators import calcular_digito_verificador

DOMINIO = "@idearia.test"

USUARIOS = [
    # correo, nombres, apellidos, cuerpo RUT, rol
    ("administradora", "María", "Fernández", "11111111", Usuario.Rol.ADMINISTRADOR),
    ("colaboradora", "Camila", "Rojas", "15555555", Usuario.Rol.COLABORADOR),
    ("colaborador2", "Francisco", "Núñez", "16666666", Usuario.Rol.COLABORADOR),
    ("educadora", "Valentina", "Mora", "17777777", Usuario.Rol.EDUCADOR),
    ("postulante", "Paula", "Martínez", "18888888", Usuario.Rol.EDUCADOR),
]

E = Planificacion.Estado
IDEAS = [
    # (titulo, autor, estado, nivel, edad, nucleo, duracion, categorias, materiales, objetivo, descripcion, formato)
    ("Exploramos la naturaleza con todos los sentidos", "colaboradora", E.PUBLICADA, "NIVEL_MEDIO", "3-4",
     "Exploración del Entorno Natural", 45, ["Exploración y naturaleza", "Sensorial"],
     ["Elementos naturales (hojas, piedras, ramas)", "Lupas", "Recipientes y bandejas"],
     "Explorar y describir características de elementos naturales utilizando sus sentidos.",
     "Experiencia para observar, tocar, oler y describir elementos naturales del entorno cercano, "
     "registrando descubrimientos en grupo.", "pdf"),
    ("Cuentos que nos hacen sentir", "colaboradora", E.PUBLICADA, "PREKINDER", "4-5",
     "Lenguaje Verbal", 30, ["Lenguaje y cuentos", "Emociones y convivencia"], ["Cuentos e imágenes"],
     "Comprender y expresar emociones de personajes a partir de la lectura compartida de cuentos.",
     "Lectura de cuentos para reconocer, nombrar y conversar sobre emociones propias y de los personajes.", "docx"),
    ("Arte con elementos de la naturaleza", "colaborador2", E.PUBLICADA, "KINDER", "5-6",
     "Lenguajes Artísticos", 60, ["Arte y creatividad", "Exploración y naturaleza"],
     ["Elementos naturales (hojas, piedras, ramas)", "Pinturas", "Papel y cartulina"],
     "Crear composiciones plásticas con materiales naturales, explorando colores y texturas.",
     "Creación de obras con hojas, ramas y piedras, explorando colores, texturas y formas.", "pdf"),
    ("Pequeños exploradores del jardín", "colaboradora", E.PUBLICADA, "NIVEL_MEDIO", "2-3",
     "Exploración del Entorno Natural", 30, ["Exploración y naturaleza", "Cuidado del medioambiente"], ["Lupas"],
     "Observar seres vivos del entorno y manifestar interés por su cuidado.",
     "Salida al patio para observar insectos, plantas y otros seres vivos, valorando la biodiversidad.", "pdf"),
    ("Cocinamos una colación saludable", "colaborador2", E.PUBLICADA, "KINDER", "5-6",
     "Identidad y Autonomía", 60, ["Vida saludable"], ["Alimentos para preparar", "Recipientes y bandejas"],
     "Reconocer alimentos saludables y participar en su preparación con autonomía creciente.",
     "Preparación de una receta simple para conocer alimentos saludables y conversar sobre sus beneficios.", "pdf"),
    ("Construimos y creamos juntos", "colaborador2", E.PUBLICADA, "PREKINDER", "4-5",
     "Convivencia y Ciudadanía", 45, ["Juego y movimiento", "Emociones y convivencia"],
     ["Bloques o material de construcción"],
     "Participar en juegos colaborativos acordando roles y resolviendo conflictos con ayuda.",
     "Propuesta lúdica para promover la cooperación, la resolución de problemas y la creatividad en equipo.", "pdf"),
    ("Exploramos los colores con pintura y esponjas", "colaboradora", E.PUBLICADA, "SALA_CUNA", "0-2",
     "Lenguajes Artísticos", 20, ["Arte y creatividad", "Sensorial"], ["Pinturas", "Esponjas y pinceles", "Papel y cartulina"],
     "Experimentar con diferentes colores, texturas y herramientas, desarrollando la coordinación motriz.",
     "Experiencia sensorial para descubrir y mezclar colores con pintura y distintos tipos de esponjas.", "docx"),
    ("Ritmos que nos hacen mover", "colaborador2", E.PUBLICADA, "NIVEL_MEDIO", "3-4",
     "Corporalidad y Movimiento", 30, ["Música y ritmo", "Juego y movimiento"],
     ["Instrumentos musicales", "Reproductor de música"],
     "Coordinar movimientos corporales siguiendo ritmos y pulsos musicales.",
     "Juegos de movimiento con canciones e instrumentos para explorar ritmos rápidos y lentos.", "pdf"),
    ("Contamos y clasificamos tesoros", "colaboradora", E.PUBLICADA, "KINDER", "5-6",
     "Pensamiento Matemático", 45, ["Pensamiento matemático"],
     ["Elementos naturales (hojas, piedras, ramas)", "Recipientes y bandejas"],
     "Emplear cuantificadores y contar colecciones de objetos, clasificándolos por atributos.",
     "Recolección de tesoros naturales para contarlos, compararlos y clasificarlos por forma, color y tamaño.", "pdf"),
    # Estados distintos para demostrar el flujo de revisión
    ("Jugamos con la luz y las sombras", "colaboradora", E.EN_REVISION, "KINDER", "5-6",
     "Exploración del Entorno Natural", 45, ["Exploración y naturaleza"], ["Telas y pañuelos"],
     "Formular explicaciones sobre fenómenos de luz y sombra a partir de la experimentación.",
     "Experimentos con linternas y objetos para descubrir cómo se forman y cambian las sombras.", "pdf"),
    ("Nuestras emociones también se expresan", "colaborador2", E.EN_REVISION, "PREKINDER", "4-5",
     "Identidad y Autonomía", 30, ["Emociones y convivencia"], ["Papel y cartulina", "Lápices de colores"],
     "Expresar emociones y sentimientos mediante el lenguaje verbal y artístico.",
     "Creación de un mural de emociones donde cada niño y niña expresa cómo se siente.", "docx"),
    ("Masa sensorial casera", "colaboradora", E.REQUIERE_CORRECCION, "SALA_CUNA", "0-2",
     "Corporalidad y Movimiento", 20, ["Sensorial"], ["Masa o plasticina"],
     "Explorar texturas y fortalecer la motricidad fina manipulando masa.",
     "Manipulación libre de masa sensorial con distintos aromas y colores.", "pdf"),
    ("Reciclamos y creamos instrumentos", "colaboradora", E.BORRADOR, "PREKINDER", "4-5",
     "Lenguajes Artísticos", 60, ["Música y ritmo", "Cuidado del medioambiente"], ["Material reciclado"],
     "", "Borrador en preparación.", "pdf"),
]

COMENTARIOS = [
    ("educadora", "Exploramos la naturaleza con todos los sentidos",
     "La apliqué con mi grupo de nivel medio y fue muy entretenida. Agregamos una caja sorpresa con texturas."),
    ("colaborador2", "Exploramos la naturaleza con todos los sentidos",
     "Excelente propuesta. Sugiero cerrar con un registro gráfico para comunicar hallazgos."),
    ("educadora", "Cuentos que nos hacen sentir", "Muy útil para trabajar la regulación emocional después del recreo."),
]


def rut(cuerpo):
    return f"{cuerpo}-{calcular_digito_verificador(cuerpo)}"


def secciones_planificacion(datos):
    titulo, _, _, nivel, edad, nucleo, duracion, _, materiales, objetivo, descripcion, _ = datos
    return [
        ("Nivel y edad", f"{dict(Planificacion.Nivel.choices)[nivel]} · {dict(Planificacion.Edad.choices)[edad]}"),
        ("Núcleo de aprendizaje", nucleo),
        ("Objetivo de aprendizaje", objetivo or "Por definir."),
        ("Duración", f"{duracion} minutos"),
        ("Materiales", ", ".join(materiales) or "Sin materiales específicos."),
        ("Inicio", "Se invita al grupo a sentarse en semicírculo. Se presenta la experiencia mediante preguntas "
                   "que activan conocimientos previos y se acuerdan normas de convivencia."),
        ("Desarrollo", descripcion + " La educadora media con preguntas abiertas, acompaña y favorece la "
                       "participación de todos y todas, respetando sus ritmos."),
        ("Cierre", "Se comparte lo vivido: ¿qué descubrimos?, ¿qué nos gustó?, ¿qué haríamos distinto? "
                   "Se registran los aprendizajes en un papelógrafo."),
        ("Evaluación", "Observación directa con registro anecdótico y lista de cotejo de indicadores del objetivo."),
    ]


class Command(BaseCommand):
    help = "Carga usuarios, ideas pedagógicas, valoraciones y comentarios de demostración."

    def add_arguments(self, parser):
        parser.add_argument("--reiniciar", action="store_true", help="Borra los datos de demostración y los vuelve a crear.")

    def handle(self, *args, **opciones):
        clave = os.getenv("DEMO_PASSWORD", "")
        if len(clave) < 10:
            raise CommandError("Define DEMO_PASSWORD en el archivo .env (mínimo 10 caracteres).")

        demo = Usuario.objects.filter(email__endswith=DOMINIO)
        if demo.exists():
            if not opciones["reiniciar"]:
                self.stdout.write(self.style.WARNING("Los datos de demostración ya existen. Usa --reiniciar para recrearlos."))
                return
            self._eliminar(demo)

        with transaction.atomic():
            usuarios = self._crear_usuarios(clave)
            self._crear_solicitudes(usuarios)
            ideas = self._crear_ideas(usuarios)
            self._crear_interacciones(usuarios, ideas)

        self.stdout.write(self.style.SUCCESS("Datos de demostración cargados:"))
        for correo, nombres, apellidos, _, rol in USUARIOS:
            self.stdout.write(f"  {correo}{DOMINIO:<16} {rol.label}")
        self.stdout.write("  Contraseña: la definida en DEMO_PASSWORD (.env)")
        self.stdout.write(f"  Ideas creadas: {len(ideas)} ({Planificacion.objects.filter(estado=E.PUBLICADA).count()} publicadas)")

    # ------------------------------------------------------------------
    def _eliminar(self, demo):
        for p in Planificacion.objects.filter(colaborador__in=demo):
            if p.archivo:
                p.archivo.delete(save=False)
            p.delete()
        for s in SolicitudColaborador.objects.filter(usuario__in=demo):
            s.documento_respaldo.delete(save=False)
        demo.delete()
        self.stdout.write("Datos de demostración anteriores eliminados.")

    def _crear_usuarios(self, clave):
        usuarios = {}
        for correo, nombres, apellidos, cuerpo, rol in USUARIOS:
            usuarios[correo] = Usuario.objects.create_user(
                email=f"{correo}{DOMINIO}", password=clave, first_name=nombres, last_name=apellidos,
                rut=rut(cuerpo), rol=rol, fecha_nacimiento="1990-05-15",
            )
        return usuarios

    def _crear_solicitudes(self, usuarios):
        admin = usuarios["administradora"]
        for clave_usuario, estado in (("colaboradora", "APROBADA"), ("colaborador2", "APROBADA"), ("postulante", "PENDIENTE")):
            usuario = usuarios[clave_usuario]
            certificado = generar_pdf(
                "Certificado de título profesional (demostración)",
                [("Nombre", usuario.get_full_name()), ("RUT", usuario.rut),
                 ("Título", "Educador/a de Párvulos"), ("Institución", "Universidad de Demostración")],
            )
            solicitud = SolicitudColaborador(
                usuario=usuario, titulo_profesional="Educador/a de Párvulos",
                institucion="Universidad de Demostración", anio_titulacion=2016, estado=estado,
                nombre_archivo="certificado_titulo.pdf",
            )
            if estado == "APROBADA":
                solicitud.revisado_por = admin
                solicitud.fecha_resolucion = timezone.now()
            solicitud.documento_respaldo.save("certificado.pdf", ContentFile(certificado), save=False)
            solicitud.save()

    def _crear_ideas(self, usuarios):
        ahora = timezone.now()
        ideas = {}
        for indice, datos in enumerate(IDEAS):
            titulo, autor, estado, nivel, edad, nucleo, duracion, categorias, materiales, objetivo, descripcion, formato = datos
            p = Planificacion(
                colaborador=usuarios[autor], titulo=titulo, estado=estado, nivel_educativo=nivel,
                edad_recomendada=edad, nucleo=Nucleo.objects.get(nombre=nucleo), duracion_minutos=duracion,
                objetivo_aprendizaje=objetivo, descripcion=descripcion,
            )
            secciones = secciones_planificacion(datos)
            contenido = generar_pdf(titulo, secciones) if formato == "pdf" else generar_docx(titulo, secciones)
            p.archivo.save(f"planificacion.{formato}", ContentFile(contenido), save=False)
            p.nombre_archivo = f"{slugify(titulo)}.{formato}"
            p.tipo_archivo = formato
            p.tamano_archivo = len(contenido)
            if estado != E.BORRADOR:
                p.fecha_envio = ahora - timedelta(days=30 - indice)
            if estado == E.PUBLICADA:
                p.fecha_publicacion = ahora - timedelta(days=25 - indice)
                p.revisado_por = usuarios["administradora"]
            if estado == E.REQUIERE_CORRECCION:
                p.revisado_por = usuarios["administradora"]
                p.observacion_revision = "Por favor especifica el objetivo de aprendizaje según las Bases Curriculares y los resguardos de seguridad de la masa."
            p.save()
            p.categorias.set(Categoria.objects.filter(nombre__in=categorias))
            p.materiales.set(Material.objects.filter(nombre__in=materiales))
            ideas[titulo] = p
        return ideas

    def _crear_interacciones(self, usuarios, ideas):
        publicadas = [p for p in ideas.values() if p.estado == E.PUBLICADA]
        for indice, p in enumerate(publicadas):
            Valoracion.objects.create(usuario=usuarios["educadora"], planificacion=p, puntuacion=5 - (indice % 3))
            otro = "colaborador2" if p.colaborador == usuarios["colaboradora"] else "colaboradora"
            Valoracion.objects.create(usuario=usuarios[otro], planificacion=p, puntuacion=4 + (indice % 2))
        for p in publicadas[:3]:
            Favorito.objects.create(usuario=usuarios["educadora"], planificacion=p)
        for autor, titulo, texto in COMENTARIOS:
            Comentario.objects.create(usuario=usuarios[autor], planificacion=ideas[titulo], contenido=texto)
