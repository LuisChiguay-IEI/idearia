# Protocolo de prueba de usabilidad · CP-059 (RNF-08)

**Requisito RNF-08:** al menos 4 de 5 usuarios nuevos deben poder realizar una búsqueda, aplicar un filtro y abrir el detalle de una planificación **sin ayuda externa**, en un máximo de **3 minutos** por persona.

## 1. Participantes

- 5 personas que **no hayan usado Idearia**.
- Idealmente Educadoras/es de Párvulos o estudiantes de la carrera. Si no es posible, personas que no participaron en el desarrollo.
- Antes de comenzar, pedir su consentimiento verbal y explicar que se evalúa la aplicación, no a la persona.
- No registrar datos personales: usar códigos P1 a P5.

## 2. Preparación (5 minutos antes)

1. Servidor encendido con los datos de demostración (`manage.py cargar_demo`).
2. Sesión iniciada como `educadora@idearia.test` en el catálogo (`/ideas/`), sin filtros.
3. Cronómetro (el del celular sirve) y esta planilla impresa o abierta.
4. Usar el mismo computador y navegador con todos los participantes.

## 3. Guion (leer textualmente)

> "Imagina que trabajas en un jardín infantil con un grupo de **Nivel Medio** y tienes **entre 30 y 60 minutos** para una experiencia de aprendizaje. Usando Idearia, encuentra una idea que te sirva y **abre su planificación** para revisarla. Avísame cuando la tengas en pantalla. No puedo ayudarte durante la tarea; piensa en voz alta si quieres."

Iniciar el cronómetro al terminar de leer. **No dar pistas.** Si después de 3 minutos no lo logra, detener la tarea y marcarla como no completada.

## 4. Qué observar

| Paso | Se cumple cuando la persona… |
|---|---|
| T1 Búsqueda / filtro de nivel | Marca "Nivel Medio" o busca por palabra clave y obtiene resultados |
| T2 Filtro de duración | Marca "30 a 60 minutos" |
| T3 Detalle y planificación | Abre "Ver detalle" y luego "Ver planificación" |

## 5. Planilla de registro

| Participante | T1 | T2 | T3 | ¿Sin ayuda? | Tiempo (mm:ss) | Errores o dudas observadas | Comentario de la persona |
|---|:-:|:-:|:-:|:-:|:-:|---|---|
| P1 | ☐ | ☐ | ☐ | ☐ | | | |
| P2 | ☐ | ☐ | ☐ | ☐ | | | |
| P3 | ☐ | ☐ | ☐ | ☐ | | | |
| P4 | ☐ | ☐ | ☐ | ☐ | | | |
| P5 | ☐ | ☐ | ☐ | ☐ | | | |

**Éxito por participante:** T1, T2 y T3 cumplidos, sin ayuda y en 3:00 o menos.

## 6. Preguntas de cierre (1 minuto por persona)

1. Del 1 al 5, ¿qué tan fácil fue encontrar la idea?
2. ¿Qué fue lo más confuso?
3. ¿Qué agregarías o cambiarías?

## 7. Resultado y registro en la matriz

| Indicador | Valor |
|---|---|
| Participantes exitosos | ___ / 5 |
| Porcentaje de éxito | ___ % (meta: 80 % o más) |
| Tiempo promedio | ___ |
| Facilidad promedio (1-5) | ___ |
| **Estado CP-059** | OK si hay 4 o más éxitos; NO OK si no |

En `matriz_pruebas_E3.xlsx`, fila **CP-059**:

- completar *Resultado obtenido* (ejemplo: "4/5 exitosos, tiempo promedio 1:45");
- cambiar *Estado*;
- en *Evidencia*, indicar esta planilla completada (foto o PDF en `docs/evidencias/`);
- registrar la *Fecha*.

Si aparecen dificultades repetidas, por ejemplo que 2 o más personas no encuentran el filtro de duración, anotarlas en la hoja *Discrepancias* con una recomendación de mejora.
