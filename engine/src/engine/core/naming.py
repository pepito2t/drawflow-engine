import re
from collections.abc import Iterator, Mapping
from contextlib import contextmanager
from datetime import datetime
from pathlib import Path
from string import Formatter
from typing import Annotated, Any

from pydantic import AfterValidator

from engine.core.errors import EngineError
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


class OutputFolderError(EngineError):
    pass


def output_target(folder: Path, template: str, values: Mapping[str, str], extension: str) -> Path:
    return unique_output_path(folder, render_file_name(template, values, extension))


def unique_output_path(folder: Path, file_name: str) -> Path:
    """Reserves the name atomically: two runs writing to the same folder never share it."""
    stem, suffix = Path(file_name).stem, Path(file_name).suffix
    try:
        folder.mkdir(parents=True, exist_ok=True)
        index = 1
        while True:
            name = file_name if index == 1 else f"{stem} ({index}){suffix}"
            try:
                (folder / name).touch(exist_ok=False)
            except FileExistsError:
                index += 1
                continue
            return folder / name
    except OSError as error:
        raise OutputFolderError(
            "Le dossier de sortie est inaccessible.",
            file=folder,
            hint="Choisissez un autre dossier de sortie, ou vérifiez vos droits dessus.",
        ) from error


@contextmanager
def writing_output(path: Path) -> Iterator[Path]:
    """Removes the reserved file when the writer fails, so no empty document is left behind."""
    try:
        yield path
    except BaseException:
        path.unlink(missing_ok=True)
        raise


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
