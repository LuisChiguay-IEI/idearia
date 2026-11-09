# Plan y ejecución de pruebas · Idearia

Evaluación Sumativa N.º 3 · Proyecto Integrado · INACAP
Fecha de ejecución: **2026-11-09** · Responsable: Luis Chiguay

Este plan amplía los 10 casos de la Evaluación 2 (CP-001 a CP-010, que siguen incluidos) a **62 casos**. Cada caso ejecutado registra el resultado esperado, el obtenido, su estado y su evidencia. Los resultados provienen de ejecuciones reales; los casos que aún no se han podido ejecutar aparecen como **No ejecutado**.

**Matriz completa** (las 15 columnas: ID, funcionalidad, tipo, descripción, precondición, datos, esperado, obtenido, estado, evidencia, observaciones, posible defecto, recomendación, fecha y responsable):

- [`pruebas/matriz_pruebas_E3.xlsx`](pruebas/matriz_pruebas_E3.xlsx): Excel con las hojas *Matriz Testing*, *Resumen* (fórmulas), *Discrepancias* y *Leyenda*.
- [`pruebas/matriz_pruebas_E3.csv`](pruebas/matriz_pruebas_E3.csv): la misma matriz en CSV (separador `;`).

---

## 1. Estrategia

| Tipo | Cómo se ejecutó | Herramienta |
|---|---|---|
| Funcional, seguridad, casos borde | Pruebas automatizadas que simulan las peticiones HTTP del navegador (formularios, sesiones, roles) | `manage.py test` (Django TestCase) |
| Integración | Las mismas pruebas sobre **PostgreSQL 15** + inspección de tablas, restricciones e índices | Contenedor Docker local, `connection.vendor` |
| Sistema (E2E) | Recorrido en un navegador real con los 3 perfiles, a 1366 px y 390 px | `scripts/recorrido_navegador.py` (Microsoft Edge) |
| Rendimiento | Usuarios concurrentes que inician sesión y buscan con filtros aleatorios | `scripts/prueba_carga.py` |
| Usabilidad | Observación de 5 usuarios nuevos (RNF-08) | Manual (pendiente) |

**Por qué automatizadas:** cada prueba se puede **repetir** con un solo comando y deja un registro con fecha (`docs/evidencias/pruebas_automatizadas_*.txt`). El nombre de cada método incluye el ID del caso, por ejemplo `test_cp021_rechazo_exige_motivo`. Así cada fila de la matriz se puede rastrear hasta su código.

## 2. Entorno de ejecución

| Elemento | Valor |
|---|---|
| Sistema operativo | Windows 11 Enterprise |
| Python / Django | 3.12.10 / 5.2.19 |
| Base de datos | SQLite 3 (desarrollo), PostgreSQL 15.19 (contenedor Docker local) y **Supabase**: PostgreSQL 17, región us-west-2, Session pooler con SSL, rol propio `idearia_app` |
| Navegador | Microsoft Edge (Chromium), modo sin interfaz |
| Servidor (carga) | `runserver` de Django, un proceso, con datos de demostración (13 propuestas, 5 usuarios) |
| Datos | Usuarios ficticios con dominio `.test`; archivos PDF/DOCX generados para las pruebas |

## 3. Resumen de resultados

| Indicador | Valor |
|---|---|
| Casos del plan | **62** |
| Ejecutados | **61** (98,4 %) |
| OK | **60** (98,4 % de los ejecutados) |
| NO OK | **1**: CP-061, rendimiento con Supabase usando el servidor de desarrollo (ver D-11; mitigado en CP-062) |
| No ejecutado | **1**: CP-059, usabilidad con 5 personas (protocolo listo) |
| Pruebas automatizadas | **104 métodos**: OK en SQLite; 102/102 OK en PostgreSQL 15 local |
| Integración con Supabase | Migraciones, datos, registro visible en Supabase (CP-055) y RLS activo en las 23 tablas |

| Tipo | Casos | OK | NO OK | No ejecutado |
|---|---:|---:|---:|---:|
| Funcional | 25 | 25 | 0 | 0 |
| Seguridad | 17 | 17 | 0 | 0 |
| Caso borde | 11 | 11 | 0 | 0 |
| Integración | 4 | 4 | 0 | 0 |
| Rendimiento | 3 | 2 | 1 | 0 |
| Usabilidad | 1 | 0 | 0 | 1 |
| Sistema (E2E) | 1 | 1 | 0 | 0 |

