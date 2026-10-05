"""Installs ODA File Converter from the editor's site: winget's manifest points to removed files."""

import tempfile
from collections.abc import Callable
from pathlib import Path

import anyio
import httpx

from engine.core.errors import EngineError
from engine.setup.commands import CommandOutcome, CommandRunner

# Unversioned name: the editor redirects it to the latest release, so it never goes stale.
ODA_MSI_URL = (
    "https://www.opendesign.com/guestfiles/get?filename=ODAFileConverter_QT6_vc16_amd64dll.msi"
)
ODA_MSI_NAME = "ODAFileConverter.msi"
DOWNLOAD_TIMEOUT = httpx.Timeout(connect=10.0, read=60.0, write=30.0, pool=10.0)
MAX_MSI_BYTES = 500_000_000
MSIEXEC_FLAGS = ("/passive", "/norestart")
MSI_SUCCESS = {0, 3010}
MSI_CANCELLED = 1602
MSI_ANOTHER_INSTALL_RUNNING = 1618
DOWNLOAD_PAGE_HINT = (
    "Cliquez sur « Page de téléchargement », installez ODA File Converter, puis sur "
    "« Analyser à nouveau » : Drawflow le détectera."
)

PERCENT = 100

DownloadProgress = Callable[[int], None]


class OdaInstallError(EngineError):
    pass


def install_oda(
    run: CommandRunner,
    on_progress: DownloadProgress,
    transport: httpx.AsyncBaseTransport | None = None,
) -> None:
    with tempfile.TemporaryDirectory(prefix="drawflow-oda-") as folder:
        msi = Path(folder) / ODA_MSI_NAME
        anyio.run(_download, msi, on_progress, transport)
        _check(run(["msiexec", "/i", str(msi), *MSIEXEC_FLAGS]))


async def _download(
    target: Path, on_progress: DownloadProgress, transport: httpx.AsyncBaseTransport | None
) -> None:
    async with httpx.AsyncClient(
        timeout=DOWNLOAD_TIMEOUT, transport=transport, follow_redirects=True
    ) as http:
        try:
            async with http.stream("GET", ODA_MSI_URL) as response:
                _check_response(response)
                await _save(response, target, on_progress)
        except httpx.TransportError as error:
            raise OdaInstallError(
                "Téléchargement d'ODA File Converter impossible.",
                hint="Vérifiez la connexion Internet, puis réessayez.",
            ) from error


def _check_response(response: httpx.Response) -> None:
    if not response.is_success:
        raise OdaInstallError(
            f"Le site d'ODA ne fournit plus l'installeur (HTTP {response.status_code}).",
            hint=DOWNLOAD_PAGE_HINT,
        )


async def _save(response: httpx.Response, target: Path, on_progress: DownloadProgress) -> None:
    total = int(response.headers.get("content-length", 0))
    received = 0
    reported = -1
    with target.open("wb") as file:
        async for chunk in response.aiter_bytes():
            received += len(chunk)
            if received > MAX_MSI_BYTES:
                raise OdaInstallError("L'installeur d'ODA téléchargé est anormalement volumineux.")
            file.write(chunk)
            percent = received * PERCENT // total if total else 0
            if percent != reported:
                reported = percent
                on_progress(percent)


def _check(outcome: CommandOutcome) -> None:
    if outcome.return_code in MSI_SUCCESS:
        return
    if outcome.return_code == MSI_CANCELLED:
        raise OdaInstallError(
            "L'installation d'ODA File Converter a été annulée.",
            hint="Relancez l'installation et acceptez la demande d'autorisation de Windows.",
        )
    if outcome.return_code == MSI_ANOTHER_INSTALL_RUNNING:
        raise OdaInstallError(
            "Une autre installation est en cours sur ce poste.",
            hint="Attendez qu'elle se termine, puis réessayez.",
        )
    raise OdaInstallError(
        f"L'installation d'ODA File Converter a échoué (code {outcome.return_code}).",
        hint=outcome.tail() or DOWNLOAD_PAGE_HINT,
    )
