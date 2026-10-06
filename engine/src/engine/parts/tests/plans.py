"""Synthetic plans used by tests and by scripts/generate-sample-plans.py."""

from pathlib import Path

from ezdxf.document import Drawing
from ezdxf.filemanagement import new
from ezdxf.layouts.base import BaseLayout
from ezdxf.layouts.blocklayout import BlockLayout

DYNAMIC_BLOCK_APPID = "AcDbBlockRepBTag"
PART_TAGS = ("REF", "DESIGNATION", "LONGUEUR", "MATIERE", "FINITION")


def define_part_block(document: Drawing, name: str) -> BlockLayout:
    block = document.blocks.new(name)
    block.add_line((0, 0), (1, 0))
    for index, tag in enumerate(PART_TAGS):
        block.add_attdef(tag, insert=(0, -index))
    return block


def place_part(
    layout: BaseLayout, block: str, values: dict[str, str], at: tuple[float, float]
) -> None:
    insert = layout.add_blockref(block, at)
    insert.add_auto_attribs(values)


def build_facade_plan(path: Path) -> Path:
    """Two panels, one bracket type, a nested assembly and a dynamic window block."""
    document = new("R2018")
    define_part_block(document, "PANNEAU")
    define_part_block(document, "EQUERRE")
    define_part_block(document, "FENETRE")
    assembly = document.blocks.new("ASSEMBLAGE")
    place_part(
        assembly, "EQUERRE", {"REF": "EQ-40", "DESIGNATION": "Équerre 40", "MATIERE": "ALU"}, (0, 0)
    )
    place_part(
        assembly, "EQUERRE", {"REF": "EQ-40", "DESIGNATION": "Équerre 40", "MATIERE": "ALU"}, (2, 0)
    )

    model = document.modelspace()
    panel = {
        "REF": "P-1200",
        "DESIGNATION": "Panneau composite",
        "LONGUEUR": "1200",
        "MATIERE": "ALU",
        "FINITION": "RAL 7016",
    }
    place_part(model, "PANNEAU", panel, (0, 0))
    place_part(model, "PANNEAU", panel, (0, 10))
    place_part(model, "PANNEAU", {**panel, "REF": "P-900", "LONGUEUR": "900"}, (0, 20))
    model.add_blockref("ASSEMBLAGE", (20, 0))
    _add_dynamic_window(document)
    document.saveas(path)
    return path


def _add_dynamic_window(document: Drawing) -> None:
    document.appids.add(DYNAMIC_BLOCK_APPID)
    anonymous = document.blocks.new_anonymous_block("U")
    anonymous.add_attdef("REF", insert=(0, 0))
    original = document.blocks.get("FENETRE")
    anonymous.block_record.set_xdata(
        DYNAMIC_BLOCK_APPID, [(1005, original.block_record.dxf.handle)]
    )
    insert = document.modelspace().add_blockref(anonymous.name, (40, 0))
    insert.add_auto_attribs({"REF": "F-80"})


def build_facade_plan_revised(path: Path) -> Path:
    """The next index of the same façade: one P-900 removed, a third P-1200, a new P-1500."""
    document = new("R2018")
    define_part_block(document, "PANNEAU")
    define_part_block(document, "EQUERRE")
    assembly = document.blocks.new("ASSEMBLAGE")
    for x in (0, 2, 4):
        place_part(
            assembly,
            "EQUERRE",
            {"REF": "EQ-40", "DESIGNATION": "Équerre 40", "MATIERE": "ALU"},
            (x, 0),
        )
    model = document.modelspace()
    panel = {
        "REF": "P-1200",
        "DESIGNATION": "Panneau composite",
        "LONGUEUR": "1200",
        "MATIERE": "ALU",
        "FINITION": "RAL 7016",
    }
    for y in (0, 10, 20):
        place_part(model, "PANNEAU", panel, (0, y))
    place_part(model, "PANNEAU", {**panel, "REF": "P-1500", "LONGUEUR": "1500"}, (0, 30))
    model.add_blockref("ASSEMBLAGE", (20, 0))
    document.saveas(path)
    return path
