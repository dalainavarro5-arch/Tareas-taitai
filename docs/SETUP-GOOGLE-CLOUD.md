# Guía detallada: configurar Google Cloud para TaiTai Tareas

> Interfaz verificada en septiembre 2026. Google movió la "Pantalla de consentimiento
> de OAuth" dentro de **Plataforma de Google Auth**, por eso las guías viejas no coinciden.

---

## Paso 0 — Decidir con qué cuenta entrar (lo más importante)

Esta decisión define si te vas a topar con pared o no.

| Cuenta | ¿Puedes crear proyecto? | Tipo de app | Token caduca |
|---|---|---|---|
| 🏫 Escolar, si el admin lo permite | A veces | **Interno** | ❌ Nunca — el mejor caso |
| 👤 Gmail personal | ✅ Siempre | **Externo** | ⚠️ Cada 7 días |
| 🏫 Escolar bloqueada | ❌ No | — | — |

**Estrategia:** intenta primero con la escolar. Si te deja, eliges *Interno* y te
ahorras el problema del token de 7 días para siempre. Si te bloquea, te pasas a
la personal sin perder nada — tu cuenta escolar igual va a poder autorizar la app,
porque **el dueño del proyecto no tiene que ser el mismo que el usuario que autoriza**.

> 💡 Antes de empezar: abre una **ventana de incógnito** e inicia sesión con una sola
> cuenta. El error más común de todos es tener varias sesiones abiertas y que Cloud
> Console use la cuenta equivocada sin avisarte.

---

## Paso 1 — Crear el proyecto

1. Ve a **https://console.cloud.google.com**
2. Si es tu primera vez: acepta los Términos del Servicio.
3. Arriba a la izquierda, junto al logo, hay un **selector de proyecto** (dice
   *"Selecciona un proyecto"* o el nombre de uno). Haz clic.
4. En la ventana emergente, arriba a la derecha: **PROYECTO NUEVO**
5. **Nombre del proyecto:** `taitai-tareas`
6. **Ubicación:** déjala en *Sin organización* (o la de tu escuela, si aparece)
7. **CREAR** — tarda unos 20 segundos
8. Vuelve al selector y **elige `taitai-tareas`**

> ⚠️ **Verifica que arriba diga `taitai-tareas`** antes de seguir. Si dice otro
> proyecto, todo lo que hagas se va a guardar en el lugar equivocado.

### Si aquí te bloquea
- *"No tienes permiso para crear proyectos"* → cuenta escolar restringida. Cambia a tu Gmail personal.
- *Te pide tarjeta de crédito* → puedes saltarlo. La API de Classroom **no requiere facturación**.

---

## Paso 2 — Habilitar las dos APIs

1. Menú ☰ (arriba a la izquierda) → **APIs y servicios** → **Biblioteca**
2. Busca `Google Classroom API` → ábrela → **HABILITAR**
3. Regresa a **Biblioteca**, busca `Google Drive API` → ábrela → **HABILITAR**

Habilitar una API es gratis y no compromete nada.

---

## Paso 3 — Configurar la Plataforma de Google Auth

Aquí es donde la mayoría se pierde: **ya no se llama "Pantalla de consentimiento de OAuth"**.

1. Menú ☰ → **APIs y servicios** → **Plataforma de Google Auth**
   (si ves *Pantalla de consentimiento de OAuth*, es la misma; haz clic)
2. Botón **COMENZAR** / *Get started*

Te va a pedir 4 bloques en una sola página:

| Bloque | Qué poner |
|---|---|
| **Información de la app** | Nombre: `TaiTai Tareas` · Correo de asistencia: el tuyo |
| **Público** (*Audience*) | **Externo** con Gmail personal · **Interno** si tu cuenta escolar te deja |
| **Información de contacto** | Tu correo |
| **Finalizar** | Acepta la Política de Datos de Usuario |

3. **CREAR**

### Externo vs Interno
- **Interno** — solo tu organización escolar. Sin verificación, sin límite de usuarios
  de prueba, y **el token no caduca**. Elígelo si está disponible.
- **Externo** — cualquier cuenta de Google, pero en modo *Prueba* y con el token
  caducando cada 7 días. Es la única opción con Gmail personal.

---

## Paso 4 — Declarar los scopes (Acceso a los datos)

1. Dentro de **Plataforma de Google Auth** → pestaña **Acceso a los datos**
2. **AGREGAR O QUITAR PERMISOS**
3. Se abre un panel lateral. Abajo hay un campo para **pegar scopes manualmente**.
   Pega estos, uno por línea:

```
https://www.googleapis.com/auth/classroom.courses.readonly
https://www.googleapis.com/auth/classroom.coursework.me
https://www.googleapis.com/auth/classroom.announcements.readonly
https://www.googleapis.com/auth/classroom.courseworkmaterials.readonly
https://www.googleapis.com/auth/classroom.student-submissions.me.readonly
https://www.googleapis.com/auth/drive.file
```