### Prueba de rendimiento (CP-058, RNF-01: búsquedas en 2 s o menos)

| Escenario | Peticiones | Promedio | Mediana | p95 | Máximo | Errores | Peticiones/s | RNF-01 |
|---|---:|---:|---:|---:|---:|---:|---:|:-:|
| 1 usuario x 30 búsquedas (línea base) | 30 | 0,030 s | 0,031 s | 0,036 s | 0,038 s | 0 | 23,1 | OK |
| 10 usuarios x 20 búsquedas | 200 | 0,143 s | 0,140 s | 0,189 s | 0,206 s | 0 | 52,0 | OK |
| 25 usuarios x 20 búsquedas | 500 | 0,397 s | 0,393 s | 0,541 s | 0,632 s | 0 | 48,0 | OK |
| 50 usuarios x 10 búsquedas | 500 | 0,778 s | 0,788 s | 1,113 s | 1,647 s | 0 | 41,5 | OK |

Las filas anteriores son con base de datos **local** (SQLite).

### Rendimiento con Supabase (CP-061, CP-062)

Idearia corriendo en un PC en Chile, conectada a Supabase en **us-west-2 (Oregón, EE. UU.)**. Cada consulta SQL tarda al menos **0,20 s** de ida y vuelta, y abrir una conexión tarda **1,22 s**.

| Escenario | Consultas por búsqueda | Promedio | p95 | Máximo | Errores | RNF-01 |
|---|---:|---:|---:|---:|---:|:-:|
| runserver, antes de optimizar, 1 usuario | 11 | 6,769 s | 7,072 s | 7,083 s | 0 | NO OK |
| runserver, antes de optimizar, 10 usuarios | 11 | 5,770 s | 6,113 s | 6,435 s | 0 | NO OK |
| runserver, optimizado, 1 usuario | 7 | 2,684 s | 3,075 s | 3,121 s | 0 | NO OK |
| runserver, optimizado, 10 usuarios | 7 | 2,319 s | 2,637 s | 2,671 s | 0 | NO OK |
| Conexiones persistentes (`CONN_MAX_AGE=60`), optimizado | 7 | 1,541 s | 1,957 s | 2,148 s | 0 | **OK** |

Optimizaciones aplicadas a partir de esta medición:
1. `DISABLE_SERVER_SIDE_CURSORS` (recomendación de Django para *poolers*).
2. Caché de los catálogos de filtros.

Evidencia: `docs/evidencias/rendimiento_supabase.txt`, `docs/evidencias/carga_*.md` (resumen) y `carga_*.csv` (cada petición).

## 4. Casos y resultados

Vista compacta. El detalle de precondiciones, datos, evidencia y recomendaciones está en la matriz Excel/CSV.

