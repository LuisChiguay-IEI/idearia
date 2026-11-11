# Idearia

**Ideas e inspiración para tus experiencias educativas.**

Idearia es una plataforma web para **Educación Parvularia**. Permite que Educadoras y Educadores de Párvulos busquen ideas pedagógicas organizadas y consulten planificaciones reales aportadas por profesionales acreditados. Un Administrador revisa cada aporte antes de publicarlo.

> Idearia **no genera ni reemplaza** la planificación del educador: es un repositorio de apoyo e inspiración.

Proyecto Integrado · Evaluación Sumativa N.º 3 · INACAP  
**Autor:** Luis Chiguay

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
9. [Publicar en Render](#publicar-en-render-producción)
10. [Producción y HTTPS](#producción-y-https)
11. [Errores frecuentes](#errores-frecuentes)
12. [Autoría y uso académico](#autoría-y-uso-académico)

---

## Funcionalidades por perfil

| Perfil | Puede |
|---|---|
| **Educador/a de Párvulos** | Registrarse, iniciar y cerrar sesión, buscar ideas, filtrar por nivel, edad, ámbito, núcleo, objetivo de aprendizaje, duración, materiales y categoría, ver el detalle, visualizar la planificación dentro de Idearia sin descarga directa, gestionar favoritos, valorar, comentar y solicitar acreditación como colaborador/a. |
| **Profesional Colaborador/a** | Todo lo anterior, más: crear propuestas, adjuntar la planificación en PDF o Word `.docx`, guardar borradores, enviar a revisión, consultar estados y observaciones, corregir y reenviar cuando se soliciten cambios. |
| **Administrador/a** | Panel general, revisión de solicitudes de colaboradores, aprobación o rechazo de acreditaciones, revisión de propuestas, aprobación, rechazo, solicitud de corrección, publicación, retiro de contenido, gestión de usuarios, moderación de comentarios y registro de acciones de auditoría. |

Los permisos se validan **en el servidor**. Por ejemplo, un Educador que intenta ingresar manualmente a `/administracion/` recibe un error 403.

---

## Tecnologías

| Componente | Tecnología |
|---|---|
| Lenguaje | Python 3.12 |
| Framework | Django 5.2 (ORM, Templates, autenticación y formularios) |
| Base de datos | PostgreSQL en **Supabase** (SQLite opcional para desarrollo local) |
| Conector | `psycopg[binary]` |
| Configuración | Variables de entorno en `.env` con `python-dotenv` |
| Frontend | Django Templates + HTML + CSS + JavaScript mínimo |
| Visor de documentos | PDF.js 3.11 incluido en `static/vendor` y `mammoth` para convertir Word `.docx` → HTML |
| Control de versiones | Git / GitHub |

---

## Requisitos

- **Python 3.12**
- **Git**
- **Visual Studio Code** recomendado
- Una cuenta gratuita en **Supabase** para la base de datos final

Verifica la versión de Python:

```powershell
py -3.12 --version
```

---

## Instalación en Windows (PowerShell)

Ejecuta cada comando por separado en la terminal de VS Code (**Terminal > New Terminal**).

No hace falta activar manualmente el entorno virtual, ya que se utiliza directamente su ejecutable.

### 1. Clonar el repositorio y entrar a la carpeta

```powershell
git clone <URL_DEL_REPOSITORIO> idearia
cd idearia
```

### 2. Crear el entorno virtual e instalar las dependencias

```powershell
py -3.12 -m venv .venv
.\.venv\Scripts\python.exe -m pip install --upgrade pip
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
```

### 3. Crear el archivo `.env`

Si ya existe, no lo sobrescribas.

```powershell
Copy-Item .env.example .env
```

Genera una clave secreta y pégala en `SECRET_KEY` dentro de `.env`:

```powershell
.\.venv\Scripts\python.exe -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())"
```

Define también `DEMO_PASSWORD` con un mínimo de 10 caracteres si vas a cargar los datos de demostración.

### 4. Crear las tablas y verificar

```powershell
.\.venv\Scripts\python.exe manage.py makemigrations
.\.venv\Scripts\python.exe manage.py migrate
.\.venv\Scripts\python.exe manage.py check
```

`makemigrations` debería responder `No changes detected`, porque las migraciones ya vienen incluidas en el repositorio.

### 5. Crear el superusuario

```powershell
.\.venv\Scripts\python.exe manage.py createsuperuser
```

Solicita correo, nombres, apellidos, RUT en formato `12345678-9` y contraseña.

El superusuario queda configurado con rol de Administrador/a.

### 6. Ejecutar el servidor

```powershell
.\.venv\Scripts\python.exe manage.py runserver 8001
```

Abre:

<http://127.0.0.1:8001/>

Para detener el servidor utiliza:

```text
Ctrl + C
```

---

## Conectar con Supabase (PostgreSQL)

Idearia utiliza PostgreSQL mediante Supabase.

La configuración de `DATABASES` en `settings.py` obtiene los valores mediante variables de entorno almacenadas en `.env`.

Los modelos, vistas y plantillas no necesitan modificarse para cambiar entre SQLite y PostgreSQL si utilizan correctamente el ORM de Django.

### 1. Crear el proyecto en Supabase

1. Entra a <https://supabase.com>.
2. Crea una cuenta con GitHub o correo electrónico.
3. Crea una organización utilizando el plan Free.
4. Crea un proyecto nuevo.
5. Guarda de forma privada la contraseña de la base de datos.
6. En el proyecto abre **Connect > Connection string > Session pooler**.
7. Copia el host, puerto, nombre de la base de datos y usuario.

### 2. Editar `.env`

Ejemplo ilustrativo:

```ini
DB_ENGINE="supabase"
DB_HOST="aws-0-REGION.pooler.supabase.com"
DB_PORT="5432"
DB_NAME="postgres"
DB_USER="postgres.ID_DEL_PROYECTO"
DB_PASSWORD="TU_CONTRASENA_DE_BD"
DB_SSLMODE="require"
```

Consideraciones:

- `DB_HOST` lleva solamente el servidor, sin `postgresql://`.
- `DB_PASSWORD` corresponde a la contraseña de PostgreSQL.
- No corresponde a la contraseña de la cuenta de Supabase ni a una API Key.
- **Nunca subas `.env` a Git**. Este archivo ya está excluido mediante `.gitignore`.

### 3. Verificar la conexión

Resultado esperado:

```text
Motor: postgresql
```

Comando:

```powershell
.\.venv\Scripts\python.exe manage.py shell -c "from django.db import connection; connection.ensure_connection(); print('Motor:', connection.vendor); print('BD:', connection.settings_dict['NAME'])"
```

### 4. Crear las tablas en Supabase y cargar datos

```powershell
.\.venv\Scripts\python.exe manage.py migrate
.\.venv\Scripts\python.exe manage.py createsuperuser
.\.venv\Scripts\python.exe manage.py cargar_demo
.\.venv\Scripts\python.exe manage.py runserver 8001
```

### 5. Comprobar en Supabase

Para verificar el estado de la conexión, motor, SSL, migraciones pendientes, tablas y últimos usuarios:

```powershell
.\.venv\Scripts\python.exe manage.py verificar_bd
```

También se puede guardar el resultado en un archivo:

```powershell
.\.venv\Scripts\python.exe manage.py verificar_bd --guardar CARPETA
```

Para comprobar manualmente:

1. Registra un usuario nuevo desde Idearia en:

   <http://127.0.0.1:8001/registro/>

2. En Supabase abre:

   **Table Editor > public > usuarios_usuario**

3. Comprueba que aparece el nuevo registro.

4. Revisa también:

   - `planificaciones_ambito`
   - `planificaciones_nucleo`

Los registros creados previamente utilizando SQLite **no se copian automáticamente a Supabase**.

Las migraciones crean las tablas correspondientes, junto con los catálogos configurados mediante migraciones de datos.

---

### Configuración utilizada en este proyecto

En lugar de conectar Django directamente utilizando el usuario administrador `postgres`, Idearia puede utilizar un usuario propio de base de datos llamado:

```text
idearia_app
```

Este usuario aplica el principio de **mínimo privilegio**.

Ejemplo de configuración mediante SQL Editor de Supabase:

```sql
CREATE ROLE idearia_app LOGIN PASSWORD 'una-contraseña-larga-y-aleatoria';

GRANT CONNECT ON DATABASE postgres TO idearia_app;

GRANT USAGE, CREATE ON SCHEMA public TO idearia_app;
```

Luego en `.env` se utiliza:

```ini
DB_USER="idearia_app.ID_DEL_PROYECTO"
```

junto con la contraseña correspondiente.

El host y puerto son los mismos utilizados por el Session Pooler.

### Seguridad adicional

- Las tablas creadas por `idearia_app` no otorgan permisos directos a los roles públicos `anon` y `authenticated` de Supabase.
- La migración `core/0002_activar_rls_postgresql` activa **Row Level Security** en las tablas correspondientes.
- Django se conecta utilizando su usuario autorizado de base de datos.

### Rendimiento

- Con Session Pooler, `settings.py` desactiva los cursores del lado del servidor mediante `DISABLE_SERVER_SIDE_CURSORS`.
- En producción puede definirse:

```ini
DB_CONN_MAX_AGE="60"
```

para reutilizar conexiones.

- Se recomienda elegir una región de Supabase cercana al servidor donde se ejecuta la aplicación.

---

## Datos de demostración

Para cargar datos de prueba:

```powershell
.\.venv\Scripts\python.exe manage.py cargar_demo
```

Para borrar y regenerar los datos:

```powershell
.\.venv\Scripts\python.exe manage.py cargar_demo --reiniciar
```

El comando crea propuestas en distintos estados, valoraciones, comentarios, favoritos y solicitudes.

Usuarios ficticios de demostración:

| Correo | Perfil |
|---|---|
| `administradora@idearia.test` | Administrador/a |
| `colaboradora@idearia.test` | Profesional Colaborador/a |
| `colaborador2@idearia.test` | Profesional Colaborador/a |
| `educadora@idearia.test` | Educador/a de Párvulos |
| `postulante@idearia.test` | Educador/a con solicitud de acreditación pendiente |

La contraseña utilizada corresponde al valor configurado en:

```text
DEMO_PASSWORD
```

dentro del archivo `.env`.

La contraseña **no está escrita directamente en el código**.

Las planificaciones de demostración se generan automáticamente y corresponden a documentos utilizados únicamente para pruebas.

---

## Pruebas

Idearia cuenta con pruebas automatizadas funcionales, de seguridad, integración y casos borde.

Actualmente existen:

**102 pruebas automatizadas que cubren 55 de los 60 casos definidos en el plan de pruebas.**

Ejecutar todas las pruebas:

```powershell
.\.venv\Scripts\python.exe manage.py test
```

Ejecutar mostrando mayor detalle:

```powershell
.\.venv\Scripts\python.exe manage.py test --verbosity 2
```

Si `.env` apunta a Supabase, las pruebas deben ejecutarse utilizando SQLite:

```powershell
$env:DB_ENGINE="sqlite"; .\.venv\Scripts\python.exe manage.py test
```

Django utiliza una base de datos temporal y una carpeta temporal para los archivos durante las pruebas.

Esto evita modificar los datos reales almacenados en Supabase.

---

## Estructura del proyecto

```text
idearia/
├── config/              Configuración general (settings.py, urls.py)
├── core/                Inicio, panel admin, auditoría, validación de archivos y seguridad
├── usuarios/            Modelo Usuario, registro, login, roles y gestión de usuarios
├── colaboradores/       Solicitudes de acreditación y revisión
├── planificaciones/     Propuestas, catálogos, búsqueda, visor y flujo de revisión
├── interacciones/       Favoritos, valoraciones y comentarios
├── notificaciones/      Notificaciones internas
├── templates/           Plantillas HTML y páginas de error
├── static/              CSS, JavaScript, íconos y PDF.js
├── media_protegida/     Archivos utilizados durante desarrollo local
├── .env.example         Plantilla de variables de entorno sin credenciales
├── render.yaml          Configuración de despliegue en Render
└── requirements.txt     Dependencias de Python
```

---

## Publicar en Render (producción)

Idearia se encuentra desplegada utilizando:

- **Render** como servidor de aplicación.
- **Supabase** como base de datos PostgreSQL y almacenamiento asociado.

El archivo:

```text
render.yaml
```

contiene la configuración necesaria para el despliegue.

### Flujo de despliegue

1. Subir el código a GitHub en la rama `main`.
2. En <https://dashboard.render.com> seleccionar **New + > Blueprint**.
3. Seleccionar el repositorio de Idearia.
4. Configurar las variables necesarias de entorno.
5. Ejecutar **Deploy Blueprint**.

Render ejecuta automáticamente procesos como:

```text
pip install
collectstatic
migrate
gunicorn
```

Cada:

```powershell
git push
```

realizado sobre `main` puede generar automáticamente un nuevo despliegue.

### Consideraciones de producción

- `whitenoise` sirve los archivos estáticos.
- Los documentos subidos se almacenan de forma persistente según la configuración de producción.
- El disco gratuito de Render no debe utilizarse como almacenamiento permanente de documentos.
- `RENDER_EXTERNAL_HOSTNAME` y `USAR_PROXY_HTTPS` permiten configurar correctamente dominio y HTTPS.

---

## Producción y HTTPS

Cuando:

```ini
DEBUG="False"
```

se activan configuraciones de seguridad para producción.

Entre ellas:

- redirección a HTTPS mediante `SECURE_SSL_REDIRECT`;
- cookies de sesión seguras;
- cookies CSRF seguras;
- HSTS mediante `SECURE_HSTS_SECONDS`.

También deben configurarse:

```text
ALLOWED_HOSTS
CSRF_TRUSTED_ORIGINS
USAR_PROXY_HTTPS
```

Para verificar la configuración:

```powershell
.\.venv\Scripts\python.exe manage.py check --deploy
```

En producción se utiliza un servidor WSGI como `gunicorn` en lugar de `runserver`.

---

## Errores frecuentes

| Error | Causa y solución |
|---|---|
| `py -3.12` → `No suitable Python runtime found` | Python 3.12 no está instalado. Instálalo antes de continuar. |
| `No module named django` | Se está utilizando otro Python. Repite la instalación utilizando `.\.venv\Scripts\python.exe`. |
| `ImproperlyConfigured: Falta SECRET_KEY` | No existe `.env` o falta la clave. Crea `.env` desde `.env.example` y genera una `SECRET_KEY`. |
| Faltan `DB_HOST`, `DB_USER`, etc. | `DB_ENGINE="supabase"` está configurado sin los datos de conexión completos. |
| `password authentication failed` | Revisa `DB_USER` y `DB_PASSWORD`. |
| Timeout o `could not translate host name` | Revisa `DB_HOST`, conexión a internet y puerto. |
| `relation ... does not exist` | Ejecuta `migrate` en la base de datos correspondiente. |
| `Port is already in use` | Utiliza otro puerto, por ejemplo `runserver 8002`. |
| `permission denied to create database` durante pruebas | Ejecuta las pruebas utilizando SQLite. |
| `Max client connections reached` | Revisa la configuración de conexiones de Supabase. |
| Páginas lentas con Supabase | Utiliza una región cercana y conexiones persistentes en producción. |
| `Motor: sqlite` en vez de `postgresql` | Revisa `DB_ENGINE` y la ubicación de `.env`. |
| Error de acceso al instalar paquetes | Revisa permisos o sincronización de OneDrive. |
| Después de 5 intentos no puedo iniciar sesión | Existe un bloqueo temporal de seguridad de 15 minutos. |
| La planificación no aparece en el visor | Comprueba que el PDF o DOCX sea válido y que el archivo exista en el almacenamiento configurado. |

---

## Autoría y uso académico

**Idearia** es un proyecto académico desarrollado por **Luis Chiguay** para la asignatura Proyecto Integrado de Ingeniería en Informática – INACAP.

Copyright © 2026 Luis Chiguay. Todos los derechos reservados.

El código fuente, documentación, diseño, estructura y demás contenidos de este repositorio se publican con fines de evaluación académica y revisión del proyecto.

No se autoriza su reproducción, redistribución, publicación como trabajo propio ni reutilización total o parcial en otras entregas académicas sin autorización expresa del autor.
