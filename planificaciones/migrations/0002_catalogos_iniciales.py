"""
Migración de datos: carga los catálogos que usan los filtros de búsqueda.

Ámbitos y núcleos según las Bases Curriculares de Educación Parvularia (2018).
Al ejecutar "migrate" en Supabase, estos registros quedan creados automáticamente.
"""

from django.db import migrations

AMBITOS = [
    (
        1,
        "Desarrollo Personal y Social",
        "corazon",
        ["Identidad y Autonomía", "Convivencia y Ciudadanía", "Corporalidad y Movimiento"],
    ),
    (2, "Comunicación Integral", "libro", ["Lenguaje Verbal", "Lenguajes Artísticos"]),
    (
        3,
        "Interacción y Comprensión del Entorno",
        "hoja",
        [
            "Exploración del Entorno Natural",
            "Comprensión del Entorno Sociocultural",
            "Pensamiento Matemático",
        ],
    ),
]

CATEGORIAS = [
    "Arte y creatividad",
    "Cuidado del medioambiente",
    "Emociones y convivencia",
    "Exploración y naturaleza",
    "Juego y movimiento",
    "Lenguaje y cuentos",
    "Música y ritmo",
    "Pensamiento matemático",
    "Sensorial",
    "Vida saludable",
]

MATERIALES = [
    "Alimentos para preparar",
    "Bloques o material de construcción",
    "Cuentos e imágenes",
    "Elementos naturales (hojas, piedras, ramas)",
    "Esponjas y pinceles",
    "Instrumentos musicales",
    "Lápices de colores",
    "Lupas",
    "Masa o plasticina",
    "Material reciclado",
    "Papel y cartulina",
    "Pelotas y aros",
    "Pinturas",
    "Recipientes y bandejas",
    "Reproductor de música",
    "Telas y pañuelos",
]


def cargar_catalogos(apps, schema_editor):
    Ambito = apps.get_model("planificaciones", "Ambito")
    Nucleo = apps.get_model("planificaciones", "Nucleo")
    Categoria = apps.get_model("planificaciones", "Categoria")
    Material = apps.get_model("planificaciones", "Material")

    for orden, nombre, icono, nucleos in AMBITOS:
        ambito, _ = Ambito.objects.get_or_create(
            nombre=nombre, defaults={"orden": orden, "icono": icono}
        )
        for nombre_nucleo in nucleos:
            Nucleo.objects.get_or_create(ambito=ambito, nombre=nombre_nucleo)
    for nombre in CATEGORIAS:
        Categoria.objects.get_or_create(nombre=nombre)
    for nombre in MATERIALES:
        Material.objects.get_or_create(nombre=nombre)


def eliminar_catalogos(apps, schema_editor):
    apps.get_model("planificaciones", "Nucleo").objects.all().delete()
    apps.get_model("planificaciones", "Ambito").objects.all().delete()
    apps.get_model("planificaciones", "Categoria").objects.all().delete()
    apps.get_model("planificaciones", "Material").objects.all().delete()


class Migration(migrations.Migration):
    dependencies = [("planificaciones", "0001_initial")]

    operations = [migrations.RunPython(cargar_catalogos, eliminar_catalogos)]
