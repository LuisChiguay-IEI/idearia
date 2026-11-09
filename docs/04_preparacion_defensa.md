# Preparación para la defensa técnica

Preguntas probables del docente, con una respuesta breve y el archivo donde mostrarlo.

---

**1. ¿Por qué Django y no otro framework?**
Trae resueltas la autenticación segura, la protección CSRF, el ORM, las migraciones y los formularios con validación. Es la tecnología del curso y se integra directamente con PostgreSQL/Supabase.

**2. ¿Cómo está organizado el proyecto?**
Hay seis apps, una por cada componente del diagrama de la Evaluación 2: `usuarios`, `colaboradores`, `planificaciones`, `interacciones`, `notificaciones` y `core`. → `docs/01_implementacion.md` §1

**3. ¿Por qué un solo modelo de usuario con un campo `rol`, y no tres tablas?**
Los tres perfiles comparten casi todos sus datos (nombre, correo, RUT, contraseña). Tres tablas duplicarían columnas y complicarían el login. Además, un Educador se convierte en Colaborador: con un campo basta cambiar `rol` al aprobar la solicitud. → `usuarios/models.py`

**4. ¿Por qué `AbstractUser`?**
Para reutilizar todo el sistema de autenticación de Django (hash, sesiones, permisos), agregando `rut`, `fecha_nacimiento` y `rol`, e iniciando sesión con correo (`USERNAME_FIELD = "email"`). Debía definirse antes del primer `migrate`.

**5. ¿Cómo se guardan las contraseñas?**
Con hash PBKDF2-SHA256 (`set_password`). En la BD se ve `pbkdf2_sha256$...`; la contraseña original no se puede recuperar. → prueba CP-037

**6. Si oculto el botón de administración, ¿un Educador puede entrar escribiendo la URL?**
No. Cada vista tiene un decorador (`@administrador_requerido`) que revisa el rol en el servidor y responde 403. → `usuarios/permisos.py`, pruebas CP-027 y CP-029

**7. ¿Qué pasa si un colaborador cambia el número en la URL para editar la propuesta de otro?**
Recibe 404, porque la consulta filtra por dueño: `get_object_or_404(Planificacion, pk=pk, colaborador=request.user)`. Esto previene IDOR. → CP-036

**8. ¿Cómo evitan favoritos o valoraciones duplicados?**
En dos niveles:
1. La vista usa `get_or_create` y `update_or_create`.
2. La base de datos tiene `UniqueConstraint(usuario, planificacion)` y `CheckConstraint(1 ≤ puntuación ≤ 5)`.

Aunque alguien se saltara la vista, PostgreSQL rechaza el dato. → `interacciones/models.py`, CP-045 y CP-046

**9. ¿Qué índices crearon y por qué?**
- `estado + fecha_publicacion`: el catálogo filtra por Publicada y ordena por fecha.
- `nivel + edad` y `duracion`: los filtros más usados.
- `usuario + leida`: el contador de notificaciones que aparece en todas las páginas.

→ `docs/01_implementacion.md` §2.4

**10. ¿El modelo está normalizado?**
Sí, en 3FN:
- Ámbito, núcleo, categoría y material son catálogos con FK o tablas intermedias, en vez de texto repetido.
- La solicitud no repite el RUT ni el nombre del usuario.
- `PlanificacionCategoria` es la tabla intermedia de la relación N:M.

**11. ¿Cómo se conectaron a Supabase?**
Solo se cambió `DATABASES` en `settings.py`, que lee `DB_HOST`, `DB_USER`, etc. desde `.env` con `python-dotenv`, con `sslmode=require`. El `.env` está en `.gitignore`. Se verifica con `connection.vendor` → `postgresql`. → README

**11b. ¿Con qué usuario se conecta Django a Supabase? ¿Qué es RLS?**
Con un usuario propio, `idearia_app`, no con el administrador `postgres`. Solo puede trabajar en el esquema `public` (mínimo privilegio). Supabase expone una API REST automática sobre `public`; por eso:
- las tablas de Idearia no dan permisos a los roles públicos (`anon`, `authenticated`);
- se activó **Row Level Security** sin políticas, así nadie puede leerlas por esa API.

Django no se ve afectado porque es el dueño de las tablas. → `core/migrations/0002_activar_rls_postgresql.py`

**11c. ¿Cumple el tiempo de respuesta con Supabase?**
La primera medición no cumplió: 6,8 s por búsqueda. El diagnóstico mostró que la causa era la red y no las consultas. La base está en EE. UU., cada consulta tarda 0,2 s en ir y volver, y abrir cada conexión 1,2 s.

Se aplicaron dos correcciones: desactivar los cursores del servidor (recomendado con *poolers*) y guardar los catálogos en caché. Con eso bajó a 2,7 s. Con conexiones persistentes, como en producción, el p95 queda en 1,96 s.

