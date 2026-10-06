import json
import subprocess
import sys
from pathlib import Path
from typing import Any

from engine.cli import EXIT_BUSINESS_ERROR, EXIT_SUCCESS
from engine.modules.soumission.tests.workbooks import write_submission


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
    assert [entry["manifest"]["id"] for entry in catalog] == [
        "dwg-parts",
        "dwg-diff",
        "pdf-report",
        "soumission",
    ]
    assert all("properties" in entry["inputs_schema"] for entry in catalog)


def test_run_streams_events_and_writes_output(tmp_path: Path) -> None:
    source = write_submission(tmp_path / "offre é.xlsx")
    output_folder = tmp_path / "Sortie avec espaces é"
    input_file = write_inputs(
        tmp_path, {"files": [str(source)], "output_folder": str(output_folder), "preview": False}
    )

    completed = run_cli("run", "soumission", "--input", str(input_file))

    assert completed.returncode == EXIT_SUCCESS, completed.stderr
    events = ndjson_events(completed.stdout)
    assert events[0]["type"] == "log"
    assert any(event["type"] == "progress" for event in events)
    assert events[-1]["type"] == "result"
    assert Path(events[-1]["outputs"][0]).parent == output_folder


def test_unknown_module_emits_error_event(tmp_path: Path) -> None:
    input_file = write_inputs(tmp_path, {})

    completed = run_cli("run", "nope", "--input", str(input_file))

    assert completed.returncode == EXIT_BUSINESS_ERROR
    assert ndjson_events(completed.stdout) == [
        {
            "type": "error",
            "message": "La fonctionnalité « nope » n'existe pas.",
            "file": None,
            "hint": "Fonctionnalités disponibles : dwg-diff, dwg-parts, pdf-report, soumission.",
        }
    ]


def test_invalid_inputs_name_the_field_label(tmp_path: Path) -> None:
    inputs = {"files": ["a.xlsx"], "recursive": "peut-être", "output_folder": str(tmp_path)}
    input_file = write_inputs(tmp_path, inputs)

    completed = run_cli("run", "soumission", "--input", str(input_file))

    assert completed.returncode == EXIT_BUSINESS_ERROR
    [event] = ndjson_events(completed.stdout)
    assert event["type"] == "error"
    assert "Inclure les sous-dossiers" in event["message"]


def test_missing_input_file_names_the_file(tmp_path: Path) -> None:
    missing = tmp_path / "absent.json"

    completed = run_cli("run", "soumission", "--input", str(missing))

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
    source = write_submission(tmp_path / "offre.xlsx")
    input_file = write_inputs(tmp_path, {"files": [str(source)], "output_folder": str(tmp_path)})

    completed = run_cli(
        "run", "soumission", "--input", str(input_file), "--settings", str(settings_file)
    )

    assert completed.returncode == EXIT_BUSINESS_ERROR
    [event] = ndjson_events(completed.stdout)
    assert event["hint"] == "Ouvrez Paramètres pour corriger les valeurs indiquées."


def test_failures_are_written_to_the_diagnostic_log(tmp_path: Path) -> None:
    settings = tmp_path / "settings.json"
    settings.write_text("{pas du json", encoding="utf-8")

    completed = run_cli("settings", "get", "--settings", str(settings))

    assert completed.returncode == EXIT_BUSINESS_ERROR

    log = tmp_path / "logs" / "engine.log"
    entry = json.loads(log.read_text(encoding="utf-8").splitlines()[-1])
    assert entry["type"] == "SettingsFileError"
    assert "JSONDecodeError" in entry["cause"]


def test_runs_are_added_to_the_history(tmp_path: Path) -> None:
    settings = tmp_path / "settings.json"
    inputs = write_inputs(
        tmp_path,
        {
            "files": [str(tmp_path / "absent.dwg")],
            "project": "P",
            "output_folder": str(tmp_path / "out"),
        },
    )

    run_cli("run", "dwg-parts", "--input", str(inputs), "--settings", str(settings))
    listed = run_cli("history", "list", "--settings", str(settings))

    [entry] = json.loads(listed.stdout)["entries"]
    assert entry["module"] == "dwg-parts"
    assert entry["status"] == "failed"
    assert entry["inputs"]["project"] == "P"
