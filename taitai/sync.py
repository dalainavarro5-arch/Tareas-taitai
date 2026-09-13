"""Sincronización: de Classroom a la base local."""

from __future__ import annotations

import time

from googleapiclient.errors import HttpError

from . import classroom, store


def sincronizar(servicio, con, al_avanzar=None) -> dict:
    """Baja cursos, tareas, avisos y entregas. Devuelve el conteo por tipo.

    Un curso que falle (permisos, profesor que restringió algo) no tumba la
    sincronización completa: se anota el error y seguimos con los demás.
    """
    inicio = time.monotonic()
    conteos = {"cursos": 0, "tareas": 0, "avisos": 0, "entregas": 0}
    errores = []

    cursos = classroom.listar_cursos(servicio)

    for curso in cursos:
        nombre = curso.get("name", curso["id"])
        if al_avanzar:
            al_avanzar(nombre)

        store.guardar_curso(con, curso)
        conteos["cursos"] += 1

        for clave, traer, guardar in (
            ("tareas", classroom.listar_tareas, store.guardar_tarea),
            ("avisos", classroom.listar_avisos, store.guardar_aviso),
            ("entregas", classroom.listar_entregas, store.guardar_entrega),
        ):
            try:
                for item in traer(servicio, curso["id"]):
                    guardar(con, curso["id"], item)
                    conteos[clave] += 1
            except HttpError as e:
                errores.append(f"{nombre} · {clave}: {e.status_code}")

        con.commit()

    segundos = time.monotonic() - inicio
    store.registrar_sync(con, conteos, segundos)
    con.commit()

    conteos["segundos"] = round(segundos, 1)
    conteos["errores"] = errores
    return conteos
