from pathlib import Path

from pydantic import BaseModel, ConfigDict

from engine.core.fields import ui_field

DEFAULT_BATCH_SIZE = 4
MAX_BATCH_SIZE = 32
DEFAULT_NOTIFICATION_THRESHOLD_SECONDS = 10
MAX_NOTIFICATION_THRESHOLD_SECONDS = 3600


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
