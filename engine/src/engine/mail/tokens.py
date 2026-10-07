"""The Microsoft session kept between launches: refresh token only, next to the settings."""

import getpass
import json
import os
import stat
import subprocess
from collections.abc import Callable, Sequence
from pathlib import Path

from pydantic import BaseModel, ConfigDict, ValidationError

from engine.core.errors import OutputWriteError
from engine.core.json_files import write_json_atomically
from engine.mail.messages import t

TOKEN_FILE = "mail-session.json"
OWNER_ONLY = stat.S_IRUSR | stat.S_IWUSR
ICACLS = "icacls"
WINDOWS = "nt"

AclRunner = Callable[[Sequence[str]], bool]


class MailSession(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    account: str
    refresh_token: str
    last_fetch_at: str | None = None
    protected: bool = True


def icacls_arguments(path: Path) -> list[str]:
    """Owner only: drop inherited rights, grant full control to the current user alone."""
    return [ICACLS, str(path), "/inheritance:r", "/grant:r", f"{getpass.getuser()}:F"]


def run_icacls(arguments: Sequence[str]) -> bool:
    try:
        completed = subprocess.run(
            list(arguments),
            capture_output=True,
            check=False,
            creationflags=int(getattr(subprocess, "CREATE_NO_WINDOW", 0)),
        )
    except OSError:
        return False
    return completed.returncode == 0


class SessionStore:
    def __init__(self, settings_file: Path, acl: AclRunner | None = None) -> None:
        self.path = settings_file.parent / TOKEN_FILE
        # POSIX restricts with chmod; Windows needs an ACL command.
        self._acl = acl if acl is not None else (run_icacls if os.name == WINDOWS else None)

    def read(self) -> MailSession | None:
        if not self.path.is_file():
            return None
        try:
            return MailSession.model_validate(json.loads(self.path.read_text(encoding="utf-8")))
        except (OSError, json.JSONDecodeError, ValidationError):
            # An unreadable session only means signing in again.
            return None

    def write(self, session: MailSession) -> None:
        try:
            self._write(session)
            if not self._restrict():
                self._write(session.model_copy(update={"protected": False}))
        except OSError as error:
            raise OutputWriteError(t("tokens.save_failed"), file=self.path) from error

    def _write(self, session: MailSession) -> None:
        # Born owner-only and swapped in whole: never readable by others, never half-written.
        write_json_atomically(self.path, session.model_dump(mode="json"), mode=OWNER_ONLY)

    def _restrict(self) -> bool:
        if self._acl is None:
            self.path.chmod(OWNER_ONLY)
            return True
        return self._acl(icacls_arguments(self.path))

    def clear(self) -> None:
        try:
            self.path.unlink(missing_ok=True)
        except OSError as error:
            raise OutputWriteError(t("tokens.clear_failed"), file=self.path) from error
