from pydantic import field_validator

from engine.core.fields import KeyValue, mapping_field, ui_field
from engine.core.naming import FileNameTemplate, file_name_template_field
from engine.core.settings_models import ModuleSettings
from engine.modules.soumission.messages import t

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
        label=t("settings.columns.label"),
        key_label=t("settings.columns.key_label"),
        value_label=t("settings.columns.value_label"),
        default=DEFAULT_COLUMNS,
        description=t("settings.columns.description"),
    )
    numeric_columns: str = ui_field(
        "text",
        label=t("settings.numeric_columns.label"),
        default=DEFAULT_NUMERIC_COLUMNS,
        description=t("settings.numeric_columns.description"),
    )
    header_search_rows: int = ui_field(
        "number",
        label=t("settings.header_search_rows.label"),
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
                raise ValueError(t("settings.no_synonyms", column=column.key))
        return columns

    def numeric_column_names(self) -> set[str]:
        return {
            name.strip() for name in self.numeric_columns.split(SYNONYM_SEPARATOR) if name.strip()
        }


def synonyms_of(column: KeyValue) -> list[str]:
    return [synonym.strip() for synonym in column.value.split(SYNONYM_SEPARATOR) if synonym.strip()]
