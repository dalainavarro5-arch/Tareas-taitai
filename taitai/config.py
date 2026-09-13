"""Rutas y permisos del proyecto."""

from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent

# Credenciales OAuth descargadas de Google Cloud. Nunca se commitean.
CREDENCIALES = RAIZ / "credentials.json"

# Token de sesión, generado en la primera autorización. Tampoco se commitea.
TOKEN = RAIZ / "token.json"

# Permisos que le pedimos a Google. Mínimo privilegio:
# solo lectura salvo donde necesitamos escribir.
SCOPES = [
    # Leer la lista de tus cursos
    "https://www.googleapis.com/auth/classroom.courses.readonly",
    # Leer tus tareas y, más adelante, adjuntar y entregar
    "https://www.googleapis.com/auth/classroom.coursework.me",
    # Leer los avisos del profesor
    "https://www.googleapis.com/auth/classroom.announcements.readonly",
    # Leer el material de apoyo publicado
    "https://www.googleapis.com/auth/classroom.courseworkmaterials.readonly",
    # Saber si una tarea está entregada, atrasada o calificada
    "https://www.googleapis.com/auth/classroom.student-submissions.me.readonly",
    # Crear y editar SOLO los documentos que genere esta app
    "https://www.googleapis.com/auth/drive.file",
]