| ID | Funcionalidad | Tipo | Resultado obtenido | Estado |
|---|---|---|---|---|
| CP-001 | Registro correcto de un Educador/a | Funcional | Cuenta creada con rol EDUCADOR, sesión iniciada y redirección al catálogo con el mensaje de éxito | **OK** |
| CP-002 | Inicio de sesión con credenciales válidas (CP-001 de la E2) | Funcional | Sesión creada; redirección a inicio → catálogo. El correo no distingue mayúsculas | **OK** |
| CP-003 | Cerrar sesión | Funcional | GET → 405; POST → sesión eliminada y redirección a /ingresar/ | **OK** |
| CP-004 | Búsqueda por palabra clave | Funcional | Se obtuvo solo 'Pintamos con esponjas' en ambos casos (coincidencia por título y por material) | **OK** |
| CP-005 | Filtros combinados nivel + edad + duración (CP-003 de la E2) | Funcional | 1 resultado correcto y 3 chips de filtros activos; duración 'corta' devuelve solo la idea de 20 min | **OK** |
| CP-006 | Filtro por materiales disponibles | Funcional | Solo aparece la idea A | **OK** |
| CP-007 | Filtro por ámbito, núcleo y categoría | Funcional | Cada filtro devolvió exactamente la idea esperada | **OK** |
| CP-008 | Visualizar el detalle completo | Funcional | Detalle mostrado con todos los datos y el botón 'Ver planificación' | **OK** |
| CP-009 | Ver planificación PDF dentro de Idearia (CP-004 de la E2) | Funcional | PDF.js dibujó el documento en canvas; la página no contiene 'Descargar' ni 'download'. En el navegador real: 1 página renderizada, sin errores | **OK** |
| CP-010 | Ver planificación Word (.docx) | Funcional | Contenido convertido a HTML y mostrado en el visor con marca de agua | **OK** |
| CP-011 | Agregar y quitar favorito | Funcional | Agregada y visible en la lista; quitada correctamente | **OK** |
| CP-012 | Valorar una idea | Funcional | Valoración 4 guardada; total de valoraciones = 1 en el detalle | **OK** |
| CP-013 | Comentar una idea | Funcional | Comentario publicado y visible | **OK** |
| CP-014 | Enviar solicitud de acreditación | Funcional | Solicitud PENDIENTE; archivo en acreditaciones/<uuid>.pdf; notificación NUEVA_SOLICITUD creada | **OK** |
| CP-015 | Aprobar solicitud de colaborador | Funcional | EN_REVISION → APROBADA; rol COLABORADOR; notificación y registro APROBAR_SOLICITUD; ya puede crear propuestas | **OK** |
| CP-016 | Guardar propuesta como borrador | Funcional | Propuesta en BORRADOR con el colaborador correcto | **OK** |
| CP-017 | Registrar propuesta con archivo obligatorio y enviarla (CP-006 de la E2) | Funcional | EN_REVISION con fecha de envío y notificación; sin archivo → error en el campo 'archivo' | **OK** |
| CP-018 | Aprobar propuesta (CP-009 de la E2) | Funcional | APROBADA; no aparece en el catálogo; notificación PROPUESTA_APROBADA; registro con el administrador | **OK** |
| CP-019 | Publicar y verificar visibilidad en el catálogo | Funcional | PUBLICADA con fecha_publicacion; visible en el catálogo; borradores y en revisión no aparecen | **OK** |
| CP-020 | Solicitar corrección y reenviar | Funcional | REQUIERE_CORRECCION con notificación; tras corregir y reenviar → EN_REVISION | **OK** |
| CP-021 | Rechazar con motivo obligatorio (CP-010 de la E2) | Funcional | Sin motivo: sigue EN_REVISION; con motivo: RECHAZADA y observación guardada | **OK** |
| CP-022 | Retirar una publicación | Funcional | RETIRADA; no aparece en el catálogo | **OK** |
| CP-023 | Notificaciones por cambios de estado | Funcional | Notificaciones creadas en cada flujo; la lista muestra solo las propias y el contador de no leídas | **OK** |
| CP-024 | Desactivar y reactivar una cuenta | Funcional | is_active False → True; el administrador no puede desactivarse a sí mismo | **OK** |
| CP-025 | Auditoría de acciones administrativas | Funcional | Registros APROBAR/PUBLICAR_PROPUESTA y ACTIVAR/DESACTIVAR_USUARIO con el administrador correcto | **OK** |
| CP-026 | Rechazo de credenciales incorrectas (CP-002 de la E2) | Seguridad | 'Correo o contraseña incorrectos.'; sin sesión | **OK** |
| CP-027 | Usuario sin permisos accede a administración por URL (CP-008 de la E2) | Seguridad | 403 en todas las rutas administrativas; un Educador/a tampoco crea propuestas (403) | **OK** |
| CP-028 | Acceso anónimo a una URL protegida | Seguridad | Redirección a /ingresar/?next=/administracion/usuarios/ | **OK** |
| CP-029 | Ejecutar una acción administrativa por POST sin rol | Seguridad | 403 en ambos casos; el estado sigue EN_REVISION | **OK** |
| CP-030 | Archivo con formato no permitido (CP-007 de la E2) | Seguridad | Rechazados con 'Formato no permitido. Formatos aceptados: …' | **OK** |
| CP-031 | Extensión válida con contenido falso | Seguridad | 'El contenido del archivo no corresponde a su extensión.' | **OK** |
| CP-032 | Archivo demasiado grande | Seguridad | 'El archivo supera el tamaño máximo de 1 MB.' | **OK** |
| CP-033 | Envío de formularios sin datos obligatorios o inválidos | Seguridad | Sin registros creados; errores en cada campo obligatorio | **OK** |
| CP-034 | Sin descarga directa del PDF (CP-005 de la E2) | Seguridad | 403 / 200 application/pdf 'inline' 'no-store' / 302 al login | **OK** |
| CP-035 | Formulario POST sin token CSRF | Seguridad | 403 | **OK** |
| CP-036 | Editar la propuesta de otro colaborador | Seguridad | 404 | **OK** |
| CP-037 | Contraseñas almacenadas con hash | Seguridad | Hash 'pbkdf2_sha256$…'; check_password válido | **OK** |
| CP-038 | Bloqueo tras intentos fallidos | Seguridad | 'Demasiados intentos fallidos…'; sin sesión | **OK** |
| CP-039 | Inyectar rol en el registro | Seguridad | rol EDUCADOR; is_superuser False | **OK** |
| CP-040 | Cabeceras de seguridad y páginas de error sin datos técnicos | Seguridad | Cabeceras presentes; 404 y 403 personalizadas sin 'Traceback' | **OK** |
| CP-041 | Acceso al certificado de otro usuario | Seguridad | 200 / 200 / 404 | **OK** |
| CP-042 | Script en un comentario | Seguridad | Mostrado como &lt;script&gt;…; además la CSP bloquea scripts en línea | **OK** |
| CP-043 | Búsqueda sin resultados | Caso borde | 0 resultados y 'No encontramos ideas con esos criterios' | **OK** |
| CP-044 | Textos excesivamente largos | Caso borde | Errores de validación en los tres casos; nada guardado | **OK** |
| CP-045 | Duplicación de favoritos | Caso borde | 1 registro; IntegrityError por UNIQUE(usuario, planificacion) | **OK** |
| CP-046 | Doble valoración | Caso borde | 1 registro con puntuación 2; IntegrityError por UNIQUE y por CHECK 1-5 | **OK** |
| CP-047 | Planificación inexistente o no publicada | Caso borde | 404 en los tres casos | **OK** |
| CP-048 | Propuesta rechazada | Caso borde | Redirección con aviso; enviar_a_revision lanza TransicionInvalida | **OK** |
| CP-049 | Usuario bloqueado o inactivo | Caso borde | Mensaje genérico; sin sesión | **OK** |
| CP-050 | Segunda solicitud con una activa | Caso borde | Redirección con aviso; IntegrityError por el índice único parcial | **OK** |
| CP-051 | El autor valora su propia propuesta | Caso borde | Mensaje de error; 0 valoraciones | **OK** |
| CP-052 | Transición inválida | Caso borde | Sigue EN_REVISION; mensaje 'No se puede realizar esta acción…' | **OK** |
| CP-053 | Parámetros manipulados en la URL | Caso borde | 200 OK | **OK** |
| CP-054 | connection.vendor devuelve 'postgresql' | Integración | Supabase: Motor postgresql, PostgreSQL 17, SSL activo, 0 migraciones pendientes. También PostgreSQL 15 local: 102/102 pruebas OK | **OK** |
| CP-055 | Registro creado en Idearia visible en Supabase | Integración | Mensaje 'Registro realizado exitosamente'; la consulta SQL directa en Supabase devuelve la fila id 6 con rol EDUCADOR, RUT 21345678-4 y contraseña con hash pbkdf2_sha256 | **OK** |
| CP-056 | Planificación: archivo almacenado y referencia correcta en BD | Integración | Ruta planificaciones/<uuid>.pdf existe; nombre_archivo, tipo 'pdf' y tamaño coinciden | **OK** |
| CP-057 | Migraciones y restricciones en PostgreSQL | Integración | 16 tablas de Idearia; restricciones UNIQUE/CHECK/FK e índices presentes; 3 ámbitos, 8 núcleos | **OK** |
| CP-058 | Carga de búsquedas concurrentes (10, 25 y 50 usuarios) | Rendimiento | Línea base 1 u: prom. 0,030 s · 10 u: prom. 0,143 s, p95 0,189 s · 25 u: prom. 0,397 s, p95 0,541 s · 50 u: prom. 0,778 s, p95 1,113 s, máx. 1,647 s · 0 errores (1.230 peticiones) | **OK** |
| CP-059 | 5 usuarios nuevos buscan, filtran y abren un detalle sin ayuda | Usabilidad | — | **No ejecutado** |
| CP-060 | Recorrido en navegador real por las pantallas de los 3 perfiles | Sistema (E2E) | 0 errores; ancho en móvil 390 px; 18 capturas | **OK** |
| CP-061 | Búsquedas contra Supabase con el servidor de desarrollo | Rendimiento | Antes de optimizar: p95 7,07 s (1 u) y 6,11 s (10 u). Tras optimizar: p95 3,08 s (1 u) y 2,64 s (10 u). 0 errores | **NO OK** |
| CP-062 | Búsquedas contra Supabase con conexiones persistentes (configuración de producción) | Rendimiento | 7 consultas por búsqueda; prom. 1,541 s, mediana 1,459 s, p95 1,957 s, máx. 2,148 s | **OK** |

