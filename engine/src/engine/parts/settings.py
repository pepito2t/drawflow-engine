from pydantic import field_validator

from engine.core.fields import KeyValue, mapping_field, ui_field
from engine.core.naming import FileNameTemplate, file_name_template_field
from engine.core.settings_models import ModuleSettings
from engine.parts.messages import t

DEFAULT_COLUMNS = [
    KeyValue(key=t("settings.column.reference"), value="REF"),
    KeyValue(key=t("settings.column.designation"), value="DESIGNATION"),
    KeyValue(key=t("settings.column.length"), value="LONGUEUR"),
    KeyValue(key=t("settings.column.material"), value="MATIERE"),
    KeyValue(key=t("settings.column.finish"), value="FINITION"),
]
DEFAULT_FILE_NAME_TEMPLATE = f"{{projet}}_{t('settings.file_name_stem')}_{{date}}"
BLOCK_PATTERN_SEPARATOR = ";"
MAX_HEADER_ROW = 1000


class PartsListSettings(ModuleSettings):
    included_blocks: str = ui_field(
        "text",
        label=t("settings.included_blocks.label"),
        default="*",
        description=t("settings.included_blocks.description"),
        min_length=1,
    )
    columns: list[KeyValue] = mapping_field(
        label=t("settings.columns.label"),
        key_label=t("settings.columns.key_label"),
        value_label=t("settings.columns.value_label"),
        default=DEFAULT_COLUMNS,
        description=t("settings.columns.description"),
    )
    quantity_attribute: str = ui_field(
        "text",
        label=t("settings.quantity_attribute.label"),
        default="QTE",
        description=t("settings.quantity_attribute.description"),
    )
    include_block_name: bool = ui_field(
        "bool", label=t("settings.include_block_name.label"), default=True
    )
    group_identical: bool = ui_field(
        "bool",
        label=t("settings.group_identical.label"),
        default=True,
        description=t("settings.group_identical.description"),
    )
    template_sheet: str = ui_field(
        "text",
        label=t("settings.template_sheet.label"),
        default="",
        description=t("settings.template_sheet.description"),
    )
    header_row: int = ui_field(
        "number",
        label=t("settings.header_row.label"),
        default=1,
        description=t("settings.header_row.description"),
        ge=1,
        le=MAX_HEADER_ROW,
    )
    file_name_template: FileNameTemplate = file_name_template_field(DEFAULT_FILE_NAME_TEMPLATE)

    @field_validator("columns")
    @classmethod
    def normalize_tags(cls, columns: list[KeyValue]) -> list[KeyValue]:
        return [
            KeyValue(key=column.key.strip(), value=column.value.strip().upper())
            for column in columns
        ]

    @field_validator("quantity_attribute")
    @classmethod
    def normalize_quantity_tag(cls, tag: str) -> str:
        return tag.strip().upper()

    def block_patterns(self) -> list[str]:
        patterns = self.included_blocks.split(BLOCK_PATTERN_SEPARATOR)
        return [pattern.strip() for pattern in patterns if pattern.strip()]
