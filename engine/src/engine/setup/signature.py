"""Checks the Authenticode signature of a downloaded installer before it is executed."""

from pathlib import Path

from engine.core.errors import EngineError
from engine.setup.commands import CommandRunner
from engine.setup.messages import t

POWERSHELL = "powershell"
POWERSHELL_FLAGS = ("-NoProfile", "-NonInteractive", "-Command")
SIGNATURE_SCRIPT = (
    "$signature = Get-AuthenticodeSignature -LiteralPath '{path}'; "
    "Write-Output $signature.Status; Write-Output $signature.SignerCertificate.Subject"
)
VALID_STATUS = "Valid"


class SignatureError(EngineError):
    pass


def verify_signature(run: CommandRunner, path: Path, *, name: str, expected_signer: str) -> None:
    script = SIGNATURE_SCRIPT.format(path=str(path).replace("'", "''"))
    outcome = run([POWERSHELL, *POWERSHELL_FLAGS, script])
    lines = [line.strip() for line in outcome.output.splitlines() if line.strip()]
    if outcome.return_code != 0 or not lines:
        raise SignatureError(
            t("signature.unverifiable", name=name),
            hint=outcome.tail() or t("signature.not_executed_hint"),
        )
    status, subject = lines[0], " ".join(lines[1:])
    if status != VALID_STATUS:
        raise SignatureError(
            t("signature.untrusted", name=name, status=status),
            hint=t("signature.not_executed_hint"),
        )
    if expected_signer.lower() not in subject.lower():
        raise SignatureError(
            t("signature.wrong_signer", name=name, subject=subject, expected=expected_signer),
            hint=t("signature.not_executed_hint"),
        )
