import fnmatch
from collections import Counter
from collections.abc import Sequence
from dataclasses import dataclass, field
from pathlib import Path

from engine.core.anomalies import Anomaly
from engine.modules.dwg_parts.reader import RawPart
from engine.modules.dwg_parts.settings import DwgPartsSettings

BLOCK_COLUMN_TITLE = "Bloc"
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


def map_parts(raw_parts: Sequence[RawPart], settings: DwgPartsSettings) -> MappingOutcome:
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


def _headers(settings: DwgPartsSettings) -> tuple[str, ...]:
    titles = tuple(column.key for column in settings.columns)
    return (BLOCK_COLUMN_TITLE, *titles) if settings.include_block_name else titles


def _column_values(
    part: RawPart, settings: DwgPartsSettings, missing: Counter[str]
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
            f"Attribut « {tag} » absent sur {_blocks(count)} (cellule laissée vide).",
            hint=f"Ajoutez l'attribut {tag} aux blocs dans AutoCAD, ou changez la colonne dans "
            "Paramètres → Liste de pièces.",
        )
        for tag, count in sorted(missing.items())
    ]
    if invalid_quantities:
        warnings.append(
            Anomaly(
                f"Quantité « {quantity_tag} » illisible sur {invalid_quantities} bloc(s) : "
                "compté(s) 1.",
                hint=f"Saisissez un nombre dans l'attribut {quantity_tag} de ces blocs.",
            )
        )
    return warnings


def _blocks(count: int) -> str:
    return f"{count} bloc{'s' if count > 1 else ''}"
