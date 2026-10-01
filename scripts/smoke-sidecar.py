"""Runs the frozen sidecar end to end: list-modules then `run hello`."""

import json
import subprocess
import sys
import tempfile
from pathlib import Path

from engine.modules.dwg_parts.tests.plans import build_facade_plan

EXPECTED_MODULE_ID = "hello"
PARALLEL_BATCH_SIZE = 2


def run_binary(binary: Path, *arguments: str) -> str:
    completed = subprocess.run(
        [str(binary), *arguments],
        capture_output=True,
        text=True,
        encoding="utf-8",
        check=False,
    )
    if completed.returncode != 0:
        raise SystemExit(
            f"{arguments[0]} failed ({completed.returncode}):\n{completed.stdout}{completed.stderr}"
        )
    return completed.stdout


def main(binary: Path) -> None:
    catalog = json.loads(run_binary(binary, "list-modules"))
    module_ids = [entry["manifest"]["id"] for entry in catalog]
    if EXPECTED_MODULE_ID not in module_ids:
        raise SystemExit(f"Module {EXPECTED_MODULE_ID!r} not discovered: {module_ids}")

    with tempfile.TemporaryDirectory() as workdir:
        settings_file = Path(workdir) / "Réglages" / "settings.json"
        sections = json.loads(
            run_binary(binary, "settings", "get", "--settings", str(settings_file))
        )
        if sections["sections"][0]["id"] != "general":
            raise SystemExit(f"Unexpected settings sections: {sections}")
        output_folder = Path(workdir) / "Sortie é"
        input_file = Path(workdir) / "entrées.json"
        input_file.write_text(
            json.dumps({"name": "Zoé", "output_folder": str(output_folder)}),
            encoding="utf-8",
        )
        stdout = run_binary(
            binary, "run", EXPECTED_MODULE_ID, "--input", str(input_file)
        )
        events = [json.loads(line) for line in stdout.splitlines()]
        if events[-1]["type"] != "result":
            raise SystemExit(f"Last event is not a result: {events[-1]}")
        events += smoke_parts_list(binary, Path(workdir))
    sys.stdout.write(f"Smoke OK: {len(events)} events\n")


def smoke_parts_list(binary: Path, workdir: Path) -> list[dict[str, object]]:
    """Exercises the process pool, ezdxf and openpyxl inside the frozen executable."""
    plans = workdir / "Plans"
    plans.mkdir()
    for name in ("Nord.dxf", "Sud.dxf"):
        build_facade_plan(plans / name)
    settings_file = workdir / "parallel-settings.json"
    settings_file.write_text(
        json.dumps({"general": {"batch_size": PARALLEL_BATCH_SIZE}}), encoding="utf-8"
    )
    input_file = workdir / "parts.json"
    input_file.write_text(
        json.dumps({"folders": [str(plans)], "output_folder": str(workdir / "Sortie")}),
        encoding="utf-8",
    )
    stdout = run_binary(
        binary,
        *(
            "run",
            "dwg-parts",
            "--input",
            str(input_file),
            "--settings",
            str(settings_file),
        ),
    )
    events = [json.loads(line) for line in stdout.splitlines()]
    if events[-1]["type"] != "result" or not Path(events[-1]["outputs"][0]).is_file():
        raise SystemExit(f"Parts list failed: {events[-1]}")
    return events


if __name__ == "__main__":
    main(Path(sys.argv[1]))
