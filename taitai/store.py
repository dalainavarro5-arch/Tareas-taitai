"""Base de datos local (SQLite).

Guarda todo lo que viene de Classroom para que la app sirva sin internet
y para tener de dónde partir en el triage.
"""

from __future__ import annotations

import json
import sqlite3
from datetime import datetime, timedelta, timezone
from pathlib import Path

from . import config

BASE = config.RAIZ / "taitai.db"

ESQUEMA = """
CREATE TABLE IF NOT EXISTS cursos (
    id           TEXT PRIMARY KEY,
    nombre       TEXT NOT NULL,
    seccion      TEXT,
    descripcion  TEXT,
    enlace       TEXT,
    actualizado  TEXT
);

CREATE TABLE IF NOT EXISTS tareas (
    id           TEXT PRIMARY KEY,
    curso_id     TEXT NOT NULL,
    titulo       TEXT NOT NULL,
    descripcion  TEXT,
    tipo         TEXT,
    puntos       REAL,
    vence_utc    TEXT,           -- ISO 8601 en UTC, o NULL si no tiene fecha
    enlace       TEXT,
    materiales   TEXT,           -- JSON crudo de Classroom
    actualizado  TEXT,
    FOREIGN KEY (curso_id) REFERENCES cursos(id)
);

CREATE TABLE IF NOT EXISTS avisos (
    id           TEXT PRIMARY KEY,
    curso_id     TEXT NOT NULL,
    texto        TEXT,
    enlace       TEXT,
    materiales   TEXT,
    creado       TEXT,
    actualizado  TEXT,
    FOREIGN KEY (curso_id) REFERENCES cursos(id)
);

CREATE TABLE IF NOT EXISTS entregas (
    id           TEXT PRIMARY KEY,
    tarea_id     TEXT NOT NULL,
    curso_id     TEXT NOT NULL,
    estado       TEXT,           -- NEW, CREATED, TURNED_IN, RETURNED, RECLAIMED_BY_STUDENT
    atrasada     INTEGER,
    calificacion REAL,
    enlace       TEXT,
    actualizado  TEXT
);

CREATE TABLE IF NOT EXISTS sincronizaciones (
    id        INTEGER PRIMARY KEY AUTOINCREMENT,
    momento   TEXT,
    cursos    INTEGER,
    tareas    INTEGER,
    avisos    INTEGER,
    entregas  INTEGER,
    segundos  REAL
);

CREATE INDEX IF NOT EXISTS idx_tareas_curso  ON tareas(curso_id);
CREATE INDEX IF NOT EXISTS idx_tareas_vence  ON tareas(vence_utc);
CREATE INDEX IF NOT EXISTS idx_entregas_tarea ON entregas(tarea_id);
CREATE INDEX IF NOT EXISTS idx_avisos_curso  ON avisos(curso_id);
"""


def conectar(ruta: Path = BASE) -> sqlite3.Connection:
    con = sqlite3.connect(ruta)
    con.row_factory = sqlite3.Row
    con.execute("PRAGMA foreign_keys = ON")
    con.executescript(ESQUEMA)
    return con


# --- Conversión de fechas -------------------------------------------------

def fecha_limite(tarea: dict) -> str | None:
    """Combina dueDate + dueTime de Classroom en un ISO 8601 UTC.

    Classroom entrega la fecha y la hora por separado, ambas en UTC. Cuando el
    profesor pone fecha sin hora, la API omite dueTime: ahí asumimos el final
    del día, que es como lo muestra Classroom.
    """
    d = tarea.get("dueDate")
    if not d:
        return None

    t = tarea.get("dueTime") or {"hours": 23, "minutes": 59}
    return datetime(
        d["year"], d["month"], d["day"],
        t.get("hours", 0), t.get("minutes", 0),
        tzinfo=timezone.utc,
    ).isoformat()


def _parsear(iso: str | None) -> datetime | None:
    """Lee un timestamp ISO, venga de Classroom o de nosotros.

    Classroom manda RFC 3339 terminado en 'Z' ("2026-09-11T17:58:34.570Z").
    fromisoformat solo aprende a leer esa 'Z' en Python 3.11, y aquí corremos
    3.9, así que la traducimos al equivalente que sí entiende.
    """
    if not iso:
        return None
    if iso.endswith("Z"):
        iso = iso[:-1] + "+00:00"
    try:
        fecha = datetime.fromisoformat(iso)
    except ValueError:
        return None
    # Sin zona horaria explícita, Classroom siempre habla en UTC.
    return fecha if fecha.tzinfo else fecha.replace(tzinfo=timezone.utc)


def a_local(iso_utc: str | None) -> datetime | None:
    """Pasa un timestamp UTC a la hora local de esta máquina."""
    fecha = _parsear(iso_utc)
    return fecha.astimezone() if fecha else None


def dias_restantes(iso_utc: str | None) -> float | None:
    fecha = _parsear(iso_utc)
    if not fecha:
        return None
    return (fecha - datetime.now(timezone.utc)).total_seconds() / 86400


