# Trazabilidad: requisitos ↔ implementación ↔ pruebas

**Criterio:** se conservan los identificadores del registro de requisitos de la Evaluación 1/2 (*App RF_RNF_Proyecto_Parvularia*, RF-01 a RF-26 y RNF-01 a RNF-12), que ya estaban relacionados con las historias de usuario y la matriz de pruebas. Los requisitos nuevos de la Evaluación 3 se agregan desde **RF-27**.

## 1. Equivalencia con los requisitos de la pauta de la Evaluación 3

| Requisito E3 | ID en el registro de requisitos |
|---|---|
| RF-01 Autenticación | RF-26 (registro) + **RF-27** (inicio y cierre de sesión) |
| RF-02 Gestión de perfiles y roles | **RF-28** |
| RF-03 Búsqueda de ideas | RF-01, RF-02 |
| RF-04 Filtros | RF-01 a RF-05 |
| RF-05 Detalle de idea | RF-06 |
| RF-06 Visualización de planificación | **RF-30** |
| RF-07 Favoritos | RF-07, RF-08 |
| RF-08 Valoraciones | RF-09, RF-10 |
| RF-09 Comentarios | RF-09, RF-10 |
| RF-10 Solicitud de colaborador | RF-11, RF-12, RF-13 |
| RF-11 Validación de profesional | RF-18, RF-19 |
| RF-12 Registro de propuesta | RF-14 |
| RF-13 Adjuntar planificación | **RF-29** |
| RF-14 Flujo de revisión | RF-15, RF-16, RF-17 + **RF-31** |
| RF-15 Administración de contenido | RF-21, RF-22, RF-23, RF-24 |
| RF-16 Publicación | RF-23, RF-25 |
| RF-17 Notificaciones | **RF-32** |

**Requisitos nuevos (E3):**

| ID | Requisito |
|---|---|
| RF-27 | Iniciar y cerrar sesión con correo y contraseña |
| RF-28 | Identificar el rol del usuario y mostrar solo las funciones autorizadas |
| RF-29 | Exigir una planificación PDF o DOCX validada para enviar a revisión |
| RF-30 | Visualizar la planificación dentro de Idearia sin opción de descarga |
| RF-31 | Solicitar correcciones a una propuesta (estado *Requiere corrección*) |
| RF-32 | Notificar los cambios de estado relevantes |
| RF-33 | Moderar (ocultar o mostrar) comentarios |

## 2. Requisitos funcionales

| RF | Requisito | Implementación | Pruebas |
|---|---|---|---|
| RF-01 | Buscar por nivel educativo | `planificaciones/busqueda.py` · `/ideas/?nivel=` | CP-005 |
| RF-02 | Buscar por OA/OAT | filtro `oa` y búsqueda `q` | CP-004 |
| RF-03 | Filtrar por materiales | filtro `materiales` (subconjunto disponible) | CP-006 |
| RF-04 | Filtrar por características del grupo | filtros `edad` y `nivel` | CP-005 |
| RF-05 | Filtrar por duración | filtro `duracion` (rangos) | CP-005 |
| RF-06 | Detalle de la idea | `planificaciones/views.py: detalle` | CP-008, CP-047 |
| RF-07 | Agregar a favoritos | `interacciones/views.py: favorito` | CP-011, CP-045 |
| RF-08 | Quitar de favoritos | `favorito` (acción quitar) | CP-011 |
| RF-09 | Mostrar valoraciones y comentarios | `detalle` (resumen y lista) | CP-012, CP-013 |
| RF-10 | Registrar valoración y comentario | `valorar`, `comentar` | CP-012, CP-013, CP-046, CP-051 |
| RF-11 | Registrar colaborador (solicitud) | `colaboradores/views.py: nueva_solicitud` | CP-014, CP-050 |
| RF-12 | Adjuntar acreditación | `SolicitudColaboradorForm` + `validar_archivo` | CP-014, CP-030 |
| RF-13 | Consultar estado de acreditación | `mi_solicitud` | CP-014, CP-015 |
| RF-14 | Crear y guardar borrador | `views_colaborador._guardar_propuesta` | CP-016 |
| RF-15 | Enviar a revisión | `Planificacion.enviar_a_revision` | CP-017 |
| RF-16 | Consultar revisión de aportes | `mis_propuestas` | CP-020 |
| RF-17 | Corregir y reenviar | estado *Requiere corrección* → *En revisión* | CP-020, CP-048 |
| RF-18 | Listar solicitudes de acreditación | `colaboradores/views.py: admin_lista` | CP-027 |
| RF-19 | Aprobar o rechazar acreditación | `admin_resolver` + `SolicitudColaborador.resolver` | CP-015 |
| RF-20 | Gestionar estado de usuarios | `usuarios/views.py: admin_cambiar_estado` | CP-024, CP-049 |
| RF-21 | Listar planificaciones pendientes | `views_admin.revision` | CP-018 |
| RF-22 | Revisar información de la planificación | panel de detalle en `revision` | CP-018 |
| RF-23 | Aprobar y publicar | acciones `aprobar` y `publicar` | CP-018, CP-019 |
| RF-24 | Rechazar con motivo | acción `rechazar` | CP-021 |
| RF-25 | Despublicar | acciones `retirar` y `republicar` | CP-022 |
| RF-26 | Registro de usuario | `usuarios/views.py: registro` | CP-001, CP-033, CP-039 |
| RF-27 | Inicio y cierre de sesión | `IngresarView`, `SalirView` | CP-002, CP-003, CP-026, CP-038 |
| RF-28 | Perfiles y roles | `Usuario.rol`, `usuarios/permisos.py` | CP-027, CP-028, CP-029 |
| RF-29 | Planificación obligatoria y validada | `PropuestaForm.clean` + `core/validators.py` | CP-017, CP-030, CP-031, CP-032, CP-056 |
| RF-30 | Visualización sin descarga | `visor`, `documento_pdf`, `static/js/visor.js` | CP-009, CP-010, CP-034 |
| RF-31 | Solicitar corrección | acción `corregir` | CP-020 |
| RF-32 | Notificaciones | `notificaciones/servicios.py` | CP-023 |
| RF-33 | Moderar comentarios | `interacciones/views.py: moderar_comentario` | prueba `test_administrador_oculta_comentario` |

