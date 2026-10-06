from ipaddress import ip_address
from pathlib import Path
from typing import Literal
from urllib.parse import urlsplit

from pydantic import BaseModel, ConfigDict, field_validator

from engine.core.fields import ui_field
from engine.core.messages import t

DEFAULT_BATCH_SIZE = 4
MAX_BATCH_SIZE = 32
DEFAULT_NOTIFICATION_THRESHOLD_SECONDS = 10
DEFAULT_MINUTES_SAVED_PER_FILE = 5
MAX_MINUTES_SAVED_PER_FILE = 600
MAX_NOTIFICATION_THRESHOLD_SECONDS = 3600
DEFAULT_MODEL_SERVER_URL = "http://127.0.0.1:11434/v1"
DEFAULT_MODEL_NAME = "qwen3.5:9b"
LOCAL_HOST_NAMES = {"localhost"}
Language = Literal["fr", "en"]
DEFAULT_LANGUAGE: Language = "fr"
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
    language: Language = ui_field(
        "enum",
        label=t("general.language.label"),
        default=DEFAULT_LANGUAGE,
        description=t("general.language.description"),
    )
    oda_converter_path: Path | None = ui_field(
        "file",
        label=t("general.oda_converter_path.label"),
        default=None,
        description=t("general.oda_converter_path.description"),
    )
    cache_folder: Path | None = ui_field(
        "folder",
        label=t("general.cache_folder.label"),
        default=None,
        description=t("general.cache_folder.description"),
    )
    batch_size: int = ui_field(
        "number",
        label=t("general.batch_size.label"),
        default=DEFAULT_BATCH_SIZE,
        ge=1,
        le=MAX_BATCH_SIZE,
    )
    notification_threshold_seconds: int = ui_field(
        "number",
        label=t("general.notification_threshold_seconds.label"),
        default=DEFAULT_NOTIFICATION_THRESHOLD_SECONDS,
        description=t("general.notification_threshold_seconds.description"),
        ge=0,
        le=MAX_NOTIFICATION_THRESHOLD_SECONDS,
    )
    usage_counters: bool = ui_field(
        "bool",
        label=t("general.usage_counters.label"),
        default=True,
        description=t("general.usage_counters.description"),
    )
    minutes_saved_per_file: int = ui_field(
        "number",
        label=t("general.minutes_saved_per_file.label"),
        default=DEFAULT_MINUTES_SAVED_PER_FILE,
        description=t("general.minutes_saved_per_file.description"),
        ge=0,
        le=MAX_MINUTES_SAVED_PER_FILE,
    )


class AssistantSettings(SettingsSection):
    model_server_url: str = ui_field(
        "text",
        label=t("assistant.model_server_url.label"),
        default=DEFAULT_MODEL_SERVER_URL,
        description=t("assistant.model_server_url.description"),
    )
    model: str = ui_field(
        "text",
        label=t("assistant.model.label"),
        default=DEFAULT_MODEL_NAME,
        description=t("assistant.model.description"),
        min_length=1,
    )

    @field_validator("model_server_url")
    @classmethod
    def _must_stay_on_this_computer(cls, url: str) -> str:
        parts = urlsplit(url.strip())
        if parts.scheme not in WEB_SCHEMES or not _is_loopback(parts.hostname):
            raise ValueError(t("assistant.model_server_url.invalid"))
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
        label=t("mail.client_id.label"),
        default="",
        description=t("mail.client_id.description"),
    )
    tenant: str = ui_field(
        "text",
        label=t("mail.tenant.label"),
        default=DEFAULT_MAIL_TENANT,
        description=t("mail.tenant.description"),
        min_length=1,
    )
    local_folder: Path | None = ui_field(
        "folder",
        label=t("mail.local_folder.label"),
        default=None,
        description=t("mail.local_folder.description"),
    )
    lookback_days: int = ui_field(
        "number",
        label=t("mail.lookback_days.label"),
        default=DEFAULT_MAIL_LOOKBACK_DAYS,
        ge=1,
        le=MAX_MAIL_LOOKBACK_DAYS,
    )
    max_conversations: int = ui_field(
        "number",
        label=t("mail.max_conversations.label"),
        default=DEFAULT_MAX_CONVERSATIONS,
        description=t("mail.max_conversations.description"),
        ge=1,
        le=MAX_CONVERSATIONS,
    )