# --- Escritura ------------------------------------------------------------

def guardar_curso(con, c: dict) -> None:
    con.execute(
        """INSERT INTO cursos (id, nombre, seccion, descripcion, enlace, actualizado)
           VALUES (?,?,?,?,?,?)
           ON CONFLICT(id) DO UPDATE SET
             nombre=excluded.nombre, seccion=excluded.seccion,
             descripcion=excluded.descripcion, enlace=excluded.enlace,
             actualizado=excluded.actualizado""",
        (c["id"], c.get("name", ""), c.get("section"), c.get("descriptionHeading"),
         c.get("alternateLink"), c.get("updateTime")),
    )


def guardar_tarea(con, curso_id: str, t: dict) -> None:
    con.execute(
        """INSERT INTO tareas (id, curso_id, titulo, descripcion, tipo, puntos,
                               vence_utc, enlace, materiales, actualizado)
           VALUES (?,?,?,?,?,?,?,?,?,?)
           ON CONFLICT(id) DO UPDATE SET
             titulo=excluded.titulo, descripcion=excluded.descripcion,
             tipo=excluded.tipo, puntos=excluded.puntos,
             vence_utc=excluded.vence_utc, enlace=excluded.enlace,
             materiales=excluded.materiales, actualizado=excluded.actualizado""",
        (t["id"], curso_id, t.get("title", ""), t.get("description"),
         t.get("workType"), t.get("maxPoints"), fecha_limite(t),
         t.get("alternateLink"), json.dumps(t.get("materials", [])),
         t.get("updateTime")),
    )


def guardar_aviso(con, curso_id: str, a: dict) -> None:
    con.execute(
        """INSERT INTO avisos (id, curso_id, texto, enlace, materiales, creado, actualizado)
           VALUES (?,?,?,?,?,?,?)
           ON CONFLICT(id) DO UPDATE SET
             texto=excluded.texto, enlace=excluded.enlace,
             materiales=excluded.materiales, actualizado=excluded.actualizado""",
        (a["id"], curso_id, a.get("text"), a.get("alternateLink"),
         json.dumps(a.get("materials", [])), a.get("creationTime"),
         a.get("updateTime")),
    )


def guardar_entrega(con, curso_id: str, e: dict) -> None:
    con.execute(
        """INSERT INTO entregas (id, tarea_id, curso_id, estado, atrasada,
                                 calificacion, enlace, actualizado)
           VALUES (?,?,?,?,?,?,?,?)
           ON CONFLICT(id) DO UPDATE SET
             estado=excluded.estado, atrasada=excluded.atrasada,
             calificacion=excluded.calificacion, actualizado=excluded.actualizado""",
        (e["id"], e.get("courseWorkId"), curso_id, e.get("state"),
         1 if e.get("late") else 0, e.get("assignedGrade"),
         e.get("alternateLink"), e.get("updateTime")),
    )


def registrar_sync(con, conteos: dict, segundos: float) -> None:
    con.execute(
        """INSERT INTO sincronizaciones (momento, cursos, tareas, avisos, entregas, segundos)
           VALUES (?,?,?,?,?,?)""",
        (datetime.now(timezone.utc).isoformat(), conteos.get("cursos", 0),
         conteos.get("tareas", 0), conteos.get("avisos", 0),
         conteos.get("entregas", 0), round(segundos, 2)),
    )


# --- Lectura --------------------------------------------------------------

# Una tarea cuenta como pendiente si no la has entregado ni te la devolvieron.
# Si no hay fila en `entregas` (LEFT JOIN nulo), también cuenta: Classroom
# todavía no registra nada tuyo.
PENDIENTE = "(e.estado IS NULL OR e.estado IN ('NEW', 'CREATED', 'RECLAIMED_BY_STUDENT'))"


def tareas_pendientes(con, dias: float = None) -> list[sqlite3.Row]:
    sql = f"""
        SELECT t.*, c.nombre AS curso, e.estado AS entrega, e.atrasada
        FROM tareas t
        JOIN cursos c ON c.id = t.curso_id
        LEFT JOIN entregas e ON e.tarea_id = t.id
        WHERE {PENDIENTE}
        ORDER BY t.vence_utc IS NULL, t.vence_utc
    """
    filas = con.execute(sql).fetchall()
    if dias is None:
        return filas
    return [f for f in filas
            if (d := dias_restantes(f["vence_utc"])) is not None and d <= dias]


def avisos_recientes(con, limite: int = 10) -> list[sqlite3.Row]:
    return con.execute(
        """SELECT a.*, c.nombre AS curso
           FROM avisos a JOIN cursos c ON c.id = a.curso_id
           WHERE a.texto IS NOT NULL AND TRIM(a.texto) != ''
           ORDER BY a.creado DESC LIMIT ?""",
        (limite,),
    ).fetchall()


def ultima_sync(con) -> sqlite3.Row | None:
    return con.execute(
        "SELECT * FROM sincronizaciones ORDER BY id DESC LIMIT 1"
    ).fetchone()
