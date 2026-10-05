from collections.abc import Sequence
from pathlib import Path

import pytest

from engine.setup.commands import CommandOutcome
from engine.setup.signature import SignatureError, verify_signature

INSTALLER = Path("C:/Temp/drawflow-oda/ODA'File.msi")


def _powershell(code: int, output: str) -> tuple[list[list[str]], object]:
    commands: list[list[str]] = []

    def run(arguments: Sequence[str]) -> CommandOutcome:
        commands.append(list(arguments))
        return CommandOutcome(code, output)

    return commands, run


def test_valid_signature_from_the_expected_publisher_passes() -> None:
    commands, run = _powershell(0, "Valid\nCN=Open Design Alliance, O=Open Design Alliance\n")

    verify_signature(run, INSTALLER, name="ODA", expected_signer="Open Design Alliance")

    assert commands[0][:2] == ["powershell", "-NoProfile"]
    assert "ODA''File.msi" in commands[0][-1]


def test_unsigned_installer_is_refused() -> None:
    _, run = _powershell(0, "NotSigned\n")

    with pytest.raises(SignatureError, match="NotSigned"):
        verify_signature(run, INSTALLER, name="ODA", expected_signer="Open Design Alliance")


def test_valid_signature_from_another_publisher_is_refused() -> None:
    _, run = _powershell(0, "Valid\nCN=Someone Else\n")

    with pytest.raises(SignatureError, match="Someone Else"):
        verify_signature(run, INSTALLER, name="ODA", expected_signer="Open Design Alliance")


def test_unavailable_check_is_readable() -> None:
    _, run = _powershell(1, "powershell : terme non reconnu")

    with pytest.raises(SignatureError, match="impossible de vérifier") as caught:
        verify_signature(run, INSTALLER, name="ODA", expected_signer="Open Design Alliance")
    assert caught.value.hint is not None
    assert "non reconnu" in caught.value.hint
