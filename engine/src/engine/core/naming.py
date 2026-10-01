import re
from collections.abc import Mapping
from datetime import datetime
from pathlib import Path
from string import Formatter
from typing import Annotated, Any

from pydantic import AfterValidator

from engine.core.fields import ui_field

NAMING_VARIABLES: dict[str, str] = {
    "projet": "nom du projet",
    "type": "type de document",
    "date": "date (AAAAMMJJ)",
    "heure": "heure (HHMM)",
    "source": "nom du fichier source",
    "indice": "indice",
}
DATE_FORMAT = "%Y%m%d"
TIME_FORMAT = "%H%M"
MAX_STEM_LENGTH = 150
FORBIDDEN_CHARACTERS = re.compile(r'[<>:"/\\|?*\x00-\x1f]')
EDGE_CHARACTERS = " ._-"
RESERVED_WINDOWS_NAMES = frozenset(
    {"CON", "PRN", "AUX", "NUL"}
    | {f"COM{index}" for index in range(1, 10)}
    | {f"LPT{index}" for index in range(1, 10)}
)
FORBIDDEN_REPLACEMENT = "-"
FALLBACK_STEM = "export"


def validate_template(template: str) -> str:
    if not template.strip():
        raise ValueError("le modèle de nom ne peut pas être vide")
    try:
        parts = list(Formatter().parse(template))
    except ValueError as error:
        raise ValueError("accolades mal fermées dans le modèle de nom") from error
    for literal, variable, format_spec, conversion in parts:
        if FORBIDDEN_CHARACTERS.search(literal):
            raise ValueError('caractères interdits dans un nom de fichier : < > : " / \\ | ? *')
        if variable is not None:
            _check_variable(variable, format_spec, conversion)
    return template


def _check_variable(variable: str, format_spec: str | None, conversion: str | None) -> None:
    if variable not in NAMING_VARIABLES:
        allowed = ", ".join(f"{{{name}}}" for name in NAMING_VARIABLES)
        raise ValueError(f"variable inconnue {{{variable}}} ; variables possibles : {allowed}")
    if format_spec or conversion:
        raise ValueError(f"la variable {{{variable}}} ne prend pas d'option de format")


FileNameTemplate = Annotated[str, AfterValidator(validate_template)]


def file_name_template_field(default: str) -> Any:
    variables = ", ".join(f"{{{name}}} : {label}" for name, label in NAMING_VARIABLES.items())
    return ui_field(
        "text",
        label="Nom des fichiers exportés",
        default=default,
        description=f"Variables disponibles — {variables}.",
    )


def naming_values(moment: datetime, **values: str) -> dict[str, str]:
    return {
        "date": moment.strftime(DATE_FORMAT),
        "heure": moment.strftime(TIME_FORMAT),
        **values,
    }


def render_file_name(template: str, values: Mapping[str, str], extension: str) -> str:
    """Fills the template; missing variables are left empty and stray separators collapsed."""
    filled = "".join(
        literal + (values.get(variable, "") if variable is not None else "")
        for literal, variable, _, _ in Formatter().parse(template)
    )
    return f"{_safe_stem(filled)}.{extension.lstrip('.')}"


def unique_output_path(folder: Path, file_name: str) -> Path:
    candidate = folder / file_name
    index = 2
    while candidate.exists():
        candidate = folder / f"{Path(file_name).stem} ({index}){Path(file_name).suffix}"
        index += 1
    return candidate


def _safe_stem(raw: str) -> str:
    stem = FORBIDDEN_CHARACTERS.sub(FORBIDDEN_REPLACEMENT, raw)
    stem = _collapse_separators(stem)[:MAX_STEM_LENGTH].strip(EDGE_CHARACTERS)
    if not stem:
        return FALLBACK_STEM
    if stem.upper() in RESERVED_WINDOWS_NAMES:
        return f"{stem}_"
    return stem


def _collapse_separators(text: str) -> str:
    collapsed = re.sub(r"\s+", " ", text)
    return re.sub(r"([_-])(?:[ _-]*[_-])+", r"\1", collapsed)
