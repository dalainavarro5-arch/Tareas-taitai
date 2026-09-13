"""Línea de comandos de TaiTai Tareas."""

from __future__ import annotations

import argparse
import sys
import textwrap

from googleapiclient.errors import HttpError

from . import auth, classroom, store, sync


def _urgencia(dias: float | None) -> tuple[str, str]:
    """Semáforo y texto legible para una fecha límite."""
    if dias is None:
        return "⚪", "sin fecha"
    if dias < 0:
        return "🔴", f"vencida hace {abs(dias):.0f}d"
    if dias < 1:
        return "🔴", f"vence en {dias * 24:.0f}h"
    if dias < 3:
        return "🟠", f"{dias:.0f} días"
    if dias < 8:
        return "🟡", f"{dias:.0f} días"
    return "⚪", f"{dias:.0f} días"


def _curso_corto(nombre: str, ancho: int = 30) -> str:
    """Los nombres de Classroom traen espacios dobles y el horario pegado."""
    limpio = " ".join(nombre.split())
    return limpio if len(limpio) <= ancho else limpio[: ancho - 1] + "…"


def cmd_auth(args) -> int:
    creds = auth.obtener_credenciales(forzar_login=args.forzar)
    cursos = classroom.listar_cursos(auth.servicio_classroom(creds))

    if not cursos:
        print("Autorización correcta, pero no tienes cursos activos.")
        print("Revisa que hayas autorizado con la cuenta correcta.")
        return 0

    print(f"\n✓ Autorizado. {len(cursos)} curso(s) activo(s):\n")
    for c in cursos:
        print(f"  · {c['name']}")
    print("\nToken guardado. Ahora corre:  taitai sync")
    return 0


def cmd_sync(args) -> int:
    servicio = auth.servicio_classroom()
    con = store.conectar()

    print("Sincronizando con Classroom...\n")
    r = sync.sincronizar(servicio, con, al_avanzar=lambda n: print(f"  · {n}"))

    print(f"\n✓ Listo en {r['segundos']}s")
    print(f"  {r['cursos']} cursos · {r['tareas']} tareas · "
          f"{r['avisos']} avisos · {r['entregas']} entregas")

    if r["errores"]:
        print("\n⚠️  Algunas partes no se pudieron leer:")
        for e in r["errores"]:
            print(f"  · {e}")

    print(f"\nGuardado en {store.BASE.name}. Ahora corre:  taitai pendientes")
    return 0


def cmd_pendientes(args) -> int:
    con = store.conectar()

    if not store.ultima_sync(con):
        print("Todavía no has sincronizado. Corre primero:  taitai sync")
        return 1

    tareas = store.tareas_pendientes(con, dias=args.dias)
    if not tareas:
        print("✓ No tienes tareas pendientes." if args.dias is None
              else f"✓ Nada pendiente en los próximos {args.dias:.0f} días.")
        return 0

    print(f"\n{len(tareas)} tarea(s) pendiente(s), de la más urgente a la menos:\n")

    for t in tareas:
        dias = store.dias_restantes(t["vence_utc"])
        icono, cuando = _urgencia(dias)
        local = store.a_local(t["vence_utc"])
        fecha = local.strftime("%d %b %H:%M") if local else "sin fecha"
        puntos = f"  ·  {t['puntos']:.0f} pts" if t["puntos"] else ""

        print(f"  {icono} {t['titulo']}")
        print(f"       {_curso_corto(t['curso'])}  ·  {fecha}  ({cuando}){puntos}")

        if args.detalle and t["descripcion"]:
            for linea in textwrap.wrap(t["descripcion"].strip(), 72)[:4]:
                print(f"       │ {linea}")

    print()
    return 0


def cmd_avisos(args) -> int:
    con = store.conectar()
    avisos = store.avisos_recientes(con, limite=args.limite)

    if not avisos:
        print("No hay avisos guardados. ¿Ya corriste  taitai sync?")
        return 0

    print(f"\nÚltimos {len(avisos)} aviso(s):\n")
    for a in avisos:
        fecha = store.a_local(a["creado"])
        print(f"  {_curso_corto(a['curso'], 40)}  ·  {fecha.strftime('%d %b %H:%M') if fecha else '—'}")
        for linea in textwrap.wrap(a["texto"].strip(), 72)[:5]:
            print(f"    {linea}")
        print()
    return 0


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(
        prog="taitai", description="Asistente de Google Classroom"
    )
    sub = parser.add_subparsers(dest="comando", required=True)

    p = sub.add_parser("auth", help="autorizar con Google")
    p.add_argument("--forzar", action="store_true", help="reautorizar desde cero")
    p.set_defaults(func=cmd_auth)

    p = sub.add_parser("sync", help="bajar todo de Classroom a la base local")
    p.set_defaults(func=cmd_sync)

    p = sub.add_parser("pendientes", help="tus tareas sin entregar, por urgencia")
    p.add_argument("--dias", type=float, help="solo las que vencen en N días")
    p.add_argument("--detalle", action="store_true", help="incluir instrucciones")
    p.set_defaults(func=cmd_pendientes)

    p = sub.add_parser("avisos", help="últimos avisos de tus profesores")
    p.add_argument("--limite", type=int, default=10)
    p.set_defaults(func=cmd_avisos)

    args = parser.parse_args(argv)

    try:
        return args.func(args)
    except auth.FaltanCredenciales as e:
        print(f"\n✗ {e}\n", file=sys.stderr)
        return 1
    except HttpError as e:
        print(f"\n✗ Google rechazó la petición: {e}\n", file=sys.stderr)
        return 1
    except KeyboardInterrupt:
        print("\nCancelado.", file=sys.stderr)
        return 130


if __name__ == "__main__":
    raise SystemExit(main())
