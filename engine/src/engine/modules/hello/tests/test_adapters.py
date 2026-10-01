from pathlib import Path

import pytest

from engine.core.errors import OutputWriteError
from engine.modules.hello.adapters import FileSystemGreetingWriter


def test_writes_utf8_in_folder_with_spaces_and_accents(tmp_path: Path) -> None:
    target = tmp_path / "Dossier de sortie é" / "bonjour.txt"

    FileSystemGreetingWriter().write_text(target, "Bonjour Zoé !")

    assert target.read_text(encoding="utf-8") == "Bonjour Zoé !"


def test_unwritable_target_raises_readable_error(tmp_path: Path) -> None:
    blocking_file = tmp_path / "fichier"
    blocking_file.write_text("", encoding="utf-8")

    with pytest.raises(OutputWriteError) as caught:
        FileSystemGreetingWriter().write_text(blocking_file / "bonjour.txt", "x")

    assert caught.value.file == blocking_file / "bonjour.txt"
    assert caught.value.hint is not None
