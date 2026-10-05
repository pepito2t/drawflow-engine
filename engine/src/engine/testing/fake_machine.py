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
    memory: int | None = None
    folders: dict[str, Path] = field(default_factory=lambda: dict(FOLDERS))
    contents: dict[Path, str] = field(default_factory=dict)

    def which(self, program: str) -> Path | None:
        return Path(program) if program in self.programs else None

    def is_file(self, path: Path) -> bool:
        return path in self.files or path in self.contents

    def read_text(self, path: Path) -> str | None:
        return self.contents.get(path)

    def is_dir(self, path: Path) -> bool:
        known = self.files | set(self.contents)
        return any(path == file or path in file.parents for file in known)

    def glob(self, folder: Path, pattern: str) -> list[Path]:
        return sorted(file for file in self.files | set(self.contents) if folder in file.parents)

    @property
    def memory_bytes(self) -> int | None:
        return self.memory

    def folder(self, variable: str) -> Path | None:
        return self.folders.get(variable)
