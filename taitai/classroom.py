"""Lectura de Google Classroom."""


def listar_cursos(servicio, solo_activos: bool = True) -> list[dict]:
    """Devuelve tus cursos, paginando hasta traerlos todos."""
    cursos, pagina = [], None
    filtros = {"courseStates": ["ACTIVE"]} if solo_activos else {}

    while True:
        r = servicio.courses().list(pageSize=100, pageToken=pagina, **filtros).execute()
        cursos.extend(r.get("courses", []))
        pagina = r.get("nextPageToken")
        if not pagina:
            break

    return cursos


def contar_tareas(servicio, id_curso: str) -> int:
    """Cuántas tareas publicadas tiene un curso. Prueba de humo de permisos."""
    r = servicio.courses().courseWork().list(courseId=id_curso, pageSize=100).execute()
    return len(r.get("courseWork", []))
