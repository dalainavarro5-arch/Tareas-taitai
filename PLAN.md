# TaiTai Tareas — Plan fase por fase

> Documento maestro del proyecto. Sirve como especificación y como **prompt**:
> al empezar una sesión nueva, di *"vamos por la Fase N de PLAN.md"* y hay
> suficiente contexto para continuar sin re-explicar nada.

---

## 1. El problema

Classroom te obliga a entrar curso por curso para saber qué debes. Las instrucciones
viven repartidas entre la descripción de la tarea, los archivos adjuntos y los avisos.
Y cuando por fin sabes qué hacer, arrancas desde cero en un documento en blanco.

## 2. La solución

Tres capas encima de Classroom:

```
  Google Classroom
        │  (lee: cursos, tareas, avisos, materiales, estado de entregas)
        ▼
  ┌───────────────┐
  │  SINCRONIZAR  │  → todo en un SQLite local, siempre disponible
  └───────┬───────┘
          ▼
  ┌───────────────┐
  │    TRIAGE     │  → Claude clasifica: 🟢 IA sola / 🟡 IA + tu input / 🔴 solo tú
  └───────┬───────┘
          ▼
  ┌───────────────┐
  │   REDACTAR    │  → borrador como Google Doc en TU Drive
  └───────┬───────┘
          ▼
     Tú revisas  →  tú entregas
```

## 3. Principios de diseño

1. **Nada se entrega sin tu confirmación explícita.** El sistema redacta y adjunta;
   el `turnIn` final es siempre un acto tuyo. Esto no es solo ética — es ingeniería:
   un modelo que malinterpreta una consigna y entrega solo es un desastre irreversible.
2. **Mínimo privilegio.** Scopes `readonly` donde se pueda; en Drive usamos
   `drive.file`, que solo da acceso a los archivos que la app crea. La app nunca
   puede leer el resto de tu Drive.
3. **Los secretos jamás tocan el repo.** `credentials.json`, `token.json` y `.env`
   están en `.gitignore` desde el commit uno.
4. **Útil sin internet.** Todo lo sincronizado vive en SQLite local.
5. **Los borradores viven en TU Drive**, no dentro de la app. Si mañana abandonas
   el proyecto, tu trabajo sigue siendo tuyo y accesible.

---

# Las fases

## Fase 0 — Cimientos 🏗️

**Objetivo:** repo navegable y ejecutable, aunque no haga nada todavía.

- Estructura de paquetes (`taitai/`: `auth`, `classroom`, `store`, `triage`, `draft`, `cli`)
- `requirements.txt` + entorno virtual
- `.gitignore` con los secretos bloqueados ✅
- `README.md` + `PLAN.md` ✅
- Primer commit y push

**Entregable:** `python -m taitai --help` responde.

---

## Fase 1 — Puerta de entrada: OAuth con Google 🔑

> ⚠️ **La fase más riesgosa de todo el proyecto.** Si algo va a fallar, falla aquí.
> No avances a la Fase 2 hasta que esta cierre limpia.

**Objetivo:** que la app pueda leer tus cursos con tu permiso.

Pasos:
1. Crear proyecto en Google Cloud Console
2. Habilitar **Google Classroom API** y **Google Drive API**
3. Configurar la pantalla de consentimiento OAuth (tipo *Externo*, estado *Testing*)
   y agregarte a ti mismo como usuario de prueba
4. Crear credencial **OAuth client ID → Desktop app** y bajar `credentials.json`
5. Implementar el flujo OAuth que guarda `token.json`
6. Prueba de humo: listar tus cursos

**Scopes:**

| Scope | Para qué |
|---|---|
| `classroom.courses.readonly` | Listar tus cursos |
| `classroom.coursework.me` | Leer tus tareas **y** poder adjuntar/entregar (fase 6) |
| `classroom.announcements.readonly` | Leer los avisos del profesor |
| `classroom.courseworkmaterials.readonly` | Material de apoyo publicado |
| `classroom.student-submissions.me.readonly` | Estado: entregada / atrasada / calificada |
| `drive.file` | Crear y editar **solo** los documentos que genera la app |

**Riesgos reales de esta fase:**

- 🔴 **Tu cuenta escolar puede bloquear apps de terceros.** Es el escenario más
  probable de fracaso. Muchos Google Workspace for Education tienen restringido el
  acceso de apps externas por política del administrador.
  *Plan B:* pedir al admin que apruebe el Client ID. *Plan C:* desarrollar contra
  una cuenta Gmail personal con un curso de prueba propio, y dejar la cuenta escolar
  para después.
- 🟡 **En estado *Testing*, el refresh token caduca cada 7 días.** Vas a tener que
  re-autenticar semanalmente. Es molesto pero normal; se resuelve publicando la app
  (proceso de verificación de Google) o conviviendo con ello.

**Entregable:** `taitai auth` imprime la lista de tus cursos reales.

---

## Fase 2 — Ingesta: traer todo de Classroom 📥

**Objetivo:** una copia local completa y actualizable.

- `courses.list` → cursos activos
- `courses.courseWork.list` → título, descripción, fecha y hora límite, puntos,
  materiales adjuntos, tipo de entrega
- `courses.announcements.list` → avisos, con fecha
- `courses.courseWorkMaterials.list` → material de apoyo
- `studentSubmissions.list` → estado de cada entrega tuya
- Esquema SQLite: `cursos`, `tareas`, `avisos`, `materiales`, `entregas`, `sync_log`
- Sync incremental usando `updateTime` (no re-descargar todo cada vez)
- Manejo de paginación y de rate limits

**Entregable:** `taitai sync` y `taitai list --pendientes`

---

## Fase 3 — Vista unificada 🗂️

