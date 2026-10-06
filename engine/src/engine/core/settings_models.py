from ipaddress import ip_address
from pathlib import Path
from urllib.parse import urlsplit

from pydantic import BaseModel, ConfigDict, field_validator

from engine.core.fields import ui_field

DEFAULT_BATCH_SIZE = 4
MAX_BATCH_SIZE = 32
DEFAULT_NOTIFICATION_THRESHOLD_SECONDS = 10
DEFAULT_MINUTES_SAVED_PER_FILE = 5
MAX_MINUTES_SAVED_PER_FILE = 600
MAX_NOTIFICATION_THRESHOLD_SECONDS = 3600
DEFAULT_MODEL_SERVER_URL = "http://127.0.0.1:11434/v1"
DEFAULT_MODEL_NAME = "qwen3.5:9b"
LOCAL_HOST_NAMES = {"localhost"}
DEFAULT_MAIL_TENANT = "common"
DEFAULT_MAIL_LOOKBACK_DAYS = 90
MAX_MAIL_LOOKBACK_DAYS = 3650
DEFAULT_MAX_CONVERSATIONS = 500
MAX_CONVERSATIONS = 20000
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
    usage_counters: bool = ui_field(
        "bool",
        label="Compteurs d'utilisation",
        default=True,
        description=(
            "Compte les traitements et fichiers sur ce poste (Paramètres → À propos). "
            "Rien n'est envoyé."
        ),
    )
    minutes_saved_per_file: int = ui_field(
        "number",
        label="Minutes gagnées par fichier",
        default=DEFAULT_MINUTES_SAVED_PER_FILE,
        description=(
            "Estimation utilisée par les compteurs : temps manuel évité pour chaque fichier traité."
        ),
        ge=0,
        le=MAX_MINUTES_SAVED_PER_FILE,
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
        description="Nom du modèle installé, par exemple qwen3.5:9b pour Ollama.",
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


class MailSettings(SettingsSection):
    client_id: str = ui_field(
        "text",
        label="Identifiant d'application (Entra ID)",
        default="",
        description=(
            "Client ID de l'application inscrite dans Microsoft Entra ID pour lire la boîte "
            "Exchange / Microsoft 365. Vide : la fonctionnalité Courriels est désactivée."
        ),
    )
    tenant: str = ui_field(
        "text",
        label="Tenant",
        default=DEFAULT_MAIL_TENANT,
        description="« common » pour tout compte professionnel, ou l'identifiant du tenant.",
        min_length=1,
    )
    local_folder: Path | None = ui_field(
        "folder",
        label="Dossier des conversations",
        default=None,
        description=(
            "Laisser vide pour conserver les conversations dans le dossier de l'application."
        ),
    )
    lookback_days: int = ui_field(
        "number",
        label="Récupérer les messages des derniers (jours)",
        default=DEFAULT_MAIL_LOOKBACK_DAYS,
        ge=1,
        le=MAX_MAIL_LOOKBACK_DAYS,
    )
    max_conversations: int = ui_field(
        "number",
        label="Conversations conservées au maximum",
        default=DEFAULT_MAX_CONVERSATIONS,
        description="Au-delà, les conversations les plus anciennes sont retirées du dossier local.",
        ge=1,
        le=MAX_CONVERSATIONS,
    )
