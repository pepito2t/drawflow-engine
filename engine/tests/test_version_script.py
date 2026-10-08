import importlib.util
import os
import subprocess
import sys
from pathlib import Path
from types import ModuleType

SCRIPT = Path(__file__).resolve().parents[2] / "scripts" / "version.py"
WINDOWS_CONSOLE_ENCODING = "cp1252"


def load_script() -> ModuleType:
    spec = importlib.util.spec_from_file_location("version_script", SCRIPT)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    # Dataclasses look their module up in sys.modules while the class is being built.
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def test_release_notes_survive_a_windows_console_encoding() -> None:
    script = load_script()
    expected = script.release_notes(script.current_version()) + "\n"
    environment = {**os.environ, "PYTHONIOENCODING": WINDOWS_CONSOLE_ENCODING}

    completed = subprocess.run(
        [sys.executable, str(SCRIPT), "notes"],
        capture_output=True,
        env=environment,
        check=False,
    )

    assert completed.returncode == 0, completed.stderr.decode("utf-8", errors="replace")
    assert completed.stdout.decode("utf-8").replace("\r\n", "\n") == expected
