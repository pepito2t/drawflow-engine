from pathlib import Path

import pytest

from engine.core.errors import OutputWriteError
from engine.modules.hello.adapters import FileSystemGreetingWriter


def test_writes_utf8_in_folder_with_spaces_and_accents(tmp_path: Path) -> None:
    folder = tmp_path / "Dossier de sortie é"

    written = FileSystemGreetingWriter().write_text(folder, "test.txt", "Bonjour Zoé !")

    assert written == folder / "test.txt"
    assert written.read_text(encoding="utf-8") == "Bonjour Zoé !"


def test_existing_file_is_never_overwritten(tmp_path: Path) -> None:
    (tmp_path / "test.txt").write_text("original", encoding="utf-8")

    written = FileSystemGreetingWriter().write_text(tmp_path, "test.txt", "nouveau")

    assert written == tmp_path / "test (2).txt"
    assert (tmp_path / "test.txt").read_text(encoding="utf-8") == "original"


def test_unwritable_target_raises_readable_error(tmp_path: Path) -> None:
    blocking_file = tmp_path / "fichier"
    blocking_file.write_text("", encoding="utf-8")

    with pytest.raises(OutputWriteError) as caught:
        FileSystemGreetingWriter().write_text(blocking_file, "test.txt", "x")

    assert caught.value.file == blocking_file / "test.txt"
    assert caught.value.hint is not None
