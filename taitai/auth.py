"""Autorización con Google.

La primera vez abre el navegador para que autorices la app. Después guarda
un token en disco y lo reutiliza, refrescándolo solo cuando vence.
"""

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build

from . import config


class FaltanCredenciales(Exception):
    """No existe credentials.json."""


def obtener_credenciales(forzar_login: bool = False) -> Credentials:
    """Devuelve credenciales válidas, autorizando en el navegador si hace falta."""
    creds = None

    if config.TOKEN.exists() and not forzar_login:
        creds = Credentials.from_authorized_user_file(str(config.TOKEN), config.SCOPES)

    if creds and creds.valid:
        return creds

    # Token vencido pero renovable: lo refrescamos sin molestar al usuario.
    if creds and creds.expired and creds.refresh_token and not forzar_login:
        try:
            creds.refresh(Request())
            _guardar(creds)
            return creds
        except Exception:
            # El refresh token caduca cada 7 días mientras la app esté en modo
            # "Prueba" en Google Cloud. Cuando pasa, toca reautorizar.
            pass

    if not config.CREDENCIALES.exists():
        raise FaltanCredenciales(
            f"No encuentro {config.CREDENCIALES.name} en la raíz del proyecto.\n"
            "Descárgalo de Google Cloud Console siguiendo docs/SETUP-GOOGLE-CLOUD.md"
        )

    flujo = InstalledAppFlow.from_client_secrets_file(
        str(config.CREDENCIALES), config.SCOPES
    )
    creds = flujo.run_local_server(
        port=0,
        prompt="consent",
        authorization_prompt_message="Abriendo el navegador para autorizar TaiTai...",
        success_message="Listo. Ya puedes cerrar esta pestaña y volver a la terminal.",
    )
    _guardar(creds)
    return creds


def _guardar(creds: Credentials) -> None:
    config.TOKEN.write_text(creds.to_json())
    config.TOKEN.chmod(0o600)


def servicio_classroom(creds: Credentials = None):
    return build("classroom", "v1", credentials=creds or obtener_credenciales())


def servicio_drive(creds: Credentials = None):
    return build("drive", "v3", credentials=creds or obtener_credenciales())
