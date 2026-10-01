from collections.abc import Sequence
from dataclasses import dataclass

from engine.modules.dwg_parts.aggregation import PartLine, aggregate
from engine.modules.dwg_parts.mapping import map_parts
from engine.modules.dwg_parts.reader import RawPart
from engine.modules.dwg_parts.settings import DwgPartsSettings

DOCUMENT_TYPE = "liste-pieces"
NO_PART_WARNING = "Aucun bloc ne correspond aux blocs retenus (Paramètres → Liste de pièces)."


@dataclass(frozen=True)
class PartsList:
    headers: tuple[str, ...]
    lines: list[PartLine]
    warnings: list[str]

    @property
    def total_quantity(self) -> float:
        return sum(line.quantity for line in self.lines)


def build_parts_list(raw_parts: Sequence[RawPart], settings: DwgPartsSettings) -> PartsList:
    mapping = map_parts(raw_parts, settings)
    lines = aggregate(mapping.parts, group_identical=settings.group_identical)
    warnings = [*mapping.warnings, *([] if lines else [NO_PART_WARNING])]
    return PartsList(headers=mapping.headers, lines=lines, warnings=warnings)


def describe_result(parts_list: PartsList, read: int, total: int) -> str:
    quantity = parts_list.total_quantity
    pieces = int(quantity) if float(quantity).is_integer() else round(quantity, 2)
    return f"{len(parts_list.lines)} ligne(s), {pieces} pièce(s), {read}/{total} plan(s) lu(s)"
