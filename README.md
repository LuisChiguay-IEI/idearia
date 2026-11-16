# Idearia

**Ideas e inspiración para tus experiencias educativas.**

Idearia es una plataforma web orientada a **Educación Parvularia**, desarrollada como parte del proyecto académico de la asignatura Proyecto Integrado de Ingeniería en Informática – INACAP.

La plataforma permite que Educadoras y Educadores de Párvulos encuentren ideas pedagógicas organizadas y consulten planificaciones aportadas por profesionales previamente acreditados.

> Idearia no genera ni reemplaza la planificación del educador. Su objetivo es funcionar como una herramienta de apoyo e inspiración para experiencias educativas.

**Proyecto Integrado · Evaluación Sumativa N.º 3 · INACAP**  
**Autor:** Luis Chiguay

**Aplicación publicada:**  
https://idearia.onrender.com

> Debido al uso del plan gratuito de Render, la primera carga puede tardar algunos segundos si el servicio se encuentra inactivo.

---

## Objetivo del proyecto

Idearia busca centralizar ideas y recursos pedagógicos relacionados con Educación Parvularia en una plataforma organizada, permitiendo consultar contenido mediante filtros y visualizar planificaciones asociadas.

El proyecto considera tres perfiles principales:

- Educador/a de Párvulos.
- Profesional Colaborador/a.
- Administrador/a.

Cada perfil dispone de permisos y funcionalidades diferentes según su responsabilidad dentro de la plataforma.

---

## Funcionalidades principales

### Educador/a de Párvulos

Puede:

- registrarse e iniciar sesión.
- buscar ideas pedagógicas.
- utilizar filtros de búsqueda.
- consultar el detalle de una propuesta.
- visualizar la planificación asociada.
- guardar favoritos.
- valorar contenido.
- realizar comentarios.
- solicitar acreditación como Profesional Colaborador/a.

### Profesional Colaborador/a

Puede:

- registrar propuestas pedagógicas.
- adjuntar una planificación en formato permitido.
- guardar propuestas como borrador.
- enviarlas a revisión.
- consultar su estado.
- recibir observaciones.
- corregir y reenviar propuestas.

### Administrador/a

Puede:

- revisar solicitudes de acreditación.
- aprobar o rechazar colaboradores.
- revisar propuestas pedagógicas.
- aprobar, rechazar o solicitar correcciones.
- publicar o retirar contenido.
- gestionar usuarios.
- moderar comentarios.
- consultar registros de auditoría.

Los permisos son validados desde el servidor y no dependen únicamente de la interfaz.

---

## Tecnologías utilizadas

| Componente | Tecnología |
|---|---|
| Lenguaje | Python 3.12 |
| Framework | Django 5.2 |
| Base de datos | PostgreSQL |
| Servicio de base de datos | Supabase PostgreSQL |
| Almacenamiento de objetos | Supabase Storage |
| ORM | Django ORM |
| Frontend | Django Templates, HTML, CSS y JavaScript |
| Autenticación | Django Authentication |
| Visor de documentos | PDF.js y Mammoth |
| Servidor de producción | Gunicorn |
| Archivos estáticos | WhiteNoise |
| Despliegue | Render |
| Control de versiones | Git / GitHub |

---

## Estructura general

```text
idearia/
├── config/              Configuración general del proyecto
├── core/                Funciones centrales, seguridad y auditoría
├── usuarios/            Usuarios, autenticación, perfiles y permisos
├── colaboradores/       Solicitudes y acreditación profesional
├── planificaciones/     Propuestas pedagógicas y flujo de revisión
├── interacciones/       Favoritos, valoraciones y comentarios
├── notificaciones/      Notificaciones internas
├── templates/           Interfaces HTML
├── static/              CSS, JavaScript, íconos y recursos
├── .env.example         Referencia de variables de entorno
├── render.yaml          Configuración de despliegue
└── requirements.txt     Dependencias del proyecto
```

---

## Datos y almacenamiento

Idearia utiliza **PostgreSQL mediante Supabase** para la información estructurada y relacional del sistema.

La estructura contempla, entre otras, información relacionada con:

- usuarios.
- solicitudes de colaboradores.
- propuestas pedagógicas.
- planificaciones.
- categorías.
- comentarios.
- valoraciones.
- favoritos.
- notificaciones.
- registros de auditoría.

La conexión utiliza variables de entorno para evitar almacenar credenciales directamente en el código.

Las imágenes de portada nuevas pueden almacenarse en un **bucket privado de Supabase Storage**, mientras que PostgreSQL conserva las referencias y los datos de negocio. Los documentos pedagógicos continúan protegidos por el backend de Idearia.

