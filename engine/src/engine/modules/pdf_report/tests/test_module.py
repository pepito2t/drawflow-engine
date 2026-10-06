import json
import subprocess
import sys
from pathlib import Path
from typing import Any

import pytest
from docx import Document

from engine.modules.pdf_report.tests.plans import build_report_plan
from engine.testing.pdf import PdfSpec, write_pdf

GOLDEN_RELATIVE_PATH = Path("fixtures") / "pdf-report" / "expected" / "rapport.json"


def repository_root() -> Path:
    for parent in Path(__file__).resolve().parents:
        if (parent / "fixtures").is_dir() and (parent / "engine").is_dir():
            return parent
    raise RuntimeError("repository root not found")


def run_report(tmp_path: Path, inputs: dict[str, Any], batch_size: int = 2) -> list[dict[str, Any]]:
    settings = tmp_path / "settings.json"
    settings.write_text(json.dumps({"general": {"batch_size": batch_size}}), encoding="utf-8")
    input_file = tmp_path / "inputs.json"
    input_file.write_text(json.dumps(inputs, ensure_ascii=False), encoding="utf-8")
    completed = subprocess.run(
        [
            sys.executable,
            "-m",
            "engine.cli",
            "run",
            "pdf-report",
            "--input",
            str(input_file),
            "--settings",
            str(settings),
        ],
        capture_output=True,
        text=True,
        encoding="utf-8",
        check=False,
    )
    return [json.loads(line) for line in completed.stdout.splitlines()]


@pytest.fixture
def plans(tmp_path: Path) -> Path:
    folder = tmp_path / "Plans PDF"
    folder.mkdir()
    build_report_plan(folder / "F-101 Nord.pdf", "F-101", "B", ["EQ-40", "P-1200"])
    build_report_plan(folder / "F-102 Sud.pdf", "F-102", "C", ["P-1200"])
    return folder


@pytest.mark.parametrize("batch_size", [1, 2])
def test_report_matches_golden_file(tmp_path: Path, plans: Path, batch_size: int) -> None:
    events = run_report(
        tmp_path,
        {"folders": [str(plans)], "project": "Tour B", "output_folder": str(tmp_path / "Sortie")},
        batch_size,
    )

    result = events[-1]
    assert result["type"] == "result", events
    output = Path(result["outputs"][0])
    assert output.name.startswith("Tour B_rapport_")
    paragraphs = [
        paragraph.text for paragraph in Document(str(output)).paragraphs if paragraph.text
    ]
    golden = json.loads((repository_root() / GOLDEN_RELATIVE_PATH).read_text(encoding="utf-8"))
    assert paragraphs[2:] == golden["paragraphs_after_header"]


def test_scanned_pdf_is_flagged(tmp_path: Path) -> None:
    scan = write_pdf(tmp_path / "scan.pdf", PdfSpec(pages=[[]]))

    events = run_report(tmp_path, {"files": [str(scan)], "output_folder": str(tmp_path / "Sortie")})

    warnings = [event for event in events if event["type"] == "warning"]
    assert warnings[0]["file"] == str(scan)
    assert "scannée" in warnings[0]["message"]
    assert "scan" in warnings[0]["hint"]
    assert events[-1]["type"] == "result"