**Objetivo:** ver todo de un vistazo, sin abrir Classroom.

- CLI primero: tabla ordenada por urgencia, con código de color por fecha límite
- Luego dashboard web local (FastAPI en `localhost`): tarjeta por tarea con
  instrucciones completas, adjuntos y días restantes
- Vista separada de avisos recientes
- Filtros: por curso, por urgencia, por estado

**Entregable:** `taitai serve` abre el dashboard en el navegador.

---

## Fase 4 — Triage: ¿qué puede hacer la IA? 🚦

> **El corazón del proyecto.** Es lo que diferencia esto de un lector de Classroom.

**Objetivo:** que cada tarea llegue clasificada, con razón explícita.

Claude recibe: título + instrucciones + materiales adjuntos + tipo de entrega +
puntos + curso. Devuelve una clasificación estructurada:

### 🟢 VERDE — la IA puede hacerla casi completa
Ensayos y redacciones · resúmenes de lectura · reportes escritos · análisis de texto ·
investigación documental · traducciones · ejercicios de programación ·
cuestionarios de respuesta escrita · mapas conceptuales en texto

### 🟡 AMARILLO — borrador sí, pero necesita algo tuyo
Requiere datos de tu laboratorio o de tu clase · pide experiencia u opinión personal ·
depende de apuntes que solo tú tienes · formato específico que el profesor explicó
de viva voz · necesita una fuente que no está adjunta

→ En estos casos la app **primero te hace las preguntas** que necesita responder,
y con tus respuestas redacta.

### 🔴 ROJO — 100% tuya
Exposición oral · examen presencial o cronometrado · trabajo en equipo ·
dibujo, maqueta o manualidad · experimento físico · evaluación de participación ·
entrega en una plataforma externa a Classroom

### Además devuelve
- **Esfuerzo estimado** (minutos de tu tiempo real)
- **Qué le falta** para poder avanzar
- **Confianza** en la clasificación (para que no confíes ciegamente en un 🟢 dudoso)

**Entregable:** `taitai triage` → tabla con semáforo y razón por tarea.

---

## Fase 5 — Motor de redacción ✍️

**Objetivo:** del triage al borrador terminado.

1. **Construir contexto:** instrucciones de Classroom + contenido de los archivos
   adjuntos (leer Google Docs, PDFs y Slides vinculados) + avisos relacionados
2. **Redactar** con Claude, respetando extensión, formato y rúbrica si existe
3. **Publicar** el borrador como Google Doc en tu Drive, en
   `TaiTai / [Curso] / [Tarea]`
4. Para 🟡: primero generar las preguntas, esperar tus respuestas, luego redactar

**Entregable:** `taitai draft <id-tarea>` devuelve el link al Google Doc.

---

## Fase 6 — Revisión y entrega ✅

**Objetivo:** cerrar el ciclo — pero con tus manos en el volante.

- El dashboard muestra el borrador junto a las instrucciones originales
- Tú editas directamente en Google Docs
- Botón **"Adjuntar a Classroom"** → `modifyAttachments`
- Botón **"Entregar"** → `turnIn`, con confirmación explícita y un resumen de
  qué se va a entregar. **Nunca automático, nunca en lote.**

**Entregable:** una tarea recorrida de punta a punta: sync → triage → borrador → entrega.

---

## Fase 7 — Que corra solo 🔁

**Objetivo:** dejar de acordarte de abrirlo.

- Sync programado (launchd en macOS, o tarea programada de Claude Code)
- Notificaciones: tarea nueva, fecha límite en menos de 48h, aviso nuevo
- Resumen diario: qué vence, qué está listo para revisar, qué está trabado
- Triage automático de cada tarea nueva al llegar

**Entregable:** no tienes que abrir la app para enterarte de nada.

---

# Riesgos del proyecto

| # | Riesgo | Probabilidad | Mitigación |
|---|---|---|---|
| 1 | La cuenta escolar bloquea apps de terceros | Alta | Plan B: aprobación del admin. Plan C: desarrollar con Gmail personal |
| 2 | Token caduca cada 7 días en modo Testing | Alta | Convivir, o publicar la app |
| 3 | Instrucciones incompletas en Classroom (se dijeron en clase) | Alta | El triage lo detecta y marca 🟡 pidiéndote el dato |
| 4 | Quizzes de Google Forms no exponen detalle por API | Media | Marcarlos 🔴 y avisarte |
| 5 | Cambios de la API de Classroom | Baja | Fijar versiones en `requirements.txt` |

---

# Prompt para continuar

Copia esto al empezar una sesión nueva:

```
Proyecto TaiTai Tareas (~/Documents/Tareas-taitai).
Lee PLAN.md para el contexto completo.

Vamos por la Fase [N]: [nombre].

Contexto de dónde quedamos: [qué funciona ya / qué falló / qué decidimos].

Quiero que: [objetivo concreto de esta sesión].
```

---

# Decisiones tomadas

- ✅ **Fase 1 contra la cuenta escolar directo.** Atacamos el riesgo más grande
      primero: si el administrador bloquea apps de terceros, nos enteramos antes
      de construir nada encima.
- ✅ **Repo público** por ahora. ⚠️ Revisar antes de la Fase 2: a partir de ahí
      el proyecto maneja info de tus cursos. Los secretos ya están cubiertos por
      `.gitignore`, pero la base de datos local y los borradores nunca deben
      commitearse.

# Decisiones abiertas

- [ ] ¿Dashboard web desde la Fase 3, o aguantamos en CLI hasta la Fase 5?
- [ ] Si la cuenta escolar está bloqueada: ¿pedimos aprobación al admin o nos
      movemos a un curso de prueba con Gmail personal?
