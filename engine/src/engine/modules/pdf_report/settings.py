import re

from pydantic import field_validator

from engine.core.fields import KeyValue, mapping_field, ui_field
from engine.core.naming import FileNameTemplate, file_name_template_field
from engine.core.settings_models import ModuleSettings
from engine.modules.pdf_report.messages import t

PERCENT_MAX = 100
REGEX_PREFIX = "re:"
TAG_PATTERN = re.compile(r"^[a-z_][a-z0-9_]*$")
DEFAULT_FIELDS = [
    KeyValue(key="projet", value="Projet"),
    KeyValue(key="numero_plan", value="N° plan"),
    KeyValue(key="indice", value="Indice"),
    KeyValue(key="date", value="Date"),
    KeyValue(key="echelle", value="Échelle"),
    KeyValue(key="auteur", value="Dessiné par"),
]
DEFAULT_REFERENCE_PATTERN = r"\b[A-Z]{1,4}-\d{2,6}[A-Z]?\b"
DEFAULT_FILE_NAME_TEMPLATE = "{projet}_rapport_{date}"


def _zone_field(label: str, default: float) -> float:
    value: float = ui_field("number", label=label, default=default, ge=0, le=PERCENT_MAX)
    return value


class PdfReportSettings(ModuleSettings):
    title_block_left: float = _zone_field(t("settings.title_block_left.label"), 55)
    title_block_top: float = _zone_field(t("settings.title_block_top.label"), 70)
    title_block_right: float = _zone_field(t("settings.title_block_right.label"), 100)
    title_block_bottom: float = _zone_field(t("settings.title_block_bottom.label"), 100)
    fields: list[KeyValue] = mapping_field(
        label=t("settings.fields.label"),
        key_label=t("settings.fields.key_label"),
        value_label=t("settings.fields.value_label"),
        default=DEFAULT_FIELDS,
        description=t("settings.fields.description"),
    )
    reference_pattern: str = ui_field(
        "text",
        label=t("settings.reference_pattern.label"),
        default=DEFAULT_REFERENCE_PATTERN,
        description=t("settings.reference_pattern.description"),
    )

    file_name_template: FileNameTemplate = file_name_template_field(DEFAULT_FILE_NAME_TEMPLATE)

    @field_validator("fields")
    @classmethod
    def validate_fields(cls, fields: list[KeyValue]) -> list[KeyValue]:
        for field in fields:
            if not TAG_PATTERN.match(field.key):
                raise ValueError(t("settings.invalid_tag", tag=field.key))
            if field.value.startswith(REGEX_PREFIX):
                _compile(field.value.removeprefix(REGEX_PREFIX), field.key)
        return fields

    @field_validator("reference_pattern")
    @classmethod
    def validate_reference_pattern(cls, pattern: str) -> str:
        _compile(pattern, t("settings.references_owner"))
        return pattern


def _compile(pattern: str, owner: str) -> re.Pattern[str]:
    try:
        return re.compile(pattern)
    except re.error as error:
        raise ValueError(t("settings.invalid_regex", owner=owner, error=error)) from error
