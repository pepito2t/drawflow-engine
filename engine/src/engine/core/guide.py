"""The user guide (docs/guide.md), split by section: shown in the app and read by the assistant."""

import re
import sys
import unicodedata
from dataclasses import dataclass
from functools import cache
from pathlib import Path

from engine.core.errors import EngineError, InvalidInputError
from engine.core.i18n import DEFAULT_LANGUAGE, Language, current_language
from engine.core.messages import t

GUIDE_FILES: dict[Language, tuple[str, ...]] = {
    "fr": ("docs", "guide.md"),
    "en": ("docs", "guide.en.md"),
}
# engine/src/engine/core/guide.py → repository root, for runs from the source checkout.
SOURCE_ROOT = Path(__file__).resolve().parents[4]
SECTION_PREFIX = "## "
SLUG_DROPPED = re.compile(r"[^\w\- ]")


@dataclass(frozen=True)
class Section:
    id: str
    title: str
    markdown: str


class GuideUnavailableError(EngineError):
    pass


def guide_file(language: Language | None = None) -> Path:
    bundle = getattr(sys, "_MEIPASS", None)
    root = Path(bundle) if bundle else SOURCE_ROOT
    wanted = root.joinpath(*GUIDE_FILES[language or current_language()])
    return wanted if wanted.is_file() else root.joinpath(*GUIDE_FILES[DEFAULT_LANGUAGE])


def sections() -> tuple[Section, ...]:
    return _sections(current_language())


@cache
def _sections(language: Language) -> tuple[Section, ...]:
    try:
        text = guide_file(language).read_text(encoding="utf-8")
    except OSError as error:
        raise GuideUnavailableError(
            t("guide.unavailable"), hint=t("guide.unavailable_hint")
        ) from error
    return tuple(_split(text))


def read_section(topic: str) -> Section:
    found = _find(topic, sections())
    if found is None and current_language() != DEFAULT_LANGUAGE:
        # Topics are often French ids (setup screen, saved links): same position in both guides.
        french = _sections(DEFAULT_LANGUAGE)
        translated = _find(topic, french)
        if translated is not None and len(french) == len(sections()):
            found = sections()[french.index(translated)]
    if found is not None:
        return found
    available = ", ".join(section.id for section in sections())
    raise InvalidInputError(
        t("guide.section_missing", topic=topic),
        hint=t("guide.section_missing_hint", available=available),
    )


def _find(topic: str, candidates: tuple[Section, ...]) -> Section | None:
    wanted = _fold(topic)
    for section in candidates:
        if section.id == topic or _fold(section.title) == wanted:
            return section
    for section in candidates:
        if wanted and wanted in _fold(section.title):
            return section
    return None


def slug(title: str) -> str:
    """Same anchors as GitHub, so the guide's own links keep working."""
    return SLUG_DROPPED.sub("", title.strip().lower()).replace(" ", "-")


def _split(text: str) -> list[Section]:
    found: list[Section] = []
    title: str | None = None
    lines: list[str] = []
    for line in text.splitlines():
        if line.startswith(SECTION_PREFIX):
            if title is not None:
                found.append(_section(title, lines))
            title, lines = line.removeprefix(SECTION_PREFIX).strip(), []
        elif title is not None:
            lines.append(line)
    if title is not None:
        found.append(_section(title, lines))
    return found


def _section(title: str, lines: list[str]) -> Section:
    return Section(id=slug(title), title=title, markdown="\n".join(lines).strip())


def _fold(text: str) -> str:
    decomposed = unicodedata.normalize("NFD", text.casefold())
    return "".join(char for char in decomposed if not unicodedata.combining(char)).strip()
