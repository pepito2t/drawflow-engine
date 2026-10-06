import fnmatch
from collections import Counter
from collections.abc import Sequence
from dataclasses import dataclass, field
from pathlib import Path

from engine.core.anomalies import Anomaly
from engine.parts.messages import t
from engine.parts.reader import RawPart
from engine.parts.settings import PartsListSettings

BLOCK_COLUMN_TITLE = t("mapping.block_column")
DECIMAL_COMMA = ","


@dataclass(frozen=True)
class MappedPart:
    values: tuple[str, ...]
    quantity: float
    source: Path


@dataclass(frozen=True)
class MappingOutcome:
    headers: tuple[str, ...]
    parts: list[MappedPart]
    warnings: list[Anomaly] = field(default_factory=list)


def map_parts(raw_parts: Sequence[RawPart], settings: PartsListSettings) -> MappingOutcome:
    patterns = settings.block_patterns()
    retained = [part for part in raw_parts if _matches(part.block, patterns)]
    missing: Counter[str] = Counter()
    invalid_quantities = 0
    mapped: list[MappedPart] = []
    for part in retained:
        values = _column_values(part, settings, missing)
        quantity, valid = _quantity(part, settings.quantity_attribute)
        invalid_quantities += 0 if valid else 1
        mapped.append(MappedPart(values=values, quantity=quantity, source=part.source))
    return MappingOutcome(
        headers=_headers(settings),
        parts=mapped,
        warnings=_warnings(missing, invalid_quantities, settings.quantity_attribute),
    )


def _matches(block: str, patterns: Sequence[str]) -> bool:
    name = block.upper()
    return any(fnmatch.fnmatchcase(name, pattern.upper()) for pattern in patterns)


def _headers(settings: PartsListSettings) -> tuple[str, ...]:
    titles = tuple(column.key for column in settings.columns)
    return (BLOCK_COLUMN_TITLE, *titles) if settings.include_block_name else titles


def _column_values(
    part: RawPart, settings: PartsListSettings, missing: Counter[str]
) -> tuple[str, ...]:
    values: list[str] = []
    for column in settings.columns:
        value = part.attributes.get(column.value)
        if value is None:
            missing[column.value] += 1
        values.append(value or "")
    return (part.block, *values) if settings.include_block_name else tuple(values)


def _quantity(part: RawPart, tag: str) -> tuple[float, bool]:
    raw = part.attributes.get(tag, "").strip() if tag else ""
    if not raw:
        return float(part.count), True
    try:
        return float(raw.replace(DECIMAL_COMMA, ".")) * part.count, True
    except ValueError:
        return float(part.count), False


def _warnings(missing: Counter[str], invalid_quantities: int, quantity_tag: str) -> list[Anomaly]:
    warnings = [
        Anomaly(
            t("mapping.missing_attribute", tag=tag, blocks=_blocks(count)),
            hint=t("mapping.missing_attribute_hint", tag=tag),
        )
        for tag, count in sorted(missing.items())
    ]
    if invalid_quantities:
        warnings.append(
            Anomaly(
                t("mapping.invalid_quantity", tag=quantity_tag, count=invalid_quantities),
                hint=t("mapping.invalid_quantity_hint", tag=quantity_tag),
            )
        )
    return warnings


def _blocks(count: int) -> str:
    return t("mapping.blocks.many" if count > 1 else "mapping.blocks.one", count=count)
