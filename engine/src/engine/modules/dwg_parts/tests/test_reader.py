from pathlib import Path

import pytest
from ezdxf.filemanagement import new

from engine.core.events import Event, WarningEvent
from engine.modules.dwg_parts.reader import MAX_NESTING_DEPTH, DxfReadError, read_parts
from engine.modules.dwg_parts.tests.plans import build_facade_plan


@pytest.fixture
def plan(tmp_path: Path) -> Path:
    return build_facade_plan(tmp_path / "Façade nord é.dxf")


def test_reads_attributes_of_every_block_reference(plan: Path) -> None:
    parts = read_parts(plan, plan, lambda _: None)

    panels = [part for part in parts if part.block == "PANNEAU"]
    assert len(panels) == 3
    assert panels[0].attributes["REF"] == "P-1200"
    assert panels[0].attributes["FINITION"] == "RAL 7016"
    assert panels[0].layout == "Model"
    assert panels[0].source == plan


def test_nested_blocks_are_included(plan: Path) -> None:
    blocks = [part.block for part in read_parts(plan, plan, lambda _: None)]

    assert blocks.count("ASSEMBLAGE") == 1
    assert blocks.count("EQUERRE") == 2


def test_dynamic_blocks_use_their_original_name(plan: Path) -> None:
    windows = [
        part
        for part in read_parts(plan, plan, lambda _: None)
        if part.attributes.get("REF") == "F-80"
    ]

    assert [window.block for window in windows] == ["FENETRE"]


def test_count_defaults_to_one(plan: Path) -> None:
    assert {part.count for part in read_parts(plan, plan, lambda _: None)} == {1}


def test_unreadable_file_names_the_source(tmp_path: Path) -> None:
    broken = tmp_path / "cassé.dxf"
    broken.write_text("pas un dxf", encoding="utf-8")
    original = tmp_path / "cassé.dwg"

    with pytest.raises(DxfReadError) as caught:
        read_parts(broken, original, lambda _: None)

    assert caught.value.file == original


def test_blocks_nested_too_deeply_are_reported_instead_of_silently_dropped(tmp_path: Path) -> None:
    document = new("R2018")
    levels = MAX_NESTING_DEPTH + 2
    for level in range(levels):
        block = document.blocks.new(f"NIVEAU{level}")
        if level + 1 < levels:
            block.add_blockref(f"NIVEAU{level + 1}", (0, 0))
    document.modelspace().add_blockref("NIVEAU0", (0, 0))
    plan = tmp_path / "profond.dxf"
    document.saveas(plan)
    events: list[Event] = []

    blocks = [part.block for part in read_parts(plan, plan, events.append)]

    assert blocks == [f"NIVEAU{level}" for level in range(MAX_NESTING_DEPTH + 1)]
    assert len(events) == 1
    assert isinstance(events[0], WarningEvent)
    assert events[0].location == f"blocs NIVEAU{MAX_NESTING_DEPTH}"
    assert events[0].hint is not None
    assert events[0].file == str(plan)
