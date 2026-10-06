"""The engine's language: chosen once per process, before any label or message is built."""

import json
import re
from collections.abc import Callable, Mapping, Sequence
from pathlib import Path
from typing import Literal, TypeGuard, get_args

Language = Literal["fr", "en"]
LANGUAGES: tuple[Language, ...] = get_args(Language)
DEFAULT_LANGUAGE: Language = "fr"
LANGUAGE_FLAG = "--lang"
SETTINGS_FLAG = "--settings"
GENERAL_SECTION = "general"
LANGUAGE_FIELD = "language"
PLACEHOLDER = re.compile(r"\{(\w+)\}")

Messages = Mapping[str, str]
Translate = Callable[..., str]

_current: Language = DEFAULT_LANGUAGE
# Every catalog registers itself so a test can check both languages agree.
CATALOGS: list[dict[Language, Messages]] = []


def current_language() -> Language:
    return _current


def set_language(language: Language) -> None:
    global _current
    _current = language


def is_language(value: object) -> TypeGuard[Language]:
    return isinstance(value, str) and value in LANGUAGES


def language_from_argv(argv: Sequence[str]) -> Language | None:
    """`--lang xx` wins; otherwise the `language` saved in the file given by `--settings`."""
    explicit = _flag_value(argv, LANGUAGE_FLAG)
    if is_language(explicit):
        return explicit
    settings = _flag_value(argv, SETTINGS_FLAG)
    return _language_in_settings(Path(settings)) if settings else None


def configure_from_argv(argv: Sequence[str]) -> None:
    set_language(language_from_argv(argv) or DEFAULT_LANGUAGE)


def define_messages(*, fr: Messages, en: Messages) -> Translate:
    """A catalog; `t(key, **params)` resolves the current language when called."""
    catalog: dict[Language, Messages] = {"fr": fr, "en": en}
    CATALOGS.append(catalog)

    def translate(key: str, **params: object) -> str:
        text = catalog[_current][key]
        return text.format(**params) if params else text

    return translate


def catalog_issues(catalog: Mapping[Language, Messages]) -> list[str]:
    """Keys missing in one language, or placeholders that differ between languages."""
    issues = []
    fr, en = catalog["fr"], catalog["en"]
    for key in sorted(set(fr) ^ set(en)):
        issues.append(f"clé « {key} » absente d'une langue")
    for key in sorted(set(fr) & set(en)):
        if set(PLACEHOLDER.findall(fr[key])) != set(PLACEHOLDER.findall(en[key])):
            issues.append(f"clé « {key} » : paramètres différents entre fr et en")
    return issues


def _flag_value(argv: Sequence[str], flag: str) -> str | None:
    for index, argument in enumerate(argv):
        if argument == flag and index + 1 < len(argv):
            return argv[index + 1]
        if argument.startswith(flag + "="):
            return argument.removeprefix(flag + "=")
    return None


def _language_in_settings(path: Path) -> Language | None:
    try:
        document = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return None
    general = document.get(GENERAL_SECTION) if isinstance(document, dict) else None
    value = general.get(LANGUAGE_FIELD) if isinstance(general, dict) else None
    return value if is_language(value) else None
