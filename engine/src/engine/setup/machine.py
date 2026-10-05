"""Where things live on this computer: the only part of the setup scan that touches the system."""

import os
import platform
import shutil
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Literal, Protocol

OperatingSystem = Literal["windows", "macos", "linux"]


class Machine(Protocol):
    @property
    def os(self) -> OperatingSystem: ...

    @property
    def arch(self) -> str: ...

    def which(self, program: str) -> Path | None: ...

    def is_file(self, path: Path) -> bool: ...

    def is_dir(self, path: Path) -> bool: ...

    def read_text(self, path: Path) -> str | None: ...

    def glob(self, folder: Path, pattern: str) -> list[Path]: ...

    def folder(self, variable: str) -> Path | None:
        """A folder named by an environment variable (ProgramFiles, APPDATA, LOCALAPPDATA)."""
        ...

    @property
    def home(self) -> Path: ...

    @property
    def memory_bytes(self) -> int | None:
        """Installed RAM, or None when the system does not tell."""
        ...


@dataclass(frozen=True)
class LocalMachine:
    @property
    def os(self) -> OperatingSystem:
        if sys.platform == "win32":
            return "windows"
        return "macos" if sys.platform == "darwin" else "linux"

    @property
    def arch(self) -> str:
        return platform.machine().lower()

    def which(self, program: str) -> Path | None:
        found = shutil.which(program)
        return Path(found) if found else None

    def is_file(self, path: Path) -> bool:
        return path.is_file()

    def is_dir(self, path: Path) -> bool:
        return path.is_dir()

    def read_text(self, path: Path) -> str | None:
        try:
            return path.read_text(encoding="utf-8")
        except (OSError, UnicodeDecodeError):
            return None

    def glob(self, folder: Path, pattern: str) -> list[Path]:
        return sorted(folder.glob(pattern)) if folder.is_dir() else []

    def folder(self, variable: str) -> Path | None:
        value = os.environ.get(variable)
        return Path(value) if value else None

    @property
    def home(self) -> Path:
        return Path.home()

    @property
    def memory_bytes(self) -> int | None:
        if sys.platform == "win32":
            return _windows_memory_bytes()
        try:
            return os.sysconf("SC_PAGE_SIZE") * os.sysconf("SC_PHYS_PAGES")
        except (ValueError, OSError):
            return None


def _windows_memory_bytes() -> int | None:
    if sys.platform != "win32":
        return None
    import ctypes

    class MemoryStatus(ctypes.Structure):
        _fields_ = [  # MEMORYSTATUSEX layout
            ("length", ctypes.c_ulong),
            ("memory_load", ctypes.c_ulong),
            ("total_physical", ctypes.c_ulonglong),
            ("available_physical", ctypes.c_ulonglong),
            ("total_page_file", ctypes.c_ulonglong),
            ("available_page_file", ctypes.c_ulonglong),
            ("total_virtual", ctypes.c_ulonglong),
            ("available_virtual", ctypes.c_ulonglong),
            ("available_extended_virtual", ctypes.c_ulonglong),
        ]

    status = MemoryStatus()
    status.length = ctypes.sizeof(MemoryStatus)
    if not ctypes.windll.kernel32.GlobalMemoryStatusEx(ctypes.byref(status)):
        return None
    return int(status.total_physical)
