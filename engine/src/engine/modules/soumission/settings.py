from pydantic import field_validator

from engine.core.fields import KeyValue, mapping_field, ui_field
from engine.core.naming import FileNameTemplate, file_name_template_field
from engine.core.settings_models import ModuleSettings

SYNONYM_SEPARATOR = ";"
DEFAULT_COLUMNS = [
    KeyValue(key="Position", value="pos;position;n°;no;numéro"),
    KeyValue(key="Désignation", value="désignation;description;libellé;texte"),
    KeyValue(key="Quantité", value="quantité;qté;qte;qty"),
    KeyValue(key="Unité", value="unité;u;unit;un"),
    KeyValue(key="Prix unitaire", value="prix unitaire;pu;p.u.;prix"),
    KeyValue(key="Total", value="total;montant;prix total"),
]
DEFAULT_NUMERIC_COLUMNS = "Quantité;Prix unitaire;Total"
DEFAULT_FILE_NAME_TEMPLATE = "{projet}_soumission_{date}"
MIN_HEADER_MATCHES = 2
MAX_HEADER_SEARCH_ROWS = 200


class SoumissionSettings(ModuleSettings):
    columns: list[KeyValue] = mapping_field(
        label="Colonnes normalisées",
        key_label="Colonne exportée",
        value_label="En-têtes reconnus (séparés par ;)",
        default=DEFAULT_COLUMNS,
        description="L'en-tête du tableau est repéré grâce à ces libellés (sans accents ni casse).",
    )
    numeric_columns: str = ui_field(
        "text",
        label="Colonnes numériques",
        default=DEFAULT_NUMERIC_COLUMNS,
        description="Colonnes converties en nombres (formats 1'234.50 et 1 234,50 acceptés).",
    )
    header_search_rows: int = ui_field(
        "number",
        label="Lignes parcourues pour trouver l'en-tête",
        default=30,
        ge=1,
        le=MAX_HEADER_SEARCH_ROWS,
    )
    file_name_template: FileNameTemplate = file_name_template_field(DEFAULT_FILE_NAME_TEMPLATE)

    @field_validator("columns")
    @classmethod
    def require_synonyms(cls, columns: list[KeyValue]) -> list[KeyValue]:
        for column in columns:
            if not synonyms_of(column):
                raise ValueError(f"aucun en-tête reconnu pour « {column.key} »")
        return columns

    def numeric_column_names(self) -> set[str]:
        return {
            name.strip() for name in self.numeric_columns.split(SYNONYM_SEPARATOR) if name.strip()
        }


def synonyms_of(column: KeyValue) -> list[str]:
    return [synonym.strip() for synonym in column.value.split(SYNONYM_SEPARATOR) if synonym.strip()]