4. **AGREGAR A LA TABLA** → **ACTUALIZAR** → **GUARDAR**

> Van a aparecer marcados como *Restringidos* o *Sensibles*. Es normal y esperado.
> En modo *Prueba* funcionan sin verificación de Google.

---

## Paso 5 — Agregarte como usuario de prueba

**Sáltate este paso si elegiste Interno.**

1. Pestaña **Público** (*Audience*)
2. Baja hasta **Usuarios de prueba** → **AGREGAR USUARIOS**
3. Agrega **los dos** correos, uno por línea:
   - `dalainavarro5@gmail.com`
   - tu correo escolar
4. **GUARDAR**

> 🔑 **Este es el paso que hace posible todo.** Aunque el proyecto viva en tu Gmail
> personal, agregar aquí tu correo escolar es lo que le permite autorizar la app
> y leer tus cursos reales.

---

## ⚠️ Antes del Paso 6: llave de API ≠ cliente OAuth

En **Credenciales** hay tres botones juntos y es fácil equivocarse. Para este
proyecto necesitas el segundo:

| | 🔑 Clave de API | ✅ ID de cliente de OAuth |
|---|---|---|
| Responde a | *¿Qué proyecto pregunta?* | *¿Qué **usuario** pregunta?* |
| Sirve para | Datos públicos (Maps, traducción) | Datos privados de una persona |
| Pide permiso al usuario | No | Sí |
| ¿Nos sirve? | ❌ Da `401` en Classroom | ✅ Es lo que necesitamos |

Classroom y Drive **no tienen datos públicos**: para devolver *tus* tareas, la API
necesita saber quién eres. Una clave de API no identifica personas, solo proyectos.

> 🔒 Si por error creaste claves de API: bórralas en **Credenciales → Claves de API
> → ⋮ → Eliminar**. Y nunca pegues una credencial en un chat, correo o repo — si ya
> pasó, bórrala y genera una nueva.

---

## Paso 6 — Crear el cliente OAuth

1. Pestaña **Clientes** (*Clients*) → **CREAR CLIENTE**
2. **Tipo de aplicación:** `App de escritorio` ← debe ser *escritorio*, no *web*
3. **Nombre:** `taitai-cli`
4. **CREAR**
5. Aparece una ventana con el ID y el secreto → **DESCARGAR JSON**

Si cerraste la ventana: en la lista de **Clientes**, el ícono de descarga ⬇️ a la
derecha de tu cliente hace lo mismo.

---

## Paso 7 — Guardar el archivo en el proyecto

El archivo se llama algo como `client_secret_1234-abcd.apps.googleusercontent.com.json`.
Renómbralo a `credentials.json` y muévelo a la carpeta del proyecto:

```bash
mv ~/Downloads/client_secret_*.json ~/Documents/Tareas-taitai/credentials.json
```

Verifica que git lo esté ignorando (debe imprimir la ruta):

```bash
cd ~/Documents/Tareas-taitai && git check-ignore -v credentials.json
```

> 🔒 Ese archivo es una llave. `.gitignore` ya lo bloquea, pero nunca lo pegues en
> un chat, un correo ni un repo.

---

## La primera autorización

Cuando corras la app por primera vez se abre el navegador. Con **Externo** vas a ver
**"Google no ha verificado esta aplicación"**. Es esperado — la app eres tú.

→ **Configuración avanzada** → **Ir a TaiTai Tareas (no seguro)** → acepta los permisos.

---

## Errores comunes

| Error | Causa | Solución |
|---|---|---|
| `access_blocked: no cumple con la política` | El admin escolar bloquea apps de terceros | Pedir aprobación del Client ID al admin, o usar Apps Script |
| `Error 403: org_internal` | Elegiste *Interno* pero autorizas con otra cuenta | Cambia a *Externo*, o autoriza con la cuenta escolar |
| `access_denied` en modo Prueba | No agregaste ese correo como usuario de prueba | Paso 5 |
| No aparece "Pantalla de consentimiento" | UI nueva | Busca **Plataforma de Google Auth** |
| `invalid_client` | Creaste cliente tipo *Web* | Crea uno nuevo tipo **App de escritorio** |
| Token expira cada 7 días | App *Externa* en modo *Prueba* | Es normal. Se quita publicando la app o usando *Interno* |

---

## Si nada de esto funciona

El bloqueo es del administrador de tu escuela, no tuyo. Alternativa sin Cloud Console:
**Google Apps Script** ([script.google.com](https://script.google.com)) administra un
proyecto de Cloud oculto por ti. Ver la discusión en [PLAN.md](../PLAN.md).
