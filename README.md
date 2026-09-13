# TaiTai Tareas

Asistente personal que se conecta a **Google Classroom** para centralizar tareas,
instrucciones y avisos — y que además **clasifica qué tareas puede resolver la IA**
y redacta los borradores en **Google Drive**.

No es un bot que entrega tareas solo. Es un copiloto: sincroniza, ordena, triagea,
redacta — y tú revisas y decides qué entregar.

## Qué hace

| Capacidad | Descripción |
|---|---|
| 📥 Sincroniza | Cursos, tareas, fechas límite, materiales y anuncios de Classroom |
| 🗂️ Centraliza | Una sola vista ordenada por urgencia, sin entrar curso por curso |
| 🚦 Triagea | Semáforo: qué puede hacer la IA sola, qué necesita tu input, qué es 100% tuyo |
| ✍️ Redacta | Genera el borrador como Google Doc en tu Drive, con el contexto de la tarea |
| ✅ Prepara la entrega | Adjunta a Classroom — la entrega final siempre la confirmas tú |

## Estado

📥 **Fase 2 completa** — autenticación y sincronización funcionando contra
Classroom real. Siguiente: Fase 4, el triage. Ver [PLAN.md](PLAN.md).

```
taitai auth        autorizar con Google
taitai sync        bajar todo a la base local
taitai pendientes  tus tareas sin entregar, por urgencia
taitai avisos      últimos avisos de tus profesores
```

## Stack

- Python 3.11+
- `google-api-python-client` + `google-auth-oauthlib` — Classroom y Drive
- `anthropic` — Claude para triage y redacción
- SQLite — caché local
- FastAPI — dashboard local (fase 3+)

## Empezar

Necesitas `credentials.json` de Google Cloud — la guía paso a paso está en
[docs/SETUP-GOOGLE-CLOUD.md](docs/SETUP-GOOGLE-CLOUD.md).

```bash
python3 -m venv .venv
./.venv/bin/pip install -r requirements.txt
./.venv/bin/python -m taitai auth
```

La primera vez abre el navegador para que autorices. Después guarda el token
y ya no vuelve a preguntar.

### Nota sobre Python

Este proyecto corre con el Python 3.9 del sistema, que ya está fuera de soporte.
Por eso `cryptography` está fijado en la 44.0.3 (las versiones nuevas ya no
publican binarios para 3.9). Funciona bien, pero si algún día instalas un Python
3.11+, se puede quitar ese tope en `requirements.txt`.