## 5. Comparación esperado vs. obtenido: discrepancias encontradas

Durante la construcción y la ejecución de pruebas aparecieron estas diferencias entre lo esperado y lo obtenido. Todas son hallazgos reales; en cada caso se indica cómo se resolvieron.

| ID | Origen | Esperado | Obtenido | Severidad | Acción | Estado |
|---|---|---|---|---|---|---|
| D-01 | Revisión de código (CP-024) | Redirección solo interna tras cambiar el estado de un usuario | El parámetro `volver` aceptaba cualquier URL (*open redirect*) | Media | `redireccion_segura()` con `url_has_allowed_host_and_scheme` + prueba | Corregido |
| D-02 | Revisión funcional (CP-011) | Siempre se puede quitar un favorito | Si la idea se retiraba, no se podía quitar | Baja | "Quitar" ya no exige estado Publicada | Corregido |
| D-03 | CP-060 navegador | Botón "Registrarse" legible | Texto azul sobre fondo azul (conflicto de especificidad CSS) | Media | Clase propia `.acciones-acceso` | Corregido |
| D-04 | CP-060 (390 px) | Encabezado en una línea; resultados visibles | El avatar bajaba a otra línea; los filtros ocupaban la pantalla | Baja | Ajuste del espaciado móvil; filtros cerrados por defecto | Corregido |
| D-05 | CP-060 navegador | Formulario y tablas legibles | Etiquetas de estado superpuestas; borde de `fieldset`; RUT y fecha partidos | Baja | Ajustes de CSS y plantillas | Corregido |
| D-06 | `makemigrations` | Una migración inicial por app | Django generó 0001–0003 por dependencias cruzadas | Baja | Regeneradas en orden de dependencias | Corregido |
| D-07 | `check --deploy` | Sin advertencias | W021: HSTS *preload* desactivado | Informativa | Configurable en `.env`; requiere un dominio definitivo | Aceptado |
| D-08 | Diseño E2 vs. E3 | Matriz E2: el Colaborador no usa favoritos ni valoraciones; formatos .doc/.docx/.pdf | El Colaborador conserva sus funciones de Educador/a; .doc no se acepta | Informativa | Decisión documentada (01_implementacion §6 y §12) | Aceptado |
| D-09 | CP-058 carga | Tiempo estable al aumentar usuarios | La latencia crece en forma lineal (p95 0,19 s → 1,11 s de 10 a 50 usuarios); techo de ~50 peticiones/s | Media (escala) | Ver recomendaciones R-02 y R-03 | Pendiente |
| D-10 | CP-059 | Todos los casos ejecutados | La usabilidad requiere 5 participantes reales | — | Protocolo y planilla en `pruebas/protocolo_usabilidad_CP059.md` | Pendiente |
| D-11 | CP-061 Supabase | Búsquedas en 2 s o menos también con Supabase | 6,8 s: 0,2 s por viaje a us-west-2, conexión nueva por petición (1,2 s) y cursores del servidor en 4 listas | Alta (RNF-01) | Cursores desactivados y catálogos en caché (6,8 → 2,7 s); con conexiones persistentes, p95 1,96 s (CP-062) | Mitigado; ver R-02 |
| D-12 | Configuración de Supabase | Crear el proyecto `idearia` en São Paulo por la API | 403: la cuenta no pertenece a ninguna organización; solo tiene acceso a un proyecto | Baja | Se usó el proyecto existente (vacío, creado hoy) con el rol `idearia_app` y RLS | Resuelto |

