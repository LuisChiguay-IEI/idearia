from django.db import migrations, models

import planificaciones.models


class Migration(migrations.Migration):

    dependencies = [
        (
            "planificaciones",
            "0002_catalogos_iniciales",
        ),
    ]

    operations = [

        migrations.AddField(
            model_name="planificacion",
            name="imagen_portada",
            field=models.FileField(
                blank=True,
                max_length=255,
                upload_to=planificaciones.models.ruta_imagen_portada,
                verbose_name="imagen de portada",
            ),
        ),

        migrations.AddField(
            model_name="planificacion",
            name="nombre_imagen",
            field=models.CharField(
                blank=True,
                max_length=200,
                verbose_name="nombre original de la imagen",
            ),
        ),

        migrations.AddField(
            model_name="planificacion",
            name="tipo_imagen",
            field=models.CharField(
                blank=True,
                max_length=20,
                verbose_name="tipo de imagen",
            ),
        ),

        migrations.AddField(
            model_name="planificacion",
            name="tamano_imagen",
            field=models.PositiveIntegerField(
                blank=True,
                null=True,
                verbose_name="tamaño de imagen (bytes)",
            ),
        ),

    ]