import re

from pydantic import field_validator

from engine.core.fields import ui_field
from engine.core.naming import FileNameTemplate, file_name_template_field
from engine.core.settings_models import ModuleSettings
from engine.modules.dwg_diff.messages import t

DEFAULT_KEY_COLUMNS = "Référence"
# "01_facade-nord" and "facade-nord_02" are the same plan at two indices.
DEFAULT_INCREMENT_PATTERN = r"^\d{2,}[_-]|[_-]\d{2,}$"
DEFAULT_FILE_NAME_TEMPLATE = "{projet}_comparaison_{date}"
KEY_SEPARATOR = ";"


class DwgDiffSettings(ModuleSettings):
    key_columns: str = ui_field(
        "text",
        label=t("settings.key_columns.label"),
        default=DEFAULT_KEY_COLUMNS,
        description=t("settings.key_columns.description"),
    )
    increment_pattern: str = ui_field(
        "text",
        label=t("settings.increment_pattern.label"),
        default=DEFAULT_INCREMENT_PATTERN,
        description=t("settings.increment_pattern.description"),
    )
    file_name_template: FileNameTemplate = file_name_template_field(DEFAULT_FILE_NAME_TEMPLATE)

    @field_validator("increment_pattern")
    @classmethod
    def valid_pattern(cls, pattern: str) -> str:
        try:
            re.compile(pattern)
        except re.error as error:
            raise ValueError(t("settings.invalid_pattern", error=error)) from error
        return pattern

    def key_column_names(self) -> list[str]:
        return [name.strip() for name in self.key_columns.split(KEY_SEPARATOR) if name.strip()]

    def increment(self) -> re.Pattern[str]:
        return re.compile(self.increment_pattern)