Las correcciones se verificaron con una nueva ejecución de las 102 pruebas (regresión) y del recorrido en navegador.

## 6. Análisis

- **Funcionalidad:** los 15 flujos que exige la evaluación funcionan de extremo a extremo con los tres perfiles: registro, login, búsqueda, filtros, detalle, favorito, valoración, comentario, solicitud de colaborador, propuesta, carga de planificación, envío a revisión, aprobación y publicación.
- **Seguridad:** los controles se comprueban **en el servidor**, no solo en la interfaz. Las pruebas envían peticiones directas (URL escrita a mano, POST sin rol, POST sin CSRF, campos inyectados, archivos maliciosos) y todas son rechazadas. La base de datos aplica sus propias restricciones (UNIQUE, CHECK, índice parcial): aunque alguien se saltara la aplicación, no podría duplicar favoritos o valoraciones, ni registrar puntuaciones fuera de rango.
- **Rendimiento:** con 50 usuarios simultáneos el p95 (1,11 s) sigue bajo el umbral de 2 s. Sin embargo, la latencia promedio crece casi en proporción a los usuarios (0,14 s → 0,40 s → 0,78 s) mientras el rendimiento se mantiene en ~41–52 peticiones/s. Esto indica que el límite es el **servidor de desarrollo** (un proceso), no las consultas: con un solo usuario la búsqueda tarda 0,030 s de promedio (línea base medida). Extrapolando, el p95 superaría los 2 s con unos 90 usuarios simultáneos en este entorno.
- **Rendimiento con Supabase:** la primera medición dio **NO OK** (6,8 s por búsqueda). El diagnóstico mostró que el tiempo no venía de las consultas (0,03 s con la base local), sino de la **red**: 0,2 s por viaje a EE. UU. y 1,2 s por abrir cada conexión. Además, los cursores del servidor multiplicaban los viajes. Con dos optimizaciones el tiempo bajó un 60 % (2,7 s). Con conexiones persistentes, como en producción, se cumple RNF-01 (p95 1,96 s), aunque con poco margen. La medida definitiva es ubicar el servidor de aplicación en la misma región que la base de datos, como plantea el diagrama de despliegue de la Evaluación 2, o crear la base en São Paulo (R-02).
- **Limitaciones de las pruebas:** las pruebas automatizadas crean una base temporal, por lo que se ejecutan en SQLite o PostgreSQL local; el rol `idearia_app` no tiene permiso para crear bases en Supabase, por seguridad. La integración con Supabase se comprobó por separado (CP-054, CP-055, CP-061, CP-062). La protección contra descarga **disminuye** la distribución, pero no impide capturas de pantalla; es una limitación técnica reconocida desde la Evaluación 2.

