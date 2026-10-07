"""Windows long and UNC paths, applied only where the operating system is called."""

import errno
import ntpath
import sys
from pathlib import Path

from engine.core.messages import t

# MAX_PATH is 260 characters, terminating null included.
WINDOWS_MAX_PATH_LENGTH = 259
EXTENDED_PREFIX = "\\\\?\\"
EXTENDED_UNC_PREFIX = "\\\\?\\UNC\\"
DEVICE_PREFIX = "\\\\.\\"
UNC_PREFIX = "\\\\"
DRIVE_SEPARATOR = ":"
ERROR_FILENAME_EXCED_RANGE = 206


def running_on_windows() -> bool:
    return sys.platform == "win32"


def extended_path(path: Path) -> Path:
    """The form to hand to a system call, never to display or emit.

    On Windows the extended-length prefix lifts the 260-character limit; elsewhere it is identity.
    """
    if not running_on_windows():
        return path
    return Path(extended_form(ntpath.abspath(str(path))))


def extended_form(text: str) -> str:
    """Prefixes an absolute Windows path; any other path is returned unchanged."""
    if text.startswith((EXTENDED_PREFIX, DEVICE_PREFIX)):
        return text
    normalized = ntpath.normpath(text)
    if normalized.startswith(UNC_PREFIX):
        return EXTENDED_UNC_PREFIX + normalized.removeprefix(UNC_PREFIX)
    drive, _ = ntpath.splitdrive(normalized)
    if drive.endswith(DRIVE_SEPARATOR) and ntpath.isabs(normalized):
        return EXTENDED_PREFIX + normalized
    return text


def is_path_too_long(path: Path, error: OSError) -> bool:
    if error.errno == errno.ENAMETOOLONG:
        return True
    if getattr(error, "winerror", None) == ERROR_FILENAME_EXCED_RANGE:
        return True
    return running_on_windows() and len(str(path)) > WINDOWS_MAX_PATH_LENGTH


def write_failure_text(path: Path, error: OSError, message: str, hint: str) -> tuple[str, str]:
    """Message and hint for a failed write; a path that is too long is named as the cause."""
    if not is_path_too_long(path, error):
        return message, hint
    too_long_hint = t("paths.too_long_hint", length=len(str(path)), limit=WINDOWS_MAX_PATH_LENGTH)
    return t("paths.too_long"), too_long_hint
