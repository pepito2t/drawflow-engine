from pydantic import field_validator

from engine.core.fields import KeyValue, mapping_field, ui_field
from engine.core.naming import FileNameTemplate, file_name_template_field
from engine.core.settings_models import ModuleSettings

DEFAULT_COLUMNS = [
    KeyValue(key="Référence", value="REF"),
    KeyValue(key="Désignation", value="DESIGNATION"),
    KeyValue(key="Longueur", value="LONGUEUR"),
    KeyValue(key="Matière", value="MATIERE"),
    KeyValue(key="Finition", value="FINITION"),
]
DEFAULT_FILE_NAME_TEMPLATE = "{projet}_liste-pieces_{date}"
BLOCK_PATTERN_SEPARATOR = ";"


class DwgPartsSettings(ModuleSettings):
    included_blocks: str = ui_field(
        "text",
        label="Blocs retenus",
        default="*",
        description=(
            "Noms de blocs séparés par « ; », jokers * et ? acceptés (ex. PANNEAU*;EQUERRE). "
            "* = tous les blocs."
        ),
        min_length=1,
    )
    columns: list[KeyValue] = mapping_field(
        label="Colonnes de la liste",
        key_label="Colonne",
        value_label="Attribut du bloc",
        default=DEFAULT_COLUMNS,
        description="Chaque colonne du fichier exporté reprend la valeur d'un attribut AutoCAD.",
    )
    quantity_attribute: str = ui_field(
        "text",
        label="Attribut de quantité",
        default="QTE",
        description="Laisser vide ou absent du bloc : chaque bloc compte pour 1.",
    )
    include_block_name: bool = ui_field("bool", label="Ajouter une colonne « Bloc »", default=True)
    group_identical: bool = ui_field(
        "bool",
        label="Regrouper les pièces identiques",
        default=True,
        description="Les pièces dont toutes les colonnes sont égales forment une seule ligne.",
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
