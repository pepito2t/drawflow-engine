"""Something off in a file that did not stop the run: where it is and what to do about it."""

from collections.abc import Iterable
from dataclasses import dataclass
from pathlib import Path

from engine.core.events import Emit, WarningEvent


@dataclass(frozen=True)
class Anomaly:
    message: str
    location: str | None = None
    hint: str | None = None

    def within(self, container: str) -> "Anomaly":
        """The same anomaly seen from one level up (a workbook inside a PDF, a sheet…)."""
        location = container if self.location is None else f"{container}, {self.location}"
        return Anomaly(self.message, location, self.hint)


def emit_anomalies(emit: Emit, anomalies: Iterable[Anomaly], file: Path | None) -> None:
    for anomaly in anomalies:
        emit(
            WarningEvent(
                message=anomaly.message,
                file=None if file is None else str(file),
                location=anomaly.location,
                hint=anomaly.hint,
            )
        )
