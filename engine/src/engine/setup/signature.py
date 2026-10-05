"""Checks the Authenticode signature of a downloaded installer before it is executed."""

from pathlib import Path

from engine.core.errors import EngineError
from engine.setup.commands import CommandRunner

POWERSHELL = "powershell"
POWERSHELL_FLAGS = ("-NoProfile", "-NonInteractive", "-Command")
SIGNATURE_SCRIPT = (
    "$signature = Get-AuthenticodeSignature -LiteralPath '{path}'; "
    "Write-Output $signature.Status; Write-Output $signature.SignerCertificate.Subject"
)
VALID_STATUS = "Valid"
NOT_EXECUTED_HINT = (
    "Il n'a pas été exécuté. Téléchargez l'installeur depuis la page officielle, "
    "ou réessayez plus tard."
)


class SignatureError(EngineError):
    pass


def verify_signature(run: CommandRunner, path: Path, *, name: str, expected_signer: str) -> None:
    script = SIGNATURE_SCRIPT.format(path=str(path).replace("'", "''"))
    outcome = run([POWERSHELL, *POWERSHELL_FLAGS, script])
    lines = [line.strip() for line in outcome.output.splitlines() if line.strip()]
    if outcome.return_code != 0 or not lines:
        raise SignatureError(
            f"{name} : impossible de vérifier la signature de l'installeur.",
            hint=outcome.tail() or NOT_EXECUTED_HINT,
        )
    status, subject = lines[0], " ".join(lines[1:])
    if status != VALID_STATUS:
        raise SignatureError(
            f"{name} : l'installeur téléchargé n'est pas signé par un éditeur de confiance "
            f"({status}).",
            hint=NOT_EXECUTED_HINT,
        )
    if expected_signer.lower() not in subject.lower():
        raise SignatureError(
            f"{name} : l'installeur est signé par « {subject} », pas par {expected_signer}.",
            hint=NOT_EXECUTED_HINT,
        )
