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

🏗️ **Fase 0** — Cimientos. Ver el plan completo en [PLAN.md](PLAN.md).

## Stack

- Python 3.11+
- `google-api-python-client` + `google-auth-oauthlib` — Classroom y Drive
- `anthropic` — Claude para triage y redacción
- SQLite — caché local
- FastAPI — dashboard local (fase 3+)

## Empezar

Todavía no hay código. El siguiente paso es la **Fase 1: OAuth con Google**.
El plan fase por fase está en [PLAN.md](PLAN.md).
