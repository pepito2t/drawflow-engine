from collections.abc import AsyncIterator
from pathlib import Path

import anyio
import httpx
import pytest

from engine.setup.installer_download import InstallerDownloadError, download_installer

URL = "https://example.test/setup.msi"
BODY = b"x" * 1000


async def _chunks() -> AsyncIterator[bytes]:
    yield BODY[:500]
    yield BODY[500:]


def _site() -> httpx.MockTransport:
    # A streamed body carries no Content-Length, like some download mirrors.
    return httpx.MockTransport(lambda _: httpx.Response(200, content=_chunks()))


def _download(target: Path, transport: httpx.MockTransport, max_bytes: int = 10_000) -> list[int]:
    progress: list[int] = []
    anyio.run(
        lambda: download_installer(
            URL,
            target,
            name="Outil",
            max_bytes=max_bytes,
            on_progress=progress.append,
            transport=transport,
        )
    )
    return progress


def test_download_without_content_length_still_completes(tmp_path: Path) -> None:
    target = tmp_path / "setup.msi"

    progress = _download(target, _site())

    assert target.read_bytes() == BODY
    assert progress == [0]


def test_download_larger_than_allowed_is_refused(tmp_path: Path) -> None:
    with pytest.raises(InstallerDownloadError, match="volumineux"):
        _download(tmp_path / "setup.msi", _site(), max_bytes=100)


def test_disk_error_is_readable(tmp_path: Path) -> None:
    unwritable = tmp_path / "absent" / "setup.msi"

    with pytest.raises(InstallerDownloadError, match="disque") as caught:
        _download(unwritable, _site())
    assert caught.value.file == unwritable
    assert caught.value.hint is not None
