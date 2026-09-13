"""Línea de comandos de TaiTai Tareas."""

import argparse
import sys

from googleapiclient.errors import HttpError

from . import auth, classroom


def cmd_auth(args) -> int:
    """Autoriza con Google y muestra tus cursos."""
    creds = auth.obtener_credenciales(forzar_login=args.forzar)
    servicio = auth.servicio_classroom(creds)

    cursos = classroom.listar_cursos(servicio)
    if not cursos:
        print("Autorización correcta, pero no tienes cursos activos.")
        print("Si esperabas ver cursos, revisa que autorizaste con la cuenta correcta.")
        return 0

    print(f"\n✓ Autorizado. {len(cursos)} curso(s) activo(s):\n")
    for c in cursos:
        try:
            n = classroom.contar_tareas(servicio, c["id"])
            tareas = f"{n} tarea(s)"
        except HttpError:
            tareas = "sin acceso a tareas"
        print(f"  · {c['name']}")
        print(f"      id: {c['id']}  —  {tareas}")

    print("\nToken guardado. La próxima vez no vuelve a pedir autorización.")
    return 0


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(
        prog="taitai", description="Asistente de Google Classroom"
    )
    sub = parser.add_subparsers(dest="comando", required=True)

    p = sub.add_parser("auth", help="autorizar con Google y listar tus cursos")
    p.add_argument(
        "--forzar", action="store_true", help="reautorizar aunque haya token guardado"
    )
    p.set_defaults(func=cmd_auth)

    args = parser.parse_args(argv)

    try:
        return args.func(args)
    except auth.FaltanCredenciales as e:
        print(f"\n✗ {e}\n", file=sys.stderr)
        return 1
    except HttpError as e:
        print(f"\n✗ Google rechazó la petición: {e}\n", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
