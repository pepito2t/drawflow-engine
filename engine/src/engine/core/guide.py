"""The user guide (docs/guide.md), split by section: shown in the app and read by the assistant."""

import re
import sys
import unicodedata
from dataclasses import dataclass
from functools import cache
from pathlib import Path

from engine.core.errors import EngineError, InvalidInputError

GUIDE_PARTS = ("docs", "guide.md")
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


def guide_file() -> Path:
    bundle = getattr(sys, "_MEIPASS", None)
    root = Path(bundle) if bundle else SOURCE_ROOT
    return root.joinpath(*GUIDE_PARTS)


@cache
def sections() -> tuple[Section, ...]:
    try:
        text = guide_file().read_text(encoding="utf-8")
    except OSError as error:
        raise GuideUnavailableError(
            "Le guide utilisateur est introuvable.", hint="Réinstallez Drawflow."
        ) from error
    return tuple(_split(text))


def read_section(topic: str) -> Section:
    wanted = _fold(topic)
    for section in sections():
        if section.id == topic or _fold(section.title) == wanted:
            return section
    for section in sections():
        if wanted and wanted in _fold(section.title):
            return section
    available = ", ".join(section.id for section in sections())
    raise InvalidInputError(
        f"Section « {topic} » absente du guide.", hint=f"Sections : {available}."
    )


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
