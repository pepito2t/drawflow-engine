from collections.abc import Iterator, Mapping
from dataclasses import dataclass
from pathlib import Path

from ezdxf.document import Drawing
from ezdxf.entities.insert import Insert
from ezdxf.filemanagement import readfile
from ezdxf.lldxf.const import DXFError

from engine.core.errors import EngineError

MAX_NESTING_DEPTH = 8
ANONYMOUS_BLOCK_PREFIX = "*U"
DYNAMIC_BLOCK_APPID = "AcDbBlockRepBTag"
HANDLE_GROUP_CODE = 1005


class DxfReadError(EngineError):
    pass


@dataclass(frozen=True)
class RawPart:
    block: str
    attributes: Mapping[str, str]
    count: int
    layout: str
    source: Path


def read_parts(dxf_path: Path, source: Path) -> list[RawPart]:
    """Lists every block reference with its attributes, nested blocks included."""
    document = _open(dxf_path, source)
    parts: list[RawPart] = []
    for layout in document.layouts:
        for insert in layout.query("INSERT"):
            if isinstance(insert, Insert):
                parts.extend(_collect(document, insert, layout.name, source, depth=0))
    return parts


def effective_block_name(document: Drawing, name: str) -> str:
    """Dynamic blocks are stored as anonymous '*U' copies that point back to their original."""
    if not name.upper().startswith(ANONYMOUS_BLOCK_PREFIX):
        return name
    block = document.blocks.get(name)
    if block is None or block.block_record is None:
        return name
    record = block.block_record
    if not record.has_xdata(DYNAMIC_BLOCK_APPID):
        return name
    for tag in record.get_xdata(DYNAMIC_BLOCK_APPID):
        if tag.code == HANDLE_GROUP_CODE:
            original = document.entitydb.get(str(tag.value))
            if original is not None:
                return str(original.dxf.name)
    return name


def _open(dxf_path: Path, source: Path) -> Drawing:
    try:
        return readfile(dxf_path)
    except (OSError, DXFError) as error:
        raise DxfReadError(
            "Le plan est illisible.",
            file=source,
            hint="Vérifiez qu'il s'ouvre dans AutoCAD, puis réenregistrez-le.",
        ) from error


def _collect(
    document: Drawing, insert: Insert, layout: str, source: Path, depth: int
) -> Iterator[RawPart]:
    yield RawPart(
        block=effective_block_name(document, insert.dxf.name),
        attributes={attrib.dxf.tag.upper(): attrib.dxf.text.strip() for attrib in insert.attribs},
        count=insert.mcount,
        layout=layout,
        source=source,
    )
    if depth >= MAX_NESTING_DEPTH:
        return
    definition = document.blocks.get(insert.dxf.name)
    if definition is None:
        return
    for nested in definition.query("INSERT"):
        if isinstance(nested, Insert):
            yield from _collect(document, nested, layout, source, depth + 1)
