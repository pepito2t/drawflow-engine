"""Minimal PDF writer: positioned Helvetica text, optional embedded files."""

from collections.abc import Sequence
from dataclasses import dataclass, field
from pathlib import Path

A4_WIDTH = 595
A4_HEIGHT = 842
FONT_SIZE = 10


@dataclass(frozen=True)
class TextItem:
    x: float
    y_from_top: float
    text: str


@dataclass
class PdfSpec:
    pages: list[list[TextItem]] = field(default_factory=list)
    attachments: dict[str, bytes] = field(default_factory=dict)


def write_pdf(path: Path, spec: PdfSpec) -> Path:
    objects: list[bytes] = []
    font_id = _add(
        objects,
        b"<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica /Encoding /WinAnsiEncoding >>",
    )
    pages_id = len(objects) + 1
    objects.append(b"")
    page_ids = [_add_page(objects, items, pages_id, font_id) for items in spec.pages]
    kids = " ".join(f"{page} 0 R" for page in page_ids).encode()
    objects[pages_id - 1] = (
        b"<< /Type /Pages /Kids [" + kids + b"] /Count " + str(len(page_ids)).encode() + b" >>"
    )
    names = _add_attachments(objects, spec.attachments)
    catalog = b"<< /Type /Catalog /Pages " + str(pages_id).encode() + b" 0 R" + names + b" >>"
    catalog_id = _add(objects, catalog)
    path.write_bytes(_serialize(objects, catalog_id))
    return path


def _add(objects: list[bytes], body: bytes) -> int:
    objects.append(body)
    return len(objects)


def _add_page(objects: list[bytes], items: Sequence[TextItem], pages_id: int, font_id: int) -> int:
    commands = b"".join(
        b"BT /F1 %d Tf %.1f %.1f Td (%s) Tj ET\n"
        % (FONT_SIZE, item.x, A4_HEIGHT - item.y_from_top, _escape(item.text))
        for item in items
    )
    content_id = _add(
        objects, b"<< /Length %d >>\nstream\n%s\nendstream" % (len(commands), commands)
    )
    page = (
        b"<< /Type /Page /Parent %d 0 R /MediaBox [0 0 %d %d] "
        b"/Resources << /Font << /F1 %d 0 R >> >> /Contents %d 0 R >>"
    )
    return _add(objects, page % (pages_id, A4_WIDTH, A4_HEIGHT, font_id, content_id))


def _add_attachments(objects: list[bytes], attachments: dict[str, bytes]) -> bytes:
    if not attachments:
        return b""
    entries = b""
    for name, content in attachments.items():
        stream_id = _add(
            objects,
            b"<< /Type /EmbeddedFile /Length %d >>\nstream\n%s\nendstream"
            % (len(content), content),
        )
        spec_id = _add(
            objects,
            b"<< /Type /Filespec /F (%s) /UF (%s) /EF << /F %d 0 R >> >>"
            % (_escape(name), _escape(name), stream_id),
        )
        entries += b"(%s) %d 0 R " % (_escape(name), spec_id)
    return b" /Names << /EmbeddedFiles << /Names [" + entries + b"] >> >>"


def _escape(text: str) -> bytes:
    return text.encode("cp1252").replace(b"\\", b"\\\\").replace(b"(", b"\\(").replace(b")", b"\\)")


def _serialize(objects: list[bytes], root_id: int) -> bytes:
    output = bytearray(b"%PDF-1.7\n")
    offsets = []
    for number, body in enumerate(objects, start=1):
        offsets.append(len(output))
        output += b"%d 0 obj\n%s\nendobj\n" % (number, body)
    xref = len(output)
    output += b"xref\n0 %d\n0000000000 65535 f \n" % (len(objects) + 1)
    output += b"".join(b"%010d 00000 n \n" % offset for offset in offsets)
    output += b"trailer\n<< /Size %d /Root %d 0 R >>\nstartxref\n%d\n%%%%EOF\n" % (
        len(objects) + 1,
        root_id,
        xref,
    )
    return bytes(output)
