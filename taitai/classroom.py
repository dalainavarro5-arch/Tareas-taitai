"""Lectura de Google Classroom.

Todas las funciones paginan hasta agotar los resultados: Classroom devuelve
como máximo 100 elementos por página y sin esto se perderían tareas en
cursos grandes.
"""

from __future__ import annotations

from googleapiclient.errors import HttpError


def _paginar(metodo, clave: str, **kwargs) -> list[dict]:
    """Recorre todas las páginas de un endpoint y junta los resultados."""
    items, pagina = [], None
    while True:
        r = metodo(pageSize=100, pageToken=pagina, **kwargs).execute()
        items.extend(r.get(clave, []))
        pagina = r.get("nextPageToken")
        if not pagina:
            return items


def listar_cursos(servicio, solo_activos: bool = True) -> list[dict]:
    filtros = {"courseStates": ["ACTIVE"]} if solo_activos else {}
    return _paginar(servicio.courses().list, "courses", **filtros)


def listar_tareas(servicio, id_curso: str) -> list[dict]:
    return _paginar(
        servicio.courses().courseWork().list, "courseWork", courseId=id_curso
    )


def listar_avisos(servicio, id_curso: str) -> list[dict]:
    return _paginar(
        servicio.courses().announcements().list, "announcements", courseId=id_curso
    )


def listar_entregas(servicio, id_curso: str) -> list[dict]:
    """Tus entregas de todo el curso.

    El courseWorkId '-' es un comodín de la API: trae las entregas de todas
    las tareas del curso en una sola llamada, en vez de una por tarea.
    """
    return _paginar(
        servicio.courses().courseWork().studentSubmissions().list,
        "studentSubmissions",
        courseId=id_curso,
        courseWorkId="-",
        userId="me",
    )


def contar_tareas(servicio, id_curso: str) -> int:
    r = servicio.courses().courseWork().list(courseId=id_curso, pageSize=100).execute()
    return len(r.get("courseWork", []))
