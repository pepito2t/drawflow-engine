from collections.abc import Sequence

from engine.core.events import PREVIEW_MAX_ROWS, TableEvent, TableRow
from engine.core.xlsx import quantity_text
from engine.modules.dwg_parts.messages import t
from engine.parts.aggregation import PartLine
from engine.parts.listing import PartsList

DOCUMENT_TYPE = "liste-pieces"
PROJECT_HEADER = t("service.project_header")
FILES_PROJECT = t("service.files_project")
QUANTITY_HEADER = t("service.quantity_header")
SOURCES_HEADER = t("service.sources_header")


def preview_table(parts_list: PartsList) -> TableEvent:
    """What the Excel file would contain, with every empty cell pointed out."""
    rows = [
        TableRow(
            cells=[*line.values, quantity_text(line.quantity), ", ".join(line.sources)],
            issues=[
                t("service.empty_cell", column=column)
                for column, value in zip(parts_list.headers, line.values, strict=True)
                if not value.strip()
            ],
        )
        for line in parts_list.lines[:PREVIEW_MAX_ROWS]
    ]
    headers = [*parts_list.headers, QUANTITY_HEADER, SOURCES_HEADER]
    return TableEvent(headers=headers, rows=rows, total=len(parts_list.lines))


def describe_result(parts_list: PartsList, read: int, total: int) -> str:
    quantity = parts_list.total_quantity
    pieces = int(quantity) if float(quantity).is_integer() else round(quantity, 2)
    return t("service.summary", lines=len(parts_list.lines), pieces=pieces, read=read, total=total)


def merge_projects(lists: Sequence[tuple[str, PartsList]]) -> PartsList:
    """One list for several projects: a « Projet » column first, lines kept per project."""
    headers = lists[0][1].headers if lists else ()
    lines = [
        PartLine((project, *line.values), line.quantity, line.sources)
        for project, parts_list in lists
        for line in parts_list.lines
    ]
    warnings = [warning for _, parts_list in lists for warning in parts_list.warnings]
    return PartsList(headers=(PROJECT_HEADER, *headers), lines=lines, warnings=warnings)


def total_of(lists: Sequence[tuple[str, PartsList]]) -> PartsList:
    """The same parts summed across projects, for one order to the supplier."""
    quantities: dict[tuple[str, ...], float] = {}
    sources: dict[tuple[str, ...], set[str]] = {}
    for _, parts_list in lists:
        for line in parts_list.lines:
            quantities[line.values] = quantities.get(line.values, 0.0) + line.quantity
            sources.setdefault(line.values, set()).update(line.sources)
    lines = [
        PartLine(values, quantity, tuple(sorted(sources[values])))
        for values, quantity in quantities.items()
    ]
    headers = lists[0][1].headers if lists else ()
    return PartsList(headers=headers, lines=lines, warnings=[])