El archivo `.env` utilizado en desarrollo y producción **no forma parte del repositorio**.

---

## Ejecución local

Requisitos:

- Python 3.12 o superior.
- pip.
- Git.

Pasos mínimos:

```bash
python -m venv .venv
pip install -r requirements.txt
```

Luego se crea un archivo `.env` a partir de `.env.example` y se completan únicamente las variables correspondientes al entorno utilizado.

Para preparar y ejecutar la aplicación:

```bash
python manage.py migrate
python manage.py runserver
```

Las credenciales reales de Supabase y las claves secretas no deben almacenarse en el repositorio.

---

## Seguridad

Durante el desarrollo se incorporaron distintos controles de seguridad.

Entre ellos:

- autenticación mediante Django.
- almacenamiento seguro de contraseñas.
- control de acceso basado en roles.
- validación de permisos desde el servidor.
- protección CSRF.
- validación de formularios.
- validación de archivos.
- manejo controlado de documentos.
- variables de entorno para información sensible.
- HTTPS en producción.
- cookies seguras.
- protección frente a múltiples intentos fallidos de autenticación.
- registro de operaciones administrativas.
- restricciones de acceso a la base de datos.

El sistema también utiliza medidas de seguridad adicionales en PostgreSQL y Supabase para limitar el acceso directo a la información.

---

## Planificaciones

Las planificaciones pedagógicas son documentos aportados por Profesionales Colaboradores.

Los formatos considerados por la plataforma son principalmente:

- PDF.
- DOCX.

Los documentos pueden visualizarse dentro de Idearia mediante un visor integrado.

La plataforma no presenta una opción directa de descarga para estos documentos.

---

## Flujo de publicación

Una propuesta pedagógica no se publica automáticamente.

El flujo principal corresponde a:

```text
Borrador
   ↓
En revisión
   ├── Aprobar y publicar → Publicada
   ├── Solicitar corrección → Requiere corrección
   └── Rechazar → Rechazada
```

El estado `Aprobada` se conserva únicamente por compatibilidad con registros anteriores. En el flujo actual, una propuesta nueva que es aprobada por el Administrador se publica directamente en el catálogo.

---

## Acreditación de Profesionales Colaboradores

Para solicitar el perfil de Profesional Colaborador se deben registrar antecedentes profesionales y documentación de respaldo.

La solicitud pasa por un proceso de revisión administrativa antes de habilitar las funciones correspondientes.

Estados considerados:

```text
Pendiente
   ↓
En revisión
   ↓
Aprobada / Rechazada
```

---

## Pruebas

Idearia cuenta con un plan de pruebas que considera:

- pruebas funcionales.
- seguridad.
- integración.
- casos borde.
- validación de roles y permisos.
- archivos.
- autenticación.
- interacción con la base de datos.
- rendimiento.
- usabilidad.

También se desarrollaron pruebas automatizadas mediante las herramientas de testing de Django.

Los resultados obtenidos se utilizan para comparar el comportamiento esperado con el comportamiento real de la aplicación y detectar posibles mejoras.

---

## Despliegue

La solución se encuentra desplegada utilizando:

**Render**  
Servidor de aplicación Django.

**Supabase**  
Base de datos PostgreSQL y almacenamiento privado de objetos.

**GitHub**  
Repositorio y control de versiones.

El despliegue se encuentra conectado con la rama principal del repositorio para mantener actualizada la versión publicada.

---

## Aplicación

La versión desplegada de Idearia se encuentra disponible en:

https://idearia.onrender.com

---

## Estado del proyecto

El proyecto actualmente cuenta con:

- interfaces funcionales.
- autenticación.
- perfiles y permisos.
- base de datos PostgreSQL.
- conexión con Supabase PostgreSQL.
- almacenamiento privado de portadas mediante Supabase Storage.
- gestión de propuestas.
- acreditación de colaboradores.
- visor de documentos.
- favoritos.
- valoraciones.
- comentarios.
- administración.
- seguridad.
- pruebas automatizadas.
- despliegue en producción.

El desarrollo corresponde a la etapa de implementación y validación de la solución.

---

## Autoría y uso académico

**Idearia** es un proyecto académico desarrollado por **Luis Chiguay** para la asignatura Proyecto Integrado de Ingeniería en Informática – INACAP.

Copyright © 2026 Luis Chiguay. Todos los derechos reservados.

El código fuente, documentación, diseño, estructura y demás contenidos de este repositorio se publican exclusivamente con fines de evaluación académica y revisión del proyecto.

No se autoriza su reproducción, redistribución, publicación como trabajo propio ni reutilización total o parcial en otras entregas académicas sin autorización expresa del autor.
