"""Runs the frozen sidecar end to end: list-modules then `run hello`."""

import json
import subprocess
import sys
import tempfile
from pathlib import Path

EXPECTED_MODULE_ID = "hello"


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
    sys.stdout.write(f"Smoke OK: {len(events)} events\n")


if __name__ == "__main__":
    main(Path(sys.argv[1]))
