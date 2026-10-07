from pathlib import Path

import pytest

from engine.core.cache import file_digest
from engine.modules.soumission.settings import SoumissionSettings
from engine.modules.soumission.tests.workbooks import write_submission
from engine.modules.soumission.worker import SourceReadError, read_submission


def test_the_worker_returns_the_content_with_its_digest(tmp_path: Path) -> None:
    path = write_submission(tmp_path / "offre é.xlsx")

    read = read_submission(path, settings=SoumissionSettings())

    assert read.digest == file_digest(path)
    assert [table.sheet for table in read.content.tables] == ["Offre"]


def test_a_vanished_file_is_a_readable_error_naming_it(tmp_path: Path) -> None:
    gone = tmp_path / "disparue.xlsx"

    with pytest.raises(SourceReadError) as caught:
        read_submission(gone, settings=SoumissionSettings())

    assert caught.value.file == gone
    assert "introuvable" in caught.value.message and caught.value.hint is not None
