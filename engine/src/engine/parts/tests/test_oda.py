import os
import subprocess
import sys
import threading
import time
from collections.abc import Sequence
from pathlib import Path

import pytest

from engine.core.cache import FileCache
from engine.core.events import Event
from engine.core.settings_models import GeneralSettings
from engine.core.shutdown import hooks
from engine.parts.oda import (
    DwgConversionError,
    OdaConverter,
    OdaNotConfiguredError,
    ensure_dxf,
    require_oda,
    run_command,
)

ODA_ENVIRONMENT_VARIABLE = "ODA_FILE_CONVERTER"
FAILING_PROGRAM = "import sys; sys.stderr.write('Licence refusée'); sys.exit(3)"
SLEEPING_PROGRAM = "import time; time.sleep(30)"
KILL_WAIT_SECONDS = 10.0
PROGRAM_START_SECONDS = 0.5


class FakeOda:
    def __init__(self, produce: bool = True, error: Exception | None = None) -> None:
        self.calls: list[list[str]] = []
        self.produce = produce
        self.error = error

    def __call__(self, arguments: Sequence[str]) -> None:
        self.calls.append(list(arguments))
        if self.error:
            raise self.error
        if self.produce:
            source = Path(arguments[1]) / "plan.dwg"
            (Path(arguments[2]) / "plan.dxf").write_bytes(b"DXF:" + source.read_bytes())


@pytest.fixture
def dwg(tmp_path: Path) -> Path:
    path = tmp_path / "Façade nord é.dwg"
    path.write_bytes(b"DWG")
    return path


def test_converts_through_a_private_folder(tmp_path: Path, dwg: Path) -> None:
    oda = FakeOda()
    target = tmp_path / "out.dxf"

    OdaConverter(Path("ODAFileConverter.exe"), oda).convert(dwg, target)

    assert target.read_bytes() == b"DXF:DWG"
    arguments = oda.calls[0]
    assert arguments[0] == "ODAFileConverter.exe"
    assert arguments[3:] == ["ACAD2018", "DXF", "0", "1", "*.DWG"]


def test_missing_output_is_a_readable_error(tmp_path: Path, dwg: Path) -> None:
    with pytest.raises(DwgConversionError) as caught:
        OdaConverter(Path("oda"), FakeOda(produce=False)).convert(dwg, tmp_path / "out.dxf")

    assert caught.value.file == dwg


@pytest.mark.parametrize(
    "error",
    [
        subprocess.CalledProcessError(1, "oda"),
        subprocess.TimeoutExpired("oda", 1),
        FileNotFoundError("oda"),
    ],
)
def test_process_failures_name_the_plan(tmp_path: Path, dwg: Path, error: Exception) -> None:
    with pytest.raises(DwgConversionError) as caught:
        OdaConverter(Path("oda"), FakeOda(error=error)).convert(dwg, tmp_path / "out.dxf")

    assert caught.value.file == dwg


def test_command_failure_carries_what_the_program_printed() -> None:
    with pytest.raises(subprocess.CalledProcessError) as caught:
        run_command([sys.executable, "-c", FAILING_PROGRAM])

    assert caught.value.returncode == 3
    # The child writes in the platform encoding: compare on the accent-free prefix.
    assert b"Licence refus" in caught.value.stderr


def test_cancelling_the_run_kills_the_converter() -> None:
    errors: list[Exception] = []

    def convert() -> None:
        try:
            run_command([sys.executable, "-c", SLEEPING_PROGRAM])
        except subprocess.CalledProcessError as error:
            errors.append(error)

    thread = threading.Thread(target=convert, daemon=True)
    started = time.monotonic()
    thread.start()
    time.sleep(PROGRAM_START_SECONDS)
    hooks.trigger()
    thread.join(KILL_WAIT_SECONDS)

    assert not thread.is_alive() and len(errors) == 1
    assert time.monotonic() - started < KILL_WAIT_SECONDS


def test_oda_must_be_configured() -> None:
    with pytest.raises(OdaNotConfiguredError) as caught:
        require_oda(GeneralSettings())

    assert caught.value.hint is not None
    assert "Paramètres" in caught.value.hint


def test_oda_path_must_exist(tmp_path: Path) -> None:
    with pytest.raises(OdaNotConfiguredError):
        require_oda(GeneralSettings(oda_converter_path=tmp_path / "absent.exe"))


@pytest.mark.oda
def test_real_oda_conversion(tmp_path: Path) -> None:
    executable = os.environ.get(ODA_ENVIRONMENT_VARIABLE)
    sample = os.environ.get("ODA_SAMPLE_DWG")
    if not executable or not sample:
        pytest.skip("ODA File Converter absent (ODA_FILE_CONVERTER / ODA_SAMPLE_DWG)")
    target = tmp_path / "plan.dxf"

    OdaConverter(Path(executable)).convert(Path(sample), target)

    assert target.stat().st_size > 0


def test_dxf_sources_skip_conversion(tmp_path: Path) -> None:
    dxf = tmp_path / "plan.DXF"
    dxf.write_text("0\nEOF\n", encoding="utf-8")
    oda = FakeOda()
    events: list[Event] = []

    result = ensure_dxf(
        dxf, FileCache(tmp_path / "cache", "dxf"), OdaConverter(Path("oda"), oda), events.append
    )

    assert result == dxf
    assert oda.calls == []


def test_dwg_conversion_is_cached(tmp_path: Path, dwg: Path) -> None:
    oda = FakeOda()
    converter = OdaConverter(Path("oda"), oda)
    cache = FileCache(tmp_path / "cache", "dxf")
    events: list[Event] = []

    first = ensure_dxf(dwg, cache, converter, events.append)
    second = ensure_dxf(dwg, cache, converter, events.append)

    assert first == second
    assert first.read_bytes() == b"DXF:DWG"
    assert len(oda.calls) == 1
