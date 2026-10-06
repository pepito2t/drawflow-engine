import re

from pydantic import field_validator

from engine.core.fields import ui_field
from engine.core.naming import FileNameTemplate, file_name_template_field
from engine.core.settings_models import ModuleSettings

DEFAULT_KEY_COLUMNS = "Référence"
# "01_facade-nord" and "facade-nord_02" are the same plan at two indices.
DEFAULT_INCREMENT_PATTERN = r"^\d{2,}[_-]|[_-]\d{2,}$"
DEFAULT_FILE_NAME_TEMPLATE = "{projet}_comparaison_{date}"
KEY_SEPARATOR = ";"


class DwgDiffSettings(ModuleSettings):
    key_columns: str = ui_field(
        "text",
        label="Colonnes qui identifient une pièce",
        default=DEFAULT_KEY_COLUMNS,
        description="Noms de colonnes de la liste de pièces, séparés par « ; ». Vide : toutes "
        "les colonnes sauf la quantité.",
    )
    increment_pattern: str = ui_field(
        "text",
        label="Incrément dans les noms de plans",
        default=DEFAULT_INCREMENT_PATTERN,
        description="Expression régulière retirée du nom des plans pour reconnaître le même plan "
        "d'un indice à l'autre (préfixe « 01_ » ou suffixe « _02 » par défaut).",
    )
    file_name_template: FileNameTemplate = file_name_template_field(DEFAULT_FILE_NAME_TEMPLATE)

    @field_validator("increment_pattern")
    @classmethod
    def valid_pattern(cls, pattern: str) -> str:
        try:
            re.compile(pattern)
        except re.error as error:
            raise ValueError(f"expression régulière invalide ({error})") from error
        return pattern

    def key_column_names(self) -> list[str]:
        return [name.strip() for name in self.key_columns.split(KEY_SEPARATOR) if name.strip()]

    def increment(self) -> re.Pattern[str]:
        return re.compile(self.increment_pattern)