La solución definitiva es poner el servidor de la aplicación en la misma región que la base. → `docs/evidencias/rendimiento_supabase.txt`

**12. ¿Por qué hay una migración de datos?**
Para que `migrate` deje cargados los ámbitos y núcleos de las Bases Curriculares, las categorías y los materiales en cualquier base, incluida Supabase. → `planificaciones/migrations/0002_catalogos_iniciales.py`

**13. ¿Cómo validan los archivos subidos?**
Se revisan cuatro cosas: extensión permitida, tamaño (no vacío y máximo 10 MB), tipo MIME y **firma real** del contenido (un PDF empieza con `%PDF-`). Un `.exe` renombrado a `.pdf` se rechaza. Los DOCX con macros también. El archivo se guarda con un nombre aleatorio y nunca se ejecuta. → `core/validators.py`, CP-030 y CP-031

**14. ¿Cómo evitan la descarga de la planificación?**
- La carpeta de archivos no tiene URL pública.
- El PDF se entrega solo a usuarios con sesión y únicamente si la petición trae la cabecera del visor (si no, 403).
- Se dibuja con PDF.js en un `canvas`, sin la barra de descarga del navegador.
- Hay marca de agua con el correo del usuario, y se bloquean el clic derecho y la impresión.

No se puede impedir al 100 % una captura de pantalla: el objetivo es disminuir y controlar la distribución directa. → `planificaciones/views.py: documento_pdf`, CP-034

**15. ¿Por qué no se acepta `.doc`?**
Los navegadores no muestran Word. `.docx` se convierte a HTML con `mammoth`; el formato antiguo `.doc` requeriría instalar LibreOffice en el servidor. Es una decisión documentada.

**16. ¿Qué es CSRF y cómo lo manejan?**
Es un ataque donde otro sitio envía formularios en nombre del usuario. Django exige un token secreto en cada POST (`{% csrf_token %}`) y rechaza con 403 los que no lo traen. El logout también es POST. → CP-035

**17. ¿Qué otras cabeceras de seguridad usan?**
- Content-Security-Policy: solo scripts propios, lo que ayuda contra XSS.
- X-Frame-Options DENY: contra clickjacking.
- nosniff y Referrer-Policy.
- En producción: HTTPS forzado, cookies Secure y HSTS.

→ `core/middleware.py`, `settings.py`, CP-040

**18. ¿Qué pasa si alguien intenta adivinar contraseñas?**
Tras 5 intentos fallidos con el mismo correo e IP, se bloquea el login por 15 minutos. Cada intento queda registrado en `logs/idearia.log`. → CP-038

**19. ¿Cómo funciona el flujo de revisión?**
Es una máquina de estados: Borrador → En revisión → (Aprobada → Publicada) | Requiere corrección | Rechazada. Las transiciones válidas están definidas en `Planificacion.ACCIONES_REVISION`; cualquier otra se rechaza. Cada decisión notifica al colaborador y queda auditada. → `planificaciones/models.py`

**20. ¿Cómo probaron el sistema?**
- 102 pruebas automatizadas que cubren 60 casos (funcionales, de seguridad, casos borde e integración), ejecutadas en SQLite y PostgreSQL con 102/102 OK.
- Un recorrido en navegador real.
- Una prueba de carga hasta 50 usuarios simultáneos.

Todo con evidencia en `docs/evidencias`. → `docs/02_plan_de_pruebas.md`

**21. ¿Encontraron errores con las pruebas?**
Sí: una redirección abierta (*open redirect*), un favorito imposible de quitar y varios defectos visuales en móvil. Se corrigieron y se volvieron a ejecutar todas las pruebas. → §5 del plan de pruebas

**22. ¿Qué mejorarían?**
- Medir la carga directamente contra Supabase.
- Usar un servidor WSGI en producción.
- Hacer la prueba de usabilidad con 5 educadoras.
- Agregar recuperación de contraseña por correo.
- Mover los archivos a Supabase Storage si el hosting no tiene disco persistente.

---

## Demostración sugerida (5–7 minutos)

1. `manage.py verificar_bd` → `postgresql`, SSL activo, y las tablas en el *Table Editor* de Supabase (con RLS activo).
2. Registro de un usuario nuevo → la fila aparece en Supabase.
3. Educadora: buscar, filtrar, quitar un filtro con un clic, ver el detalle, abrir el visor (sin descarga), marcar un favorito y valorar.
4. Escribir `/administracion/` como Educadora → 403.
5. Colaboradora: crear una propuesta, adjuntar un PDF y enviar a revisión. Intentar subir un `.exe` → rechazado.
6. Administradora: solicitar corrección → la colaboradora corrige y reenvía → aprobar → publicar → aparece en el catálogo. Mostrar notificaciones y el registro de acciones.
7. Terminal: `$env:DB_ENGINE="sqlite"; manage.py test` → todas OK.
