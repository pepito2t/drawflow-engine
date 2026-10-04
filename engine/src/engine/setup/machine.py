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

    def glob(self, folder: Path, pattern: str) -> list[Path]: ...

    def folder(self, variable: str) -> Path | None:
        """A folder named by an environment variable (ProgramFiles, APPDATA, LOCALAPPDATA)."""
        ...

    @property
    def home(self) -> Path: ...


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

    def glob(self, folder: Path, pattern: str) -> list[Path]:
        return sorted(folder.glob(pattern)) if folder.is_dir() else []

    def folder(self, variable: str) -> Path | None:
        value = os.environ.get(variable)
        return Path(value) if value else None

    @property
    def home(self) -> Path:
        return Path.home()
