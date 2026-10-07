"""Process helpers for tests that need a worker to outlive, or not, its parent."""

import ctypes
import os
import sys
import time
from pathlib import Path

LONG_SLEEP_SECONDS = 30.0
PROCESS_QUERY_LIMITED_INFORMATION = 0x1000
STILL_ACTIVE = 259


def sleep_long(path: Path) -> str:
    """A batch worker that never finishes on its own: only a kill ends it."""
    time.sleep(LONG_SLEEP_SECONDS)
    return path.name


def is_running(pid: int) -> bool:
    if sys.platform == "win32":
        kernel32 = ctypes.WinDLL("kernel32")
        handle = kernel32.OpenProcess(PROCESS_QUERY_LIMITED_INFORMATION, False, pid)
        if not handle:
            return False
        try:
            exit_code = ctypes.c_ulong()
            kernel32.GetExitCodeProcess(handle, ctypes.byref(exit_code))
            return exit_code.value == STILL_ACTIVE
        finally:
            kernel32.CloseHandle(handle)
    try:
        os.kill(pid, 0)
    except ProcessLookupError:
        return False
    except PermissionError:
        return True
    return True
