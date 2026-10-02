from ipaddress import ip_address
from pathlib import Path
from urllib.parse import urlsplit

from pydantic import BaseModel, ConfigDict, field_validator

from engine.core.fields import ui_field

DEFAULT_BATCH_SIZE = 4
MAX_BATCH_SIZE = 32
DEFAULT_NOTIFICATION_THRESHOLD_SECONDS = 10
MAX_NOTIFICATION_THRESHOLD_SECONDS = 3600
DEFAULT_MODEL_SERVER_URL = "http://127.0.0.1:11434/v1"
DEFAULT_MODEL_NAME = "qwen2.5:7b"
LOCAL_HOST_NAMES = {"localhost"}
WEB_SCHEMES = {"http", "https"}


class SettingsSection(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")


class ModuleSettings(SettingsSection):
    """Base class for the settings section a module may declare."""


class GeneralSettings(SettingsSection):
    oda_converter_path: Path | None = ui_field(
        "file",
        label="ODA File Converter",
        default=None,
        description="Chemin de ODAFileConverter.exe, nécessaire pour lire les fichiers DWG.",
    )
    cache_folder: Path | None = ui_field(
        "folder",
        label="Dossier de cache",
        default=None,
        description="Laisser vide pour utiliser le dossier de cache de l'application.",
    )
    batch_size: int = ui_field(
        "number",
        label="Fichiers traités en parallèle",
        default=DEFAULT_BATCH_SIZE,
        ge=1,
        le=MAX_BATCH_SIZE,
    )
    notification_threshold_seconds: int = ui_field(
        "number",
        label="Notifier après (secondes)",
        default=DEFAULT_NOTIFICATION_THRESHOLD_SECONDS,
        description=(
            "Une notification système signale la fin des traitements plus longs que cette durée, "
            "ou de tout traitement terminé pendant que l'application est en arrière-plan."
        ),
        ge=0,
        le=MAX_NOTIFICATION_THRESHOLD_SECONDS,
    )


class AssistantSettings(SettingsSection):
    model_server_url: str = ui_field(
        "text",
        label="Serveur du modèle",
        default=DEFAULT_MODEL_SERVER_URL,
        description=(
            "Adresse de l'API compatible OpenAI du modèle local (Ollama, LM Studio, llama.cpp). "
            "Elle doit désigner ce poste : aucune donnée ne quitte la machine."
        ),
    )
    model: str = ui_field(
        "text",
        label="Modèle",
        default=DEFAULT_MODEL_NAME,
        description="Nom du modèle installé, par exemple qwen2.5:7b pour Ollama.",
        min_length=1,
    )

    @field_validator("model_server_url")
    @classmethod
    def _must_stay_on_this_computer(cls, url: str) -> str:
        parts = urlsplit(url.strip())
        if parts.scheme not in WEB_SCHEMES or not _is_loopback(parts.hostname):
            raise ValueError(
                "l'adresse doit commencer par http:// et désigner ce poste (localhost ou 127.0.0.1)"
            )
        return url.strip().rstrip("/")


def _is_loopback(host: str | None) -> bool:
    if host is None:
        return False
    if host.lower() in LOCAL_HOST_NAMES:
        return True
    try:
        return ip_address(host).is_loopback
    except ValueError:
        return False
