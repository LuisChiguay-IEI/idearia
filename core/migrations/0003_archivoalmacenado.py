from django.db import migrations, models


def activar_rls(apps, schema_editor):
    """En PostgreSQL (Supabase), la nueva tabla también queda con Row Level Security."""
    if schema_editor.connection.vendor == "postgresql":
        with schema_editor.connection.cursor() as cursor:
            cursor.execute('ALTER TABLE "core_archivoalmacenado" ENABLE ROW LEVEL SECURITY')


class Migration(migrations.Migration):
    dependencies = [("core", "0002_activar_rls_postgresql")]

    operations = [
        migrations.CreateModel(
            name="ArchivoAlmacenado",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("nombre", models.CharField(max_length=255, unique=True)),
                ("contenido", models.BinaryField()),
                ("tamano", models.PositiveIntegerField()),
                ("fecha", models.DateTimeField(auto_now_add=True)),
            ],
            options={"verbose_name": "archivo almacenado", "verbose_name_plural": "archivos almacenados"},
        ),
        migrations.RunPython(activar_rls, migrations.RunPython.noop),
    ]
