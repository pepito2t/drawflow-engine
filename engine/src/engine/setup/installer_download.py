"""Downloads a third-party installer to disk, reporting each percent once."""

from collections.abc import Callable
from pathlib import Path

import httpx

from engine.core.errors import EngineError

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
                        f"{name} : l'installeur n'est plus disponible sur le site officiel "
                        f"(HTTP {response.status_code}).",
                        hint=f"Cliquez sur « Page de téléchargement », installez {name}, puis "
                        "sur « Analyser à nouveau » : Drawflow le détectera.",
                    )
                await _save(response, target, name, max_bytes, on_progress)
        except httpx.TransportError as error:
            raise InstallerDownloadError(
                f"{name} : téléchargement impossible.",
                hint="Vérifiez la connexion Internet, puis réessayez.",
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
    with target.open("wb") as file:
        async for chunk in response.aiter_bytes():
            received += len(chunk)
            if received > max_bytes:
                raise InstallerDownloadError(
                    f"{name} : l'installeur téléchargé est anormalement volumineux."
                )
            file.write(chunk)
            percent = received * PERCENT // total if total else 0
            if percent != reported:
                reported = percent
                on_progress(percent)
