"""In-memory computer for the setup tests: programs on PATH and existing files."""

from dataclasses import dataclass, field
from pathlib import Path

from engine.setup.machine import OperatingSystem

PROGRAM_FILES = Path("C:/Program Files")
APPDATA = Path("C:/Users/dessin/AppData/Roaming")
LOCALAPPDATA = Path("C:/Users/dessin/AppData/Local")
FOLDERS = {"ProgramFiles": PROGRAM_FILES, "APPDATA": APPDATA, "LOCALAPPDATA": LOCALAPPDATA}


@dataclass
class FakeMachine:
    os: OperatingSystem = "windows"
    arch: str = "amd64"
    programs: set[str] = field(default_factory=set)
    files: set[Path] = field(default_factory=set)
    home: Path = Path("/Users/dessin")

    def which(self, program: str) -> Path | None:
        return Path(program) if program in self.programs else None

    def is_file(self, path: Path) -> bool:
        return path in self.files

    def is_dir(self, path: Path) -> bool:
        return any(path == file or path in file.parents for file in self.files)

    def glob(self, folder: Path, pattern: str) -> list[Path]:
        return sorted(file for file in self.files if folder in file.parents)

    def folder(self, variable: str) -> Path | None:
        return FOLDERS.get(variable)
