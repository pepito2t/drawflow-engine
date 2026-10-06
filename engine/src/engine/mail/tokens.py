"""The Microsoft session kept between launches: refresh token only, next to the settings."""

import json
import os
import stat
from pathlib import Path

from pydantic import BaseModel, ConfigDict, ValidationError

from engine.core.errors import OutputWriteError
from engine.mail.messages import t

TOKEN_FILE = "mail-session.json"
OWNER_ONLY = stat.S_IRUSR | stat.S_IWUSR


class MailSession(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    account: str
    refresh_token: str
    last_fetch_at: str | None = None


class SessionStore:
    def __init__(self, settings_file: Path) -> None:
        self.path = settings_file.parent / TOKEN_FILE

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
            self.path.parent.mkdir(parents=True, exist_ok=True)
            self.path.write_text(session.model_dump_json(indent=2), encoding="utf-8")
            if os.name != "nt":
                self.path.chmod(OWNER_ONLY)
        except OSError as error:
            raise OutputWriteError(t("tokens.save_failed"), file=self.path) from error

    def clear(self) -> None:
        try:
            self.path.unlink(missing_ok=True)
        except OSError as error:
            raise OutputWriteError(t("tokens.clear_failed"), file=self.path) from error