## 7. Recomendaciones

| ID | Recomendación | Basada en |
|---|---|---|
| R-01 | Para el informe, agregar una captura del *Table Editor* de Supabase con la fila de `registro.cp055@idearia.test` (CP-055 ya está verificado por SQL). | CP-055 |
| R-02 | Desplegar el servidor de aplicación en la misma región que Supabase, o crear la base en sa-east-1 (São Paulo) desde una organización propia, y repetir CP-061. | D-11 |
| R-03 | En producción, usar un servidor WSGI con varios procesos (`waitress` o `gunicorn`) y `DB_CONN_MAX_AGE=60` para reutilizar conexiones. | D-09, D-11 |
| R-04 | Realizar la prueba de usabilidad con 5 educadoras/es (RNF-08) siguiendo [`pruebas/protocolo_usabilidad_CP059.md`](pruebas/protocolo_usabilidad_CP059.md). | CP-059 |
| R-05 | Con varios procesos, mover el bloqueo de login a una caché compartida (BD o Redis). | CP-038 |
| R-06 | Agregar la recuperación de contraseña por correo cuando haya un servidor SMTP. | Alcance |
| R-07 | Si el hosting no tiene disco persistente, mover `media_protegida/` a un *bucket* privado de Supabase Storage. | 01_implementacion §12 |
| R-08 | Mantener la suite automatizada como prueba de regresión: ejecutar `manage.py test` antes de cada entrega o commit importante. | D-01…D-06 |

## 8. Cómo repetir las pruebas

```powershell
$env:DB_ENGINE="sqlite"; .\.venv\Scripts\python.exe manage.py test --verbosity 2
.\.venv\Scripts\python.exe manage.py runserver 8001
.\.venv\Scripts\python.exe scripts\prueba_carga.py --usuarios 25 --peticiones 20
```

La primera línea fuerza SQLite solo para esa terminal y ejecuta las pruebas que cubren CP-001 a CP-054 y CP-056. CP-057 (migraciones en PostgreSQL), CP-058 (carga) y CP-060 (navegador) se ejecutan con sus scripts. La segunda va en otra terminal, para la prueba de carga de la tercera línea.

Para registrar un caso pendiente, edita en la matriz Excel las columnas *Resultado obtenido*, *Estado*, *Evidencia* y *Fecha*. La hoja *Resumen* se recalcula sola.
