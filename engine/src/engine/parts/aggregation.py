import re
from collections.abc import Sequence
from dataclasses import dataclass

from engine.parts.mapping import MappedPart

DIGITS = re.compile(r"(\d+)")

type NaturalKey = tuple[tuple[int, int | str], ...]


@dataclass(frozen=True)
class PartLine:
    values: tuple[str, ...]
    quantity: float
    sources: tuple[str, ...]


def aggregate(parts: Sequence[MappedPart], *, group_identical: bool) -> list[PartLine]:
    """Merges parts whose column values are all identical, summing quantities."""
    if not group_identical:
        lines = [PartLine(part.values, part.quantity, (part.source.name,)) for part in parts]
        return sorted(lines, key=_line_key)
    quantities: dict[tuple[str, ...], float] = {}
    sources: dict[tuple[str, ...], set[str]] = {}
    for part in parts:
        quantities[part.values] = quantities.get(part.values, 0.0) + part.quantity
        sources.setdefault(part.values, set()).add(part.source.name)
    lines = [
        PartLine(values, quantity, tuple(sorted(sources[values])))
        for values, quantity in quantities.items()
    ]
    return sorted(lines, key=_line_key)


def _line_key(line: PartLine) -> tuple[NaturalKey, ...]:
    return tuple(_natural_key(value) for value in line.values)


def _natural_key(value: str) -> NaturalKey:
    """Orders 'P-900' before 'P-1200' instead of plain text order."""
    return tuple(
        (0, int(chunk)) if chunk.isdigit() else (1, chunk.casefold())
        for chunk in DIGITS.split(value)
        if chunk
    )
