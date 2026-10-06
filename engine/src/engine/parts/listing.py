"""From raw block references to the lines of a parts list, shared by every feature listing parts."""

from collections.abc import Sequence
from dataclasses import dataclass

from engine.core.anomalies import Anomaly
from engine.parts.aggregation import PartLine, aggregate
from engine.parts.mapping import map_parts
from engine.parts.messages import t
from engine.parts.reader import RawPart
from engine.parts.settings import PartsListSettings

NO_PART_WARNING = t("listing.no_part")


@dataclass(frozen=True)
class PartsList:
    headers: tuple[str, ...]
    lines: list[PartLine]
    warnings: list[Anomaly]

    @property
    def total_quantity(self) -> float:
        return sum(line.quantity for line in self.lines)


def build_parts_list(raw_parts: Sequence[RawPart], settings: PartsListSettings) -> PartsList:
    mapping = map_parts(raw_parts, settings)
    lines = aggregate(mapping.parts, group_identical=settings.group_identical)
    no_part = Anomaly(NO_PART_WARNING, hint=t("listing.no_part_hint"))
    warnings = [*mapping.warnings, *([] if lines else [no_part])]
    return PartsList(headers=mapping.headers, lines=lines, warnings=warnings)
