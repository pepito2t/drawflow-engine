import json
import subprocess
import sys
from pathlib import Path
from typing import Any

from engine.cli import EXIT_BUSINESS_ERROR, EXIT_SUCCESS


def run_cli(*arguments: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, "-m", "engine.cli", *arguments],
        capture_output=True,
        text=True,
        encoding="utf-8",
        check=False,
    )


def ndjson_events(stdout: str) -> list[dict[str, Any]]:
    return [json.loads(line) for line in stdout.splitlines()]


def write_inputs(folder: Path, inputs: dict[str, Any]) -> Path:
    path = folder / "entrées.json"
    path.write_text(json.dumps(inputs, ensure_ascii=False), encoding="utf-8")
    return path


def test_list_modules_outputs_manifests_and_schemas() -> None:
    completed = run_cli("list-modules")

    assert completed.returncode == EXIT_SUCCESS
    catalog = json.loads(completed.stdout)
    hello = next(entry for entry in catalog if entry["manifest"]["id"] == "hello")
    assert "properties" in hello["inputs_schema"]


def test_run_hello_streams_events_and_writes_output(tmp_path: Path) -> None:
    output_folder = tmp_path / "Sortie avec espaces é"
    input_file = write_inputs(tmp_path, {"name": "Zoé", "output_folder": str(output_folder)})

    completed = run_cli("run", "hello", "--input", str(input_file))

    assert completed.returncode == EXIT_SUCCESS, completed.stderr
    events = ndjson_events(completed.stdout)
    assert events[0]["type"] == "progress"
    assert events[-1]["type"] == "result"
    output = Path(events[-1]["outputs"][0])
    assert output.read_text(encoding="utf-8") == "Bonjour Zoé !"


def test_unknown_module_emits_error_event(tmp_path: Path) -> None:
    input_file = write_inputs(tmp_path, {})

    completed = run_cli("run", "nope", "--input", str(input_file))

    assert completed.returncode == EXIT_BUSINESS_ERROR
    assert ndjson_events(completed.stdout) == [
        {
            "type": "error",
            "message": "La fonctionnalité « nope » n'existe pas.",
            "file": None,
            "hint": "Fonctionnalités disponibles : dwg-parts, hello, pdf-report, soumission.",
        }
    ]


def test_invalid_inputs_name_the_field_label(tmp_path: Path) -> None:
    input_file = write_inputs(tmp_path, {"name": "", "output_folder": str(tmp_path)})

    completed = run_cli("run", "hello", "--input", str(input_file))

    assert completed.returncode == EXIT_BUSINESS_ERROR
    [event] = ndjson_events(completed.stdout)
    assert event["type"] == "error"
    assert "Nom" in event["message"]


def test_missing_input_file_names_the_file(tmp_path: Path) -> None:
    missing = tmp_path / "absent.json"

    completed = run_cli("run", "hello", "--input", str(missing))

    assert completed.returncode == EXIT_BUSINESS_ERROR
    [event] = ndjson_events(completed.stdout)
    assert event["file"] == str(missing)


def test_settings_set_then_get(tmp_path: Path) -> None:
    settings_file = tmp_path / "settings.json"
    values = write_inputs(tmp_path, {"general": {"batch_size": 6}})

    saved = run_cli("settings", "set", "--settings", str(settings_file), "--input", str(values))
    fetched = run_cli("settings", "get", "--settings", str(settings_file))

    assert saved.returncode == EXIT_SUCCESS, saved.stdout
    general = json.loads(fetched.stdout)["sections"][0]
    assert general["values"]["batch_size"] == 6


def test_settings_set_rejects_invalid_values(tmp_path: Path) -> None:
    values = write_inputs(tmp_path, {"general": {"batch_size": 0}})

    completed = run_cli(
        "settings", "set", "--settings", str(tmp_path / "s.json"), "--input", str(values)
    )

    assert completed.returncode == EXIT_BUSINESS_ERROR
    [event] = ndjson_events(completed.stdout)
    assert "Fichiers traités en parallèle" in event["message"]


def test_run_reports_invalid_stored_settings(tmp_path: Path) -> None:
    settings_file = tmp_path / "settings.json"
    settings_file.write_text(json.dumps({"general": {"batch_size": 0}}), encoding="utf-8")
    input_file = write_inputs(tmp_path, {"name": "Zoé", "output_folder": str(tmp_path)})

    completed = run_cli(
        "run", "hello", "--input", str(input_file), "--settings", str(settings_file)
    )

    assert completed.returncode == EXIT_BUSINESS_ERROR
    [event] = ndjson_events(completed.stdout)
    assert event["hint"] == "Ouvrez Paramètres pour corriger les valeurs indiquées."
