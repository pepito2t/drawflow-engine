from collections.abc import Sequence

import httpx
import pytest

from engine.setup.commands import CommandOutcome
from engine.setup.installer_download import InstallerDownloadError
from engine.setup.oda_installer import ODA_MSI_URL, OdaInstallError, install_oda

MSI_SIZE = 4000
MSI_CANCELLED = 1602
MSI_REBOOT_REQUIRED = 3010


def _site(requested: list[str]) -> httpx.MockTransport:
    def handle(request: httpx.Request) -> httpx.Response:
        requested.append(str(request.url))
        return httpx.Response(200, content=b"x" * MSI_SIZE)

    return httpx.MockTransport(handle)


def test_downloads_the_unversioned_msi_and_reports_each_percent_once() -> None:
    requested: list[str] = []
    progress: list[int] = []
    commands: list[list[str]] = []

    def run(arguments: Sequence[str]) -> CommandOutcome:
        commands.append(list(arguments))
        return CommandOutcome(0, "")

    install_oda(run, progress.append, _site(requested))

    assert requested == [ODA_MSI_URL]
    assert progress == sorted(set(progress))
    assert progress[-1] == 100
    assert commands[0][:2] == ["msiexec", "/i"]
    assert "/passive" in commands[0]


def test_reboot_required_is_a_success() -> None:
    install_oda(lambda _: CommandOutcome(MSI_REBOOT_REQUIRED, ""), lambda _: None, _site([]))


def test_refused_permission_explains_how_to_retry() -> None:
    with pytest.raises(OdaInstallError, match="annulée") as caught:
        install_oda(lambda _: CommandOutcome(MSI_CANCELLED, ""), lambda _: None, _site([]))
    assert caught.value.hint is not None
    assert "autorisation" in caught.value.hint


def test_offline_download_is_readable() -> None:
    def refuse(request: httpx.Request) -> httpx.Response:
        raise httpx.ConnectError("offline", request=request)

    with pytest.raises(InstallerDownloadError, match="impossible"):
        install_oda(lambda _: CommandOutcome(0, ""), lambda _: None, httpx.MockTransport(refuse))