## 3. Requisitos no funcionales

| RNF | Requisito | Implementación | Verificación |
|---|---|---|---|
| RNF-01 | Búsquedas en 2 s o menos | Índices, subconsultas, paginación de 9, caché de catálogos, sin cursores del servidor | CP-058 local (p95 1,11 s con 50 usuarios); Supabase: CP-061 NO OK con runserver, CP-062 OK con conexiones persistentes (p95 1,96 s) |
| RNF-02 | Detalle en 2 s o menos | `select_related` y `prefetch_related` | Recorrido E2E (CP-060) |
| RNF-03 | Acreditación visible solo para el dueño y el administrador | Vista `documento` | CP-041 |
| RNF-04 | Acreditación PDF/JPG/PNG de 10 MB como máximo | `EXTENSIONES_ACREDITACION` | CP-030, CP-032 |
| RNF-05 | Solo colaboradores aprobados envían propuestas | `colaborador_requerido` (rol asignado al aprobar) | CP-027 |
| RNF-06 | Acciones de contenido solo para el administrador | `administrador_requerido` | CP-029 |
| RNF-07 | Persistencia de favoritos, comentarios y borradores | Base de datos relacional | CP-011, CP-016 |
| RNF-08 | Usabilidad: 4 de 5 usuarios sin ayuda | Interfaz basada en los mockups | CP-059 (pendiente) |
| RNF-09 | Mensaje de confirmación o error tras cada acción | Framework de mensajes de Django | Todas las vistas de acción |
| RNF-10 | Los borradores no se pierden | Guardado en BD | CP-016 |
| RNF-11 | Registro de acciones administrativas | `core/auditoria.py` | CP-025 |
| RNF-12 | Filtros activos visibles y removibles con un clic | `busqueda.filtros_activos` (chips) | CP-005 (3 chips) |

## 4. Historias de usuario

Las **25 historias** (EDU-01 a EDU-09, COL-01 a COL-08, ADM-01 a ADM-08) están implementadas a través de los RF anteriores. Sus escenarios alternativos se probaron como casos borde:

| Escenario | Caso |
|---|---|
| Sin resultados | CP-043 |
| Favorito ya guardado | CP-045 |
| Comentario vacío | prueba `test_comentario_vacio_no_se_publica` |
| Correo ya registrado | CP-033 |
| Colaborador no verificado | CP-027 |
| Envío duplicado | prueba `test_propuesta_en_revision_no_se_edita` |
| Solicitud ya procesada | prueba `test_solicitud_ya_procesada_no_se_resuelve_dos_veces` |
| Rechazo sin motivo | CP-021 |
| Publicación duplicada | CP-052 |
