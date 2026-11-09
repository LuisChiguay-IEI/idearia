"""
Verifica la conexión de Django con la base de datos y, opcionalmente, guarda la evidencia.

Uso:
    .\\.venv\\Scripts\\python.exe manage.py verificar_bd
    .\\.venv\\Scripts\\python.exe manage.py verificar_bd --guardar C:\\ruta\\a\\una\\carpeta

Con --guardar crea verificacion_bd_<motor>_<fecha>.txt en la carpeta indicada
(o en la carpeta actual). Nunca muestra usuario ni contraseña de la BD.
"""

from datetime import datetime
from pathlib import Path

from django.core.management.base import BaseCommand
from django.db import connection
from django.db.migrations.executor import MigrationExecutor
from django.utils import timezone

from colaboradores.models import SolicitudColaborador
from core.models import RegistroAccion
from interacciones.models import Comentario, Favorito, Valoracion
from notificaciones.models import Notificacion
from planificaciones.models import Ambito, Nucleo, Planificacion
from usuarios.models import Usuario


class Command(BaseCommand):
    help = "Muestra el motor de BD, el estado de las migraciones y los registros de Idearia."

    def add_arguments(self, parser):
        parser.add_argument(
            "--guardar", nargs="?", const=".", metavar="CARPETA",
            help="Guarda el resultado en un archivo de texto (por defecto, en la carpeta actual)",
        )

    def handle(self, *args, **opciones):
        connection.ensure_connection()
        config = connection.settings_dict
        lineas = [
            "Verificación de base de datos · Idearia",
            f"Fecha: {datetime.now():%Y-%m-%d %H:%M:%S}",
            "",
            f"Motor (connection.vendor): {connection.vendor}",
            f"Servidor: {config.get('HOST') or 'archivo local'}",
            f"Base de datos: {config['NAME']}",
        ]
        if connection.vendor == "postgresql":
            conexion = connection.connection
            lineas.append(f"Versión de PostgreSQL: {conexion.info.server_version}")
            lineas.append(f"Conexión cifrada (SSL): {'sí' if conexion.pgconn.ssl_in_use else 'no'}")

        ejecutor = MigrationExecutor(connection)
        pendientes = ejecutor.migration_plan(ejecutor.loader.graph.leaf_nodes())
        lineas.append(f"Migraciones pendientes: {len(pendientes)}")

        lineas += ["", "Registros por tabla:"]
        conteos = [
            ("usuarios_usuario", Usuario.objects.count()),
            ("colaboradores_solicitudcolaborador", SolicitudColaborador.objects.count()),
            ("planificaciones_planificacion", Planificacion.objects.count()),
            ("  · publicadas", Planificacion.objects.filter(estado=Planificacion.Estado.PUBLICADA).count()),
            ("planificaciones_ambito", Ambito.objects.count()),
            ("planificaciones_nucleo", Nucleo.objects.count()),
            ("interacciones_favorito", Favorito.objects.count()),
            ("interacciones_valoracion", Valoracion.objects.count()),
            ("interacciones_comentario", Comentario.objects.count()),
            ("notificaciones_notificacion", Notificacion.objects.count()),
            ("core_registroaccion", RegistroAccion.objects.count()),
        ]
        lineas += [f"  {tabla:<38} {total}" for tabla, total in conteos]

        lineas += ["", "Últimos usuarios registrados (para comparar con el Table Editor de Supabase):"]
        for usuario in Usuario.objects.order_by("-date_joined")[:5]:
            fecha = timezone.localtime(usuario.date_joined)  # hora de Chile (TIME_ZONE)
            lineas.append(f"  {fecha:%Y-%m-%d %H:%M}  {usuario.email:<34} {usuario.get_rol_display()}")

        texto = "\n".join(lineas)
        self.stdout.write(texto)

        if opciones["guardar"]:
            carpeta = Path(opciones["guardar"])
            carpeta.mkdir(parents=True, exist_ok=True)
            archivo = carpeta / f"verificacion_bd_{connection.vendor}_{datetime.now():%Y%m%d_%H%M%S}.txt"
            archivo.write_text(texto + "\n", encoding="utf-8")
            self.stdout.write(self.style.SUCCESS(f"\nEvidencia guardada en {archivo}"))
