"""Pure comparison of two parts lists: what appeared, disappeared or changed quantity."""

import re
from collections.abc import Iterable, Sequence
from dataclasses import dataclass

from engine.core.events import TableEvent, TableRow
from engine.core.text import fold
from engine.modules.dwg_diff.messages import t
from engine.parts.listing import PartsList

DOCUMENT_TYPE = "comparaison"
PREVIEW_MAX_ROWS = 500
STATUS_HEADER = t("service.status_header")
QUANTITY_BEFORE_HEADER = t("service.quantity_before_header")
QUANTITY_AFTER_HEADER = t("service.quantity_after_header")
DELTA_HEADER = t("service.delta_header")
PLANS_BEFORE_HEADER = t("service.plans_before_header")
PLANS_AFTER_HEADER = t("service.plans_after_header")
ADDED = t("service.status.added")
REMOVED = t("service.status.removed")
CHANGED = t("service.status.changed")
UNCHANGED = t("service.status.unchanged")
PLAN_SEPARATOR = ", "

type Key = tuple[str, ...]


@dataclass(frozen=True)
class DiffLine:
    key: Key
    values: tuple[str, ...]
    before: float
    after: float
    plans_before: tuple[str, ...]
    plans_after: tuple[str, ...]

    @property
    def delta(self) -> float:
        return self.after - self.before


@dataclass(frozen=True)
class PlanStatus:
    name: str
    in_before: bool
    in_after: bool


@dataclass(frozen=True)
class DiffReport:
    headers: tuple[str, ...]
    added: list[DiffLine]
    removed: list[DiffLine]
    changed: list[DiffLine]
    unchanged: list[DiffLine]
    plans: list[PlanStatus]

    @property
    def differences(self) -> int:
        return len(self.added) + len(self.removed) + len(self.changed)


@dataclass(frozen=True)
class _Side:
    quantity: float
    values: tuple[str, ...]
    plans: set[str]


def strip_increment(name: str, increment: re.Pattern[str]) -> str:
    """'01_facade-nord.dwg' and 'facade-nord_02.dwg' both become 'facade-nord'."""
    stem = name.rsplit(".", 1)[0] if "." in name else name
    return increment.sub("", stem).strip()


def compare(
    before: PartsList,
    after: PartsList,
    key_columns: Sequence[str],
    increment: re.Pattern[str],
) -> DiffReport:
    headers = before.headers
    key_indexes = _key_indexes(headers, key_columns)
    sides_before = _group(before, key_indexes, increment)
    sides_after = _group(after, key_indexes, increment)
    added, removed, changed, unchanged = [], [], [], []
    for key in sorted(sides_before.keys() | sides_after.keys()):
        line = _line(key, sides_before.get(key), sides_after.get(key))
        if key not in sides_before:
            added.append(line)
        elif key not in sides_after:
            removed.append(line)
        elif line.before != line.after or sides_before[key].values != sides_after[key].values:
            changed.append(line)
        else:
            unchanged.append(line)
    plans = _plans(before, after, increment)
    return DiffReport(headers, added, removed, changed, unchanged, plans)


def preview_table(report: DiffReport) -> TableEvent:
    """Differences first, unchanged lines after; a changed quantity is the row's issue."""
    headers = [
        STATUS_HEADER,
        *report.headers,
        QUANTITY_BEFORE_HEADER,
        QUANTITY_AFTER_HEADER,
        DELTA_HEADER,
    ]
    listed = [
        *((ADDED, line) for line in report.added),
        *((REMOVED, line) for line in report.removed),
        *((CHANGED, line) for line in report.changed),
        *((UNCHANGED, line) for line in report.unchanged),
    ]
    rows = [
        TableRow(
            cells=[
                status,
                *line.values,
                _quantity(line.before),
                _quantity(line.after),
                _delta(line.delta),
            ],
            issues=[] if status == UNCHANGED else [_issue(status, line)],
        )
        for status, line in listed[:PREVIEW_MAX_ROWS]
    ]
    return TableEvent(headers=headers, rows=rows, total=len(listed))


def describe_result(report: DiffReport) -> str:
    return t(
        "service.summary",
        added=len(report.added),
        removed=len(report.removed),
        changed=len(report.changed),
        unchanged=len(report.unchanged),
    )


def _key_indexes(headers: Sequence[str], key_columns: Sequence[str]) -> list[int]:
    wanted = {fold(name) for name in key_columns}
    indexes = [index for index, header in enumerate(headers) if fold(header) in wanted]
    return indexes or list(range(len(headers)))


def _group(
    parts_list: PartsList, key_indexes: Sequence[int], increment: re.Pattern[str]
) -> dict[Key, _Side]:
    sides: dict[Key, _Side] = {}
    for line in parts_list.lines:
        key = tuple(line.values[index] for index in key_indexes)
        plans = {strip_increment(plan, increment) for plan in line.sources}
        known = sides.get(key)
        if known is None:
            sides[key] = _Side(line.quantity, line.values, plans)
        else:
            sides[key] = _Side(known.quantity + line.quantity, known.values, known.plans | plans)
    return sides


def _line(key: Key, before: _Side | None, after: _Side | None) -> DiffLine:
    reference = after or before
    assert reference is not None
    return DiffLine(
        key=key,
        values=reference.values,
        before=before.quantity if before else 0.0,
        after=after.quantity if after else 0.0,
        plans_before=tuple(sorted(before.plans)) if before else (),
        plans_after=tuple(sorted(after.plans)) if after else (),
    )


def _plans(before: PartsList, after: PartsList, increment: re.Pattern[str]) -> list[PlanStatus]:
    names_before = _plan_names(before, increment)
    names_after = _plan_names(after, increment)
    return [
        PlanStatus(name, name in names_before, name in names_after)
        for name in sorted(names_before | names_after, key=fold)
    ]


def _plan_names(parts_list: PartsList, increment: re.Pattern[str]) -> set[str]:
    return {strip_increment(plan, increment) for line in parts_list.lines for plan in line.sources}


def _quantity(value: float) -> str:
    return str(int(value)) if value.is_integer() else str(round(value, 2))


def _delta(value: float) -> str:
    text = _quantity(abs(value))
    return f"+{text}" if value > 0 else f"-{text}" if value < 0 else "0"


def _issue(status: str, line: DiffLine) -> str:
    if status == CHANGED:
        return t(
            "service.quantity_changed", before=_quantity(line.before), after=_quantity(line.after)
        )
    return status


def join_plans(plans: Iterable[str]) -> str:
    return PLAN_SEPARATOR.join(plans)
