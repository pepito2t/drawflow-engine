import re
import unicodedata
from collections.abc import Iterable, Sequence
from dataclasses import dataclass

from engine.core.fields import KeyValue
from engine.modules.pdf_report.reader import TextLine
from engine.modules.pdf_report.settings import REGEX_PREFIX

EN_DASH = "\u2013"
VALUE_SEPARATORS = f" :-{EN_DASH}\t"


@dataclass(frozen=True)
class FieldExtraction:
    values: dict[str, str]
    missing: list[str]


def extract_fields(lines: Sequence[TextLine], rules: Sequence[KeyValue]) -> FieldExtraction:
    values: dict[str, str] = {}
    missing: list[str] = []
    for rule in rules:
        value = _apply(rule.value, lines)
        values[rule.key] = value
        if not value:
            missing.append(rule.key)
    return FieldExtraction(values=values, missing=missing)


def find_references(lines: Iterable[TextLine], pattern: str) -> list[str]:
    compiled = re.compile(pattern)
    found = {match.group(0) for line in lines for match in compiled.finditer(line.text)}
    return sorted(found)


def _apply(rule: str, lines: Sequence[TextLine]) -> str:
    if rule.startswith(REGEX_PREFIX):
        return _by_regex(rule.removeprefix(REGEX_PREFIX), lines)
    return _by_label(rule, lines)


def _by_regex(pattern: str, lines: Sequence[TextLine]) -> str:
    compiled = re.compile(pattern)
    for line in lines:
        match = compiled.search(line.text)
        if match:
            return (match.group(1) if compiled.groups else match.group(0)).strip()
    return ""


def _by_label(label: str, lines: Sequence[TextLine]) -> str:
    wanted = _normalize(label)
    for index, line in enumerate(lines):
        position = _normalize(line.text).find(wanted)
        if position < 0:
            continue
        after = line.text[position + len(label) :].strip(VALUE_SEPARATORS)
        if after:
            return after
        return _next_line_below(lines, index)
    return ""


def _next_line_below(lines: Sequence[TextLine], index: int) -> str:
    label_line = lines[index]
    below = [
        line
        for line in lines[index + 1 :]
        if line.top > label_line.top and line.x1 >= label_line.x0 and line.x0 <= label_line.x1
    ]
    return below[0].text.strip() if below else ""


def _normalize(text: str) -> str:
    """Accent- and case-insensitive comparison; keeps one character per input character."""
    decomposed = unicodedata.normalize("NFD", text)
    stripped = "".join(char for char in decomposed if not unicodedata.combining(char))
    return stripped.casefold() if len(stripped) == len(text) else text.casefold()
