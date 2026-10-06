import re

from engine.modules.dwg_diff.service import (
    ADDED,
    CHANGED,
    REMOVED,
    UNCHANGED,
    compare,
    describe_result,
    preview_table,
    strip_increment,
)
from engine.modules.dwg_diff.settings import DEFAULT_INCREMENT_PATTERN
from engine.parts.aggregation import PartLine
from engine.parts.listing import PartsList

INCREMENT = re.compile(DEFAULT_INCREMENT_PATTERN)
HEADERS = ("Référence", "Longueur")


def parts(*lines: tuple[tuple[str, str], float, tuple[str, ...]]) -> PartsList:
    return PartsList(
        headers=HEADERS,
        lines=[PartLine(values, quantity, sources) for values, quantity, sources in lines],
        warnings=[],
    )


BEFORE = parts(
    (("P-1200", "1200"), 2.0, ("01_facade.dwg",)),
    (("P-900", "900"), 1.0, ("01_facade.dwg",)),
    (("EQ-40", ""), 2.0, ("01_facade.dwg",)),
)
AFTER = parts(
    (("P-1200", "1200"), 3.0, ("02_facade.dwg",)),
    (("EQ-40", ""), 2.0, ("02_facade.dwg",)),
    (("P-1500", "1500"), 1.0, ("02_facade.dwg", "02_pignon.dwg")),
)


def test_increments_are_stripped_from_plan_names() -> None:
    assert strip_increment("01_facade-nord.dwg", INCREMENT) == "facade-nord"
    assert strip_increment("facade-nord_02.DWG", INCREMENT) == "facade-nord"
    assert strip_increment("facade-nord.dwg", INCREMENT) == "facade-nord"


def test_compare_sorts_lines_into_added_removed_changed_and_unchanged() -> None:
    report = compare(BEFORE, AFTER, ["Référence"], INCREMENT)

    assert [line.key for line in report.added] == [("P-1500",)]
    assert [line.key for line in report.removed] == [("P-900",)]
    assert [(line.key, line.before, line.after) for line in report.changed] == [
        (("P-1200",), 2.0, 3.0)
    ]
    assert [line.key for line in report.unchanged] == [("EQ-40",)]
    assert report.added[0].plans_after == ("facade", "pignon")
    assert report.differences == 3


def test_plans_are_matched_across_indices_despite_increments() -> None:
    report = compare(BEFORE, AFTER, ["Référence"], INCREMENT)

    assert [(plan.name, plan.in_before, plan.in_after) for plan in report.plans] == [
        ("facade", True, True),
        ("pignon", False, True),
    ]


def test_unknown_key_columns_fall_back_to_every_column() -> None:
    report = compare(BEFORE, AFTER, ["Inexistante"], INCREMENT)

    assert [line.key for line in report.changed] == [("P-1200", "1200")]


def test_preview_lists_differences_first_with_the_change_as_issue() -> None:
    table = preview_table(compare(BEFORE, AFTER, ["Référence"], INCREMENT))

    assert table.headers[:2] == ["Statut", "Référence"]
    assert [row.cells[0] for row in table.rows] == [ADDED, REMOVED, CHANGED, UNCHANGED]
    assert table.rows[2].issues == ["Quantité 2 → 3"]
    assert table.rows[2].cells[-1] == "+1"
    assert table.rows[3].issues == []


def test_result_summary_counts_everything() -> None:
    summary = describe_result(compare(BEFORE, AFTER, ["Référence"], INCREMENT))

    assert summary == "1 ajout(s), 1 suppression(s), 1 modification(s), 1 inchangée(s)"
