import re
from collections.abc import Iterator, Mapping
from contextlib import contextmanager
from datetime import datetime
from pathlib import Path
from string import Formatter
from typing import Annotated, Any

from pydantic import AfterValidator

from engine.core.errors import EngineError, OutputWriteError
from engine.core.fields import ui_field
from engine.core.json_files import replace_file
from engine.core.messages import t
from engine.core.paths import WINDOWS_MAX_PATH_LENGTH, extended_path, write_failure_text
from engine.core.shutdown import hooks

NAMING_VARIABLES: dict[str, str] = {
    "projet": t("naming.variable.projet"),
    "type": t("naming.variable.type"),
    "date": t("naming.variable.date"),
    "heure": t("naming.variable.heure"),
    "source": t("naming.variable.source"),
    "indice": t("naming.variable.indice"),
}
DATE_FORMAT = "%Y%m%d"
TIME_FORMAT = "%H%M"
MAX_STEM_LENGTH = 150
# Below this, a name stops being recognizable: the extended-length prefix takes over instead.
MIN_STEM_LENGTH = 40
UNIQUE_INDEX_RESERVE = len(" (999)")
PATH_SEPARATOR = "\\"
FORBIDDEN_CHARACTERS = re.compile(r'[<>:"/\\|?*\x00-\x1f]')
EDGE_CHARACTERS = " ._-"
RESERVED_WINDOWS_NAMES = frozenset(
    {"CON", "PRN", "AUX", "NUL"}
    | {f"COM{index}" for index in range(1, 10)}
    | {f"LPT{index}" for index in range(1, 10)}
)
FORBIDDEN_REPLACEMENT = "-"
FALLBACK_STEM = "export"
PARTIAL_SUFFIX = ".partial"


def validate_template(template: str) -> str:
    if not template.strip():
        raise ValueError(t("naming.empty_template"))
    try:
        parts = list(Formatter().parse(template))
    except ValueError as error:
        raise ValueError(t("naming.unbalanced_braces")) from error
    for literal, variable, format_spec, conversion in parts:
        if FORBIDDEN_CHARACTERS.search(literal):
            raise ValueError(t("naming.forbidden_characters"))
        if variable is not None:
            _check_variable(variable, format_spec, conversion)
    return template


def _check_variable(variable: str, format_spec: str | None, conversion: str | None) -> None:
    if variable not in NAMING_VARIABLES:
        allowed = ", ".join(f"{{{name}}}" for name in NAMING_VARIABLES)
        raise ValueError(t("naming.unknown_variable", variable=variable, allowed=allowed))
    if format_spec or conversion:
        raise ValueError(t("naming.format_option", variable=variable))


FileNameTemplate = Annotated[str, AfterValidator(validate_template)]


def file_name_template_field(default: str) -> Any:
    variables = ", ".join(
        t("naming.variable_item", name=name, label=label)
        for name, label in NAMING_VARIABLES.items()
    )
    return ui_field(
        "text",
        label=t("naming.file_name_template.label"),
        default=default,
        description=t("naming.file_name_template.description", variables=variables),
    )


def naming_values(moment: datetime, **values: str) -> dict[str, str]:
    return {
        "date": moment.strftime(DATE_FORMAT),
        "heure": moment.strftime(TIME_FORMAT),
        **values,
    }


def render_file_name(
    template: str,
    values: Mapping[str, str],
    extension: str,
    *,
    max_stem_length: int = MAX_STEM_LENGTH,
) -> str:
    """Fills the template; missing variables are left empty and stray separators collapsed."""
    filled = "".join(
        literal + (values.get(variable, "") if variable is not None else "")
        for literal, variable, _, _ in Formatter().parse(template)
    )
    return f"{_safe_stem(filled, max_stem_length)}.{extension.lstrip('.')}"


class OutputFolderError(EngineError):
    pass


def output_target(folder: Path, template: str, values: Mapping[str, str], extension: str) -> Path:
    stem_length = stem_length_for(folder, extension)
    file_name = render_file_name(template, values, extension, max_stem_length=stem_length)
    return unique_output_path(folder, file_name)


def stem_length_for(folder: Path, extension: str) -> int:
    """Caps the name so the whole path stays openable by Windows tools when the folder allows."""
    suffixes = f".{extension.lstrip('.')}{PARTIAL_SUFFIX}"
    reserved = len(PATH_SEPARATOR) + UNIQUE_INDEX_RESERVE + len(suffixes)
    room = WINDOWS_MAX_PATH_LENGTH - len(str(folder.absolute())) - reserved
    return min(MAX_STEM_LENGTH, max(MIN_STEM_LENGTH, room))


def unique_output_path(folder: Path, file_name: str) -> Path:
    """Reserves the name atomically: two runs writing to the same folder never share it."""
    stem, suffix = Path(file_name).stem, Path(file_name).suffix
    try:
        extended_path(folder).mkdir(parents=True, exist_ok=True)
        index = 1
        while True:
            name = file_name if index == 1 else f"{stem} ({index}){suffix}"
            try:
                extended_path(folder / name).touch(exist_ok=False)
            except FileExistsError:
                index += 1
                continue
            return folder / name
    except OSError as error:
        message, hint = write_failure_text(
            folder / file_name,
            error,
            t("naming.output_folder_unreachable"),
            t("naming.output_folder_unreachable_hint"),
        )
        raise OutputFolderError(message, file=folder, hint=hint) from error


@contextmanager
def writing_output(target: Path) -> Iterator[Path]:
    """Yields the file to write; it takes the reserved name only once complete.

    A failure or a cancellation mid-write leaves neither a half-written document nor an empty
    one under the final name.
    """
    partial = target.with_name(f"{target.name}{PARTIAL_SUFFIX}")

    def discard() -> None:
        extended_path(partial).unlink(missing_ok=True)
        extended_path(target).unlink(missing_ok=True)

    try:
        with hooks.registered(discard):
            yield partial
            _finalize(partial, target)
    except BaseException:
        discard()
        raise


def _finalize(partial: Path, target: Path) -> None:
    try:
        replace_file(partial, target)
    except OSError as error:
        message, hint = write_failure_text(
            target,
            error,
            t("naming.output_finalize_failed"),
            t("naming.output_finalize_failed_hint"),
        )
        raise OutputWriteError(message, file=target, hint=hint) from error


def _safe_stem(raw: str, max_length: int) -> str:
    stem = FORBIDDEN_CHARACTERS.sub(FORBIDDEN_REPLACEMENT, raw)
    stem = _collapse_separators(stem)[:max_length].strip(EDGE_CHARACTERS)
    if not stem:
        return FALLBACK_STEM
    if stem.upper() in RESERVED_WINDOWS_NAMES:
        return f"{stem}_"
    return stem


def _collapse_separators(text: str) -> str:
    collapsed = re.sub(r"\s+", " ", text)
    return re.sub(r"([_-])(?:[ _-]*[_-])+", r"\1", collapsed)
