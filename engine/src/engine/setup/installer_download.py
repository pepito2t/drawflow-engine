"""Downloads a third-party installer to disk, reporting each percent once."""

from collections.abc import Callable
from pathlib import Path

import httpx

from engine.core.errors import EngineError
from engine.setup.messages import t

DOWNLOAD_TIMEOUT = httpx.Timeout(connect=10.0, read=60.0, write=30.0, pool=10.0)
PERCENT = 100

DownloadProgress = Callable[[int], None]


class InstallerDownloadError(EngineError):
    pass


async def download_installer(
    url: str,
    target: Path,
    *,
    name: str,
    max_bytes: int,
    on_progress: DownloadProgress,
    transport: httpx.AsyncBaseTransport | None = None,
) -> None:
    async with httpx.AsyncClient(
        timeout=DOWNLOAD_TIMEOUT, transport=transport, follow_redirects=True
    ) as http:
        try:
            async with http.stream("GET", url) as response:
                if not response.is_success:
                    raise InstallerDownloadError(
                        t(
                            "installer_download.unavailable",
                            name=name,
                            status=response.status_code,
                        ),
                        hint=t("installer_download.unavailable.hint", name=name),
                    )
                await _save(response, target, name, max_bytes, on_progress)
        except httpx.TransportError as error:
            raise InstallerDownloadError(
                t("installer_download.failed", name=name),
                hint=t("installer_download.failed.hint"),
            ) from error


async def _save(
    response: httpx.Response,
    target: Path,
    name: str,
    max_bytes: int,
    on_progress: DownloadProgress,
) -> None:
    total = int(response.headers.get("content-length", 0))
    received = 0
    reported = -1
    try:
        with target.open("wb") as file:
            async for chunk in response.aiter_bytes():
                received += len(chunk)
                if received > max_bytes:
                    raise InstallerDownloadError(t("installer_download.too_large", name=name))
                file.write(chunk)
                percent = received * PERCENT // total if total else 0
                if percent != reported:
                    reported = percent
                    on_progress(percent)
    except OSError as error:
        raise InstallerDownloadError(
            t("installer_download.save_failed", name=name),
            file=target,
            hint=t("installer_download.save_failed.hint"),
        ) from error
