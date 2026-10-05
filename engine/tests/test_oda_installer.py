from collections.abc import Sequence

import httpx
import pytest

from engine.setup.commands import CommandOutcome, CommandRunner
from engine.setup.installer_download import InstallerDownloadError
from engine.setup.oda_installer import ODA_MSI_URL, OdaInstallError, install_oda
from engine.setup.signature import SignatureError

MSI_SIZE = 4000
MSI_CANCELLED = 1602
MSI_REBOOT_REQUIRED = 3010


def _site(requested: list[str]) -> httpx.MockTransport:
    def handle(request: httpx.Request) -> httpx.Response:
        requested.append(str(request.url))
        return httpx.Response(200, content=b"x" * MSI_SIZE)

    return httpx.MockTransport(handle)


SIGNED = "Valid\nCN=Open Design Alliance"


def _windows(msiexec_code: int, signature: str = SIGNED) -> tuple[list[list[str]], CommandRunner]:
    commands: list[list[str]] = []

    def run(arguments: Sequence[str]) -> CommandOutcome:
        commands.append(list(arguments))
        if arguments[0] == "powershell":
            return CommandOutcome(0, signature)
        return CommandOutcome(msiexec_code, "")

    return commands, run


def test_downloads_the_unversioned_msi_and_reports_each_percent_once() -> None:
    requested: list[str] = []
    progress: list[int] = []
    commands, run = _windows(0)

    install_oda(run, progress.append, _site(requested))

    assert requested == [ODA_MSI_URL]
    assert progress == sorted(set(progress))
    assert progress[-1] == 100
    assert commands[-1][:2] == ["msiexec", "/i"]
    assert "/passive" in commands[-1]


def test_unsigned_installer_is_never_executed() -> None:
    commands, run = _windows(0, signature="NotSigned")

    with pytest.raises(SignatureError, match="éditeur de confiance"):
        install_oda(run, lambda _: None, _site([]))
    assert all(command[0] != "msiexec" for command in commands)


def test_reboot_required_is_a_success() -> None:
    install_oda(_windows(MSI_REBOOT_REQUIRED)[1], lambda _: None, _site([]))


def test_refused_permission_explains_how_to_retry() -> None:
    with pytest.raises(OdaInstallError, match="annulée") as caught:
        install_oda(_windows(MSI_CANCELLED)[1], lambda _: None, _site([]))
    assert caught.value.hint is not None
    assert "autorisation" in caught.value.hint


def test_offline_download_is_readable() -> None:
    def refuse(request: httpx.Request) -> httpx.Response:
        raise httpx.ConnectError("offline", request=request)

    with pytest.raises(InstallerDownloadError, match="impossible"):
        install_oda(_windows(0)[1], lambda _: None, httpx.MockTransport(refuse))
