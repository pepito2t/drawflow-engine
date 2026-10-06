import shutil
import subprocess
import sys
from collections.abc import Callable, Sequence
from pathlib import Path
from tempfile import TemporaryDirectory

from engine.core.cache import FileCache
from engine.core.errors import EngineError
from engine.core.events import Emit
from engine.core.settings_models import GeneralSettings
from engine.parts.messages import t

ODA_OUTPUT_VERSION = "ACAD2018"
ODA_OUTPUT_TYPE = "DXF"
ODA_NO_RECURSION = "0"
ODA_AUDIT = "1"
ODA_INPUT_FILTER = "*.DWG"
CONVERSION_TIMEOUT_SECONDS = 300
WORK_INPUT_STEM = "plan"
DXF_SUFFIX = ".dxf"
DWG_SUFFIX = ".dwg"
CONFIGURE_ODA_HINT = t("oda.configure_hint")
# Hides the console window ODA would otherwise open on Windows.
WINDOWS_NO_WINDOW_FLAG = 0x08000000

CommandRunner = Callable[[Sequence[str]], None]


class OdaNotConfiguredError(EngineError):
    pass


class DwgConversionError(EngineError):
    pass


def require_oda(general: GeneralSettings) -> Path:
    executable = general.oda_converter_path
    if executable is None:
        raise OdaNotConfiguredError(t("oda.not_configured"), hint=CONFIGURE_ODA_HINT)
    if not executable.is_file():
        raise OdaNotConfiguredError(
            t("oda.not_found"),
            file=executable,
            hint=CONFIGURE_ODA_HINT,
        )
    return executable


def run_command(arguments: Sequence[str]) -> None:
    flags = WINDOWS_NO_WINDOW_FLAG if sys.platform == "win32" else 0
    subprocess.run(
        list(arguments),
        check=True,
        capture_output=True,
        timeout=CONVERSION_TIMEOUT_SECONDS,
        creationflags=flags,
    )


class OdaConverter:
    """Converts one DWG to DXF; ODA only works on folders, so each file gets its own."""

    def __init__(self, executable: Path, runner: CommandRunner = run_command) -> None:
        self._executable = executable
        self._runner = runner

    def convert(self, source: Path, target: Path) -> None:
        with TemporaryDirectory(prefix="drawflow-oda-") as workdir:
            input_folder = Path(workdir) / "in"
            output_folder = Path(workdir) / "out"
            input_folder.mkdir()
            output_folder.mkdir()
            shutil.copyfile(source, input_folder / f"{WORK_INPUT_STEM}{DWG_SUFFIX}")
            self._run(source, input_folder, output_folder)
            produced = output_folder / f"{WORK_INPUT_STEM}{DXF_SUFFIX}"
            if not produced.is_file():
                raise DwgConversionError(
                    t("oda.not_converted"), file=source, hint=t("oda.not_converted_hint")
                )
            shutil.move(produced, target)

    def _run(self, source: Path, input_folder: Path, output_folder: Path) -> None:
        arguments = [
            str(self._executable),
            str(input_folder),
            str(output_folder),
            ODA_OUTPUT_VERSION,
            ODA_OUTPUT_TYPE,
            ODA_NO_RECURSION,
            ODA_AUDIT,
            ODA_INPUT_FILTER,
        ]
        try:
            self._runner(arguments)
        except subprocess.TimeoutExpired as error:
            raise DwgConversionError(
                t("oda.timeout"), file=source, hint=t("oda.timeout_hint")
            ) from error
        except (subprocess.CalledProcessError, OSError) as error:
            raise DwgConversionError(
                t("oda.failed"), file=source, hint=CONFIGURE_ODA_HINT
            ) from error


def is_dxf(path: Path) -> bool:
    return path.suffix.lower() == DXF_SUFFIX


def ensure_dxf(source: Path, cache: FileCache, converter: OdaConverter, emit: Emit) -> Path:
    """DXF files are read as-is; DWG files are converted once and served from the cache."""
    if is_dxf(source):
        return source
    return cache.get_or_create(source, DXF_SUFFIX, converter.convert, emit)
