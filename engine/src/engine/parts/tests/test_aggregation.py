from pathlib import Path

from engine.parts.aggregation import PartLine, aggregate
from engine.parts.mapping import MappedPart


def part(*values: str, quantity: float = 1, source: str = "a.dwg") -> MappedPart:
    return MappedPart(values=values, quantity=quantity, source=Path("plans") / source)


def test_identical_parts_are_merged_and_quantities_summed() -> None:
    lines = aggregate(
        [part("P-1", "1200", quantity=2), part("P-1", "1200", source="b.dwg"), part("P-2", "900")],
        group_identical=True,
    )

    assert lines == [
        PartLine(("P-1", "1200"), 3, ("a.dwg", "b.dwg")),
        PartLine(("P-2", "900"), 1, ("a.dwg",)),
    ]


def test_parts_differing_by_one_column_stay_separate() -> None:
    lines = aggregate([part("P-1", "1200"), part("P-1", "1300")], group_identical=True)

    assert len(lines) == 2


def test_natural_sort_orders_numbers_by_value() -> None:
    lines = aggregate([part("P-1200"), part("P-900"), part("p-95")], group_identical=True)

    assert [line.values[0] for line in lines] == ["p-95", "P-900", "P-1200"]


def test_grouping_can_be_disabled() -> None:
    lines = aggregate([part("P-1"), part("P-1")], group_identical=False)

    assert [line.quantity for line in lines] == [1, 1]


def test_empty_input_gives_empty_list() -> None:
    assert aggregate([], group_identical=True) == []
