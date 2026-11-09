# Idearia

**Ideas e inspiración para tus experiencias educativas.**

Idearia es una plataforma web para **Educación Parvularia**. Permite que Educadoras y Educadores de Párvulos busquen ideas pedagógicas organizadas y consulten planificaciones reales aportadas por profesionales acreditados. Un Administrador revisa cada aporte antes de publicarlo.

> Idearia **no genera ni reemplaza** la planificación del educador: es un repositorio de apoyo e inspiración.

Proyecto Integrado · Evaluación Sumativa N.º 3 · INACAP

**Aplicación publicada:** <https://idearia.onrender.com>. En el plan gratuito, la primera visita después de 15 minutos sin uso tarda cerca de un minuto en cargar.

---

## Contenido

1. [Funcionalidades por perfil](#funcionalidades-por-perfil)
2. [Tecnologías](#tecnologías)
3. [Requisitos](#requisitos)
4. [Instalación en Windows (PowerShell)](#instalación-en-windows-powershell)
5. [Conectar con Supabase (PostgreSQL)](#conectar-con-supabase-postgresql)
6. [Datos de demostración](#datos-de-demostración)
7. [Pruebas](#pruebas)
8. [Estructura del proyecto](#estructura-del-proyecto)
9. [Producción y HTTPS](#producción-y-https)
10. [Errores frecuentes](#errores-frecuentes)
11. [Documentación adicional](#documentación-adicional)

---

## Funcionalidades por perfil

| Perfil | Puede |
|---|---|
| **Educador/a de Párvulos** | Registrarse, iniciar y cerrar sesión, buscar ideas, filtrar (nivel, edad, ámbito, núcleo, objetivo de aprendizaje, duración, materiales, categoría), ver el detalle, ver la planificación dentro de Idearia (sin descarga), gestionar favoritos, valorar, comentar y solicitar acreditación como colaborador/a. |
| **Profesional Colaborador/a** | Todo lo anterior, más: crear propuestas, adjuntar la planificación (PDF o Word .docx), guardar borradores, enviar a revisión, consultar estados y observaciones, y corregir y reenviar cuando se le solicitan cambios. |
| **Administrador/a** | Panel general, revisión de solicitudes de colaboradores (aprobar o rechazar), revisión de propuestas (aprobar, rechazar, solicitar corrección, publicar, retirar), gestión de usuarios (activar y desactivar), moderación de comentarios y registro de acciones (auditoría). |

Los permisos se validan **en el servidor**. Por ejemplo, un Educador que escribe `/administracion/` en la barra de direcciones recibe un error 403.

## Tecnologías

| Componente | Tecnología |
|---|---|
| Lenguaje | Python 3.12 |
| Framework | Django 5.2 (ORM, Templates, autenticación, formularios) |
| Base de datos | PostgreSQL en **Supabase** (SQLite opcional para desarrollo local) |
| Conector | `psycopg[binary]` |
| Configuración | Variables de entorno en `.env` con `python-dotenv` |
| Frontend | Django Templates + HTML + CSS + JavaScript mínimo |
| Visor de documentos | PDF.js 3.11 (incluido en `static/vendor`) y `mammoth` (Word .docx → HTML) |
| Control de versiones | Git / GitHub |

## Requisitos

- **Python 3.12** ([python.org](https://www.python.org/downloads/) o `winget install -e --id Python.Python.3.12`)
- **Git**
- **Visual Studio Code** (recomendado)
- Una cuenta gratuita en **Supabase** (para la base de datos final)

Verifica la versión de Python:

```powershell
py -3.12 --version
```

## Instalación en Windows (PowerShell)

Ejecuta cada comando por separado en la terminal de VS Code (**Terminal > New Terminal**). No hace falta activar el entorno virtual: se usa su ejecutable directamente.

**1. Clonar el repositorio y entrar a la carpeta**

```powershell
git clone <URL_DEL_REPOSITORIO> idearia
cd idearia
```

**2. Crear el entorno virtual e instalar las dependencias**

```powershell
py -3.12 -m venv .venv
.\.venv\Scripts\python.exe -m pip install --upgrade pip
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
```

**3. Crear el archivo `.env`** (si ya existe, no lo sobrescribas)

```powershell
Copy-Item .env.example .env
```

Genera una clave secreta y pégala en `SECRET_KEY` dentro de `.env`:

```powershell
.\.venv\Scripts\python.exe -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())"
```

Define también `DEMO_PASSWORD` (mínimo 10 caracteres) si vas a cargar los datos de demostración.

**4. Crear las tablas y verificar**

```powershell
.\.venv\Scripts\python.exe manage.py makemigrations
.\.venv\Scripts\python.exe manage.py migrate
.\.venv\Scripts\python.exe manage.py check
```

`makemigrations` debería responder *No changes detected*, porque las migraciones ya vienen en el repositorio.

**5. Crear el superusuario (Administrador técnico)**

```powershell
.\.venv\Scripts\python.exe manage.py createsuperuser
```

Pide correo, nombres, apellidos, RUT (formato `12345678-9`) y contraseña. El superusuario queda con rol Administrador/a.

**6. Ejecutar el servidor**

```powershell
.\.venv\Scripts\python.exe manage.py runserver 8001
```

Abre <http://127.0.0.1:8001/>. Detén el servidor con `Ctrl+C`.

## Conectar con Supabase (PostgreSQL)

Solo cambia la sección `DATABASES` de `settings.py`, que lee estos valores desde `.env`. Los modelos, vistas y plantillas no se modifican.

**1. Crear el proyecto en Supabase**

1. Entra a <https://supabase.com> y crea una cuenta (GitHub o correo).
2. Crea una organización (plan Free) y un **proyecto nuevo**. Guarda en privado la **contraseña de la base de datos**.
3. En el proyecto, abre **Connect > Connection string > Session pooler**. Copia el host, el puerto, el nombre de la BD y el usuario.

**2. Editar `.env`** con tus datos (ejemplo ilustrativo):

```ini
DB_ENGINE="supabase"
DB_HOST="aws-0-REGION.pooler.supabase.com"
DB_PORT="5432"
DB_NAME="postgres"
DB_USER="postgres.ID_DEL_PROYECTO"
DB_PASSWORD="TU_CONTRASENA_DE_BD"
DB_SSLMODE="require"
```

- `DB_HOST` lleva solo el servidor, sin `postgresql://`.
- `DB_PASSWORD` es la contraseña de PostgreSQL, no la de tu cuenta de Supabase ni una API key.
- **Nunca subas `.env` a Git**: ya está excluido en `.gitignore`.

**3. Verificar la conexión** (resultado esperado: `Motor: postgresql`)

```powershell
.\.venv\Scripts\python.exe manage.py shell -c "from django.db import connection; connection.ensure_connection(); print('Motor:', connection.vendor); print('BD:', connection.settings_dict['NAME'])"
```

**4. Crear las tablas en Supabase y cargar datos**

```powershell
.\.venv\Scripts\python.exe manage.py migrate
.\.venv\Scripts\python.exe manage.py createsuperuser
.\.venv\Scripts\python.exe manage.py cargar_demo
.\.venv\Scripts\python.exe manage.py runserver 8001
```

**5. Comprobar en Supabase**

Para generar la evidencia de la conexión (motor, SSL, tablas y últimos usuarios) en `docs/evidencias/`:

```powershell
.\.venv\Scripts\python.exe manage.py verificar_bd --guardar
```


1. Registra un usuario **nuevo** desde Idearia (<http://127.0.0.1:8001/registro/>).
2. En Supabase abre **Table Editor > public > usuarios_usuario** y verifica que aparece la fila.
3. Revisa también `planificaciones_ambito` (3 filas) y `planificaciones_nucleo` (8 filas), que crea la migración de datos.

> Los registros que creaste en SQLite **no se copian** a Supabase. Las migraciones crean las tablas vacías, salvo los catálogos.

### Configuración usada en este proyecto (recomendada)

En vez de conectar Django con el usuario administrador `postgres`, Idearia usa un **usuario de base de datos propio**, `idearia_app`. Ese usuario solo puede crear y usar tablas en el esquema `public` (principio de mínimo privilegio). Para crearlo, abre **SQL Editor** en Supabase y ejecuta:

```sql
CREATE ROLE idearia_app LOGIN PASSWORD 'una-contraseña-larga-y-aleatoria';
GRANT CONNECT ON DATABASE postgres TO idearia_app;
GRANT USAGE, CREATE ON SCHEMA public TO idearia_app;
```

En `.env` usa `DB_USER="idearia_app.ID_DEL_PROYECTO"` y esa contraseña. El host y el puerto son los mismos del Session pooler.

Seguridad adicional:
- Las tablas creadas por `idearia_app` no otorgan permisos a los roles `anon` y `authenticated` de la API REST pública de Supabase.
- La migración `core/0002_activar_rls_postgresql` activa **Row Level Security** en todas las tablas. Nadie puede leerlas por la API de Supabase, y Django, como dueño de las tablas, no se ve afectado.

Rendimiento:
- Con el Session pooler, `settings.py` desactiva los cursores del lado del servidor (`DISABLE_SERVER_SIDE_CURSORS`).
- En producción, define `DB_CONN_MAX_AGE="60"` para reutilizar conexiones.
- Elige la región de Supabase más cercana al servidor de la aplicación (desde Chile: *South America, São Paulo*).

## Datos de demostración

```powershell
.\.venv\Scripts\python.exe manage.py cargar_demo
.\.venv\Scripts\python.exe manage.py cargar_demo --reiniciar
```

La segunda forma borra y recrea los datos de demostración. El comando crea 13 propuestas (9 publicadas y 4 en otros estados), valoraciones, comentarios, favoritos, solicitudes y estos usuarios ficticios (dominio reservado `.test`):

| Correo | Perfil |
|---|---|
| `administradora@idearia.test` | Administrador/a |
| `colaboradora@idearia.test` | Profesional Colaborador/a |
| `colaborador2@idearia.test` | Profesional Colaborador/a |
| `educadora@idearia.test` | Educador/a de Párvulos |
| `postulante@idearia.test` | Educador/a con una solicitud de acreditación pendiente |

La contraseña de todos es la que definiste en `DEMO_PASSWORD` dentro de `.env`; no está escrita en el código. Las planificaciones de demostración se generan automáticamente: son documentos de prueba, no planificaciones reales.

## Pruebas

**Pruebas automatizadas**: 102 pruebas que cubren 55 de los 60 casos del plan (funcionales, de seguridad, casos borde e integración).

```powershell
.\.venv\Scripts\python.exe manage.py test
.\.venv\Scripts\python.exe manage.py test --verbosity 2
```

Si tu `.env` apunta a Supabase, ejecuta las pruebas con SQLite. Django necesita crear una base temporal y el usuario `idearia_app` no tiene ese permiso:

```powershell
$env:DB_ENGINE="sqlite"; .\.venv\Scripts\python.exe manage.py test
```

La segunda forma muestra el detalle de cada caso. Las pruebas usan una base de datos temporal y una carpeta temporal para los archivos: no modifican tus datos.

**Prueba de carga** (con el servidor corriendo y los datos de demostración cargados):

```powershell
.\.venv\Scripts\python.exe scripts\prueba_carga.py --usuarios 10 --peticiones 20
.\.venv\Scripts\python.exe scripts\prueba_carga.py --usuarios 25 --peticiones 20
```

Los resultados se guardan en `docs/evidencias/` (CSV con el detalle y resumen en Markdown).

**Recorrido en navegador (opcional):** `scripts\recorrido_navegador.py` genera capturas de las pantallas con Microsoft Edge. Requiere `pip install playwright`, que no está en `requirements.txt`.

El plan de pruebas completo, con resultados y análisis, está en [docs/02_plan_de_pruebas.md](docs/02_plan_de_pruebas.md).

## Estructura del proyecto

```
idearia/
├── config/            Configuración (settings.py, urls.py)
├── core/              Inicio, panel admin, auditoría, validación de archivos, cabeceras de seguridad
├── usuarios/          Modelo Usuario (rol), registro, login, permisos por rol, gestión de usuarios
├── colaboradores/     Solicitudes de acreditación y su revisión
├── planificaciones/   Propuestas, catálogos, búsqueda, visor, flujo de revisión
├── interacciones/     Favoritos, valoraciones y comentarios
├── notificaciones/    Notificaciones internas
├── templates/         Plantillas HTML (base, errores 403/404/500 y una carpeta por app)
├── static/            CSS, JavaScript, íconos y PDF.js
├── scripts/           Prueba de carga y recorrido en navegador
├── docs/              Documentación, plan de pruebas y evidencias
├── media_protegida/   Archivos subidos (NO se sube a Git, sin URL pública)
├── .env.example       Plantilla de variables de entorno (sin credenciales)
└── requirements.txt
```

## Publicar en Render (producción)

Idearia está desplegada en **Render** (servidor de aplicación) y conectada a **Supabase** (base de datos y archivos). El archivo `render.yaml` define el servicio, en la región Oregón, junto a la base de datos.

1. Sube el código a GitHub (rama `main`).
2. En <https://dashboard.render.com> elige **New + > Blueprint** y selecciona el repositorio.
3. Completa `DB_USER` y `DB_PASSWORD` con los valores de tu `.env`. El resto viene en `render.yaml`, y `SECRET_KEY` la genera Render.
4. Presiona **Deploy Blueprint**. Render ejecuta `pip install`, `collectstatic` y `migrate`, e inicia `gunicorn`.
5. Cada `git push` a `main` vuelve a desplegar automáticamente.

Notas de producción:
- `whitenoise` sirve los estilos y el JavaScript.
- Los archivos subidos se guardan en la base de datos (`ALMACENAMIENTO_ARCHIVOS="bd"`), porque el disco gratuito de Render se borra al reiniciar.
- Las variables `RENDER_EXTERNAL_HOSTNAME` y `USAR_PROXY_HTTPS` configuran el dominio y HTTPS.

## Producción y HTTPS

Con `DEBUG="False"` en `.env` se activan automáticamente:

- redirección a HTTPS (`SECURE_SSL_REDIRECT`);
- cookies de sesión y CSRF solo por HTTPS (`*_COOKIE_SECURE`);
- HSTS por un año (`SECURE_HSTS_SECONDS`).

Además debes configurar:

- `ALLOWED_HOSTS` con el dominio;
- `CSRF_TRUSTED_ORIGINS` con `https://tu-dominio`;
- `USAR_PROXY_HTTPS="True"` si el hosting termina HTTPS en un proxy (Render, Railway, Nginx).

Verificación:

```powershell
.\.venv\Scripts\python.exe manage.py check --deploy
```

Para producción se recomienda un servidor WSGI como `waitress` o `gunicorn` en lugar de `runserver`, y servir los estáticos con `collectstatic`.

## Errores frecuentes

| Error | Causa y solución |
|---|---|
| `py -3.12` → *No suitable Python runtime found* | Python 3.12 no está instalado. Instálalo con `winget install -e --id Python.Python.3.12`. |
| `No module named django` | Usaste otro Python. Repite la instalación con `.\.venv\Scripts\python.exe -m pip install -r requirements.txt`. |
| `ImproperlyConfigured: Falta SECRET_KEY` | No existe `.env` o falta la clave. Ejecuta `Copy-Item .env.example .env` y genera una `SECRET_KEY`. |
| `faltan en .env: DB_HOST, DB_USER...` | `DB_ENGINE="supabase"` sin los datos de conexión. Completa los valores del Session pooler. |
| `password authentication failed` | `DB_USER` o `DB_PASSWORD` incorrectos. El usuario tiene la forma `postgres.ID_DEL_PROYECTO`. |
| Timeout o `could not translate host name` | Host mal copiado, sin internet o red que bloquea el puerto 5432. Revisa `DB_HOST` y prueba en otra red. |
| `relation ... does not exist` | No ejecutaste `migrate` en la base actual. |
| `Port is already in use` | Usa otro puerto: `runserver 8002`. |
| `permission denied to create database` al ejecutar pruebas | `.env` apunta a Supabase. Ejecuta las pruebas con `$env:DB_ENGINE="sqlite"` (ver [Pruebas](#pruebas)). |
| `Max client connections reached` (Supabase) | Usaste `DB_CONN_MAX_AGE` mayor que 0 con `runserver`, que abre una conexión por petición. Déjalo en `0` en desarrollo. |
| Páginas lentas con Supabase | La base está en otra región (cada consulta es un viaje de red). Usa la región más cercana y `DB_CONN_MAX_AGE="60"` en producción. |
| Ves `Motor: sqlite` en vez de `postgresql` | `DB_ENGINE` sigue en `"sqlite"` o `.env` no está en la carpeta de `manage.py`. |
| Errores de *acceso denegado* al instalar paquetes | OneDrive está sincronizando `.venv`. Pausa la sincronización mientras instalas o ubica el proyecto fuera de OneDrive. |
| Después de 5 intentos no puedo iniciar sesión | Bloqueo de seguridad temporal (15 minutos). Espera o reinicia el servidor en desarrollo. |
| La planificación no se muestra en el visor | El archivo no es un PDF o DOCX válido o se borró de `media_protegida/`. Vuelve a adjuntarlo. |

## Documentación adicional

- [docs/01_implementacion.md](docs/01_implementacion.md): arquitectura, modelos, seguridad y decisiones técnicas.
- [docs/02_plan_de_pruebas.md](docs/02_plan_de_pruebas.md): plan de pruebas, resultados, discrepancias y recomendaciones.
- [docs/pruebas/matriz_pruebas_E3.csv](docs/pruebas/matriz_pruebas_E3.csv): matriz completa de casos (todas las columnas).
- [docs/03_trazabilidad.md](docs/03_trazabilidad.md): requisitos ↔ implementación ↔ pruebas.
- [docs/04_preparacion_defensa.md](docs/04_preparacion_defensa.md): preguntas técnicas frecuentes.
