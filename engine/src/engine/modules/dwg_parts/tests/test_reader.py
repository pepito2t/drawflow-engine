from pathlib import Path

import pytest

from engine.modules.dwg_parts.reader import DxfReadError, read_parts
from engine.modules.dwg_parts.tests.plans import build_facade_plan


@pytest.fixture
def plan(tmp_path: Path) -> Path:
    return build_facade_plan(tmp_path / "Façade nord é.dxf")


def test_reads_attributes_of_every_block_reference(plan: Path) -> None:
    parts = read_parts(plan, plan)

    panels = [part for part in parts if part.block == "PANNEAU"]
    assert len(panels) == 3
    assert panels[0].attributes["REF"] == "P-1200"
    assert panels[0].attributes["FINITION"] == "RAL 7016"
    assert panels[0].layout == "Model"
    assert panels[0].source == plan


def test_nested_blocks_are_included(plan: Path) -> None:
    blocks = [part.block for part in read_parts(plan, plan)]

    assert blocks.count("ASSEMBLAGE") == 1
    assert blocks.count("EQUERRE") == 2


def test_dynamic_blocks_use_their_original_name(plan: Path) -> None:
    windows = [part for part in read_parts(plan, plan) if part.attributes.get("REF") == "F-80"]

    assert [window.block for window in windows] == ["FENETRE"]


def test_count_defaults_to_one(plan: Path) -> None:
    assert {part.count for part in read_parts(plan, plan)} == {1}


def test_unreadable_file_names_the_source(tmp_path: Path) -> None:
    broken = tmp_path / "cassé.dxf"
    broken.write_text("pas un dxf", encoding="utf-8")
    original = tmp_path / "cassé.dwg"

    with pytest.raises(DxfReadError) as caught:
        read_parts(broken, original)

    assert caught.value.file == original
