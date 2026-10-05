"""Installs ODA File Converter from the editor's site: winget's manifest points to removed files."""

import tempfile
from pathlib import Path

import anyio
import httpx

from engine.core.errors import EngineError
from engine.setup.commands import CommandOutcome, CommandRunner
from engine.setup.installer_download import DownloadProgress, download_installer
from engine.setup.signature import verify_signature

# Unversioned name: the editor redirects it to the latest release, so it never goes stale.
ODA_MSI_URL = (
    "https://www.opendesign.com/guestfiles/get?filename=ODAFileConverter_QT6_vc16_amd64dll.msi"
)
ODA_NAME = "ODA File Converter"
ODA_SIGNER = "Open Design Alliance"
ODA_MSI_NAME = "ODAFileConverter.msi"
MAX_MSI_BYTES = 500_000_000
MSIEXEC_FLAGS = ("/passive", "/norestart")
MSI_SUCCESS = {0, 3010}
MSI_CANCELLED = 1602
MSI_ANOTHER_INSTALL_RUNNING = 1618
DOWNLOAD_PAGE_HINT = (
    "Cliquez sur « Page de téléchargement », installez ODA File Converter, puis sur "
    "« Analyser à nouveau » : Drawflow le détectera."
)


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
        verify_signature(run, msi, name=ODA_NAME, expected_signer=ODA_SIGNER)
        _check(run(["msiexec", "/i", str(msi), *MSIEXEC_FLAGS]))


async def _download(
    target: Path, on_progress: DownloadProgress, transport: httpx.AsyncBaseTransport | None
) -> None:
    await download_installer(
        ODA_MSI_URL,
        target,
        name=ODA_NAME,
        max_bytes=MAX_MSI_BYTES,
        on_progress=on_progress,
        transport=transport,
    )


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
