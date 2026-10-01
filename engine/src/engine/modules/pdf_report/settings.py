import re

from pydantic import field_validator

from engine.core.fields import KeyValue, mapping_field, ui_field
from engine.core.naming import FileNameTemplate, file_name_template_field
from engine.core.settings_models import ModuleSettings

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
    title_block_left: float = _zone_field("Cartouche : bord gauche (% de la largeur)", 55)
    title_block_top: float = _zone_field("Cartouche : bord haut (% de la hauteur)", 70)
    title_block_right: float = _zone_field("Cartouche : bord droit (% de la largeur)", 100)
    title_block_bottom: float = _zone_field("Cartouche : bord bas (% de la hauteur)", 100)
    fields: list[KeyValue] = mapping_field(
        label="Champs du cartouche",
        key_label="Balise Word",
        value_label="Libellé dans le cartouche",
        default=DEFAULT_FIELDS,
        description=(
            "La valeur est le texte qui suit le libellé (ou la ligne suivante). "
            "Préfixe « re: » pour une expression régulière avec un groupe, "
            "ex. re:Ind\\.?\\s*(\\w+)."
        ),
    )
    reference_pattern: str = ui_field(
        "text",
        label="Format des références",
        default=DEFAULT_REFERENCE_PATTERN,
        description="Expression régulière des références relevées sur tout le plan.",
    )

    file_name_template: FileNameTemplate = file_name_template_field(DEFAULT_FILE_NAME_TEMPLATE)

    @field_validator("fields")
    @classmethod
    def validate_fields(cls, fields: list[KeyValue]) -> list[KeyValue]:
        for field in fields:
            if not TAG_PATTERN.match(field.key):
                raise ValueError(
                    f"balise « {field.key} » invalide : minuscules, chiffres et _ uniquement"
                )
            if field.value.startswith(REGEX_PREFIX):
                _compile(field.value.removeprefix(REGEX_PREFIX), field.key)
        return fields

    @field_validator("reference_pattern")
    @classmethod
    def validate_reference_pattern(cls, pattern: str) -> str:
        _compile(pattern, "références")
        return pattern


def _compile(pattern: str, owner: str) -> re.Pattern[str]:
    try:
        return re.compile(pattern)
    except re.error as error:
        raise ValueError(f"expression régulière invalide pour « {owner} » : {error}") from error
