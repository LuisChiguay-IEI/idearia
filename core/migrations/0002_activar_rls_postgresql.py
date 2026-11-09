"""
Activa Row Level Security (RLS) en las tablas de Idearia cuando la base es PostgreSQL (Supabase).

¿Por qué? Supabase publica automáticamente una API REST sobre el esquema "public".
Con RLS activado y sin políticas, nadie puede leer ni modificar las tablas por esa vía.
Django no se ve afectado: se conecta con el rol dueño de las tablas (idearia_app),
y el dueño no está sujeto a RLS.

En SQLite (desarrollo) esta migración no hace nada.
"""

from django.db import migrations


def activar_rls(apps, schema_editor):
    if schema_editor.connection.vendor != "postgresql":
        return
    with schema_editor.connection.cursor() as cursor:
        cursor.execute(
            "SELECT tablename FROM pg_tables WHERE schemaname = current_schema() AND tableowner = current_user"
        )
        for (tabla,) in cursor.fetchall():
            cursor.execute(f'ALTER TABLE "{tabla}" ENABLE ROW LEVEL SECURITY')


def desactivar_rls(apps, schema_editor):
    if schema_editor.connection.vendor != "postgresql":
        return
    with schema_editor.connection.cursor() as cursor:
        cursor.execute(
            "SELECT tablename FROM pg_tables WHERE schemaname = current_schema() AND tableowner = current_user"
        )
        for (tabla,) in cursor.fetchall():
            cursor.execute(f'ALTER TABLE "{tabla}" DISABLE ROW LEVEL SECURITY')


class Migration(migrations.Migration):
    # Se ejecuta después de que existen todas las tablas del proyecto
    dependencies = [
        ("core", "0001_initial"),
        ("usuarios", "0001_initial"),
        ("colaboradores", "0001_initial"),
        ("planificaciones", "0002_catalogos_iniciales"),
        ("interacciones", "0001_initial"),
        ("notificaciones", "0001_initial"),
        ("admin", "0003_logentry_add_action_flag_choices"),
        ("auth", "0012_alter_user_first_name_max_length"),
        ("contenttypes", "0002_remove_content_type_name"),
        ("sessions", "0001_initial"),
    ]

    operations = [migrations.RunPython(activar_rls, desactivar_rls)]
