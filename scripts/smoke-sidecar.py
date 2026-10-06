"""Runs the frozen sidecar end to end: catalog, settings, then every module."""

import json
import socket
import subprocess
import sys
import tempfile
from datetime import timedelta
from pathlib import Path

import anyio
from engine.modules.dwg_parts.tests.plans import build_facade_plan
from engine.modules.pdf_report.tests.plans import build_report_plan
from engine.modules.soumission.tests.workbooks import submission_bytes
from engine.testing.pdf import PdfSpec, TextItem, write_pdf
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

EXPECTED_MODULE_IDS = ["dwg-parts", "pdf-report", "soumission"]
EXPECTED_MCP_TOOLS = [
    "inspect_submission_headers",
    "list_features",
    "list_help_topics",
    "list_presets",
    "list_templates",
    "propose_column_synonyms",
    "propose_feature",
    "propose_preset",
    "read_help",
]
PARALLEL_BATCH_SIZE = 2
MCP_REQUEST_TIMEOUT = timedelta(seconds=120)


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
    if module_ids != EXPECTED_MODULE_IDS:
        raise SystemExit(f"Unexpected modules: {module_ids}")

    with tempfile.TemporaryDirectory() as workdir:
        settings_file = Path(workdir) / "Réglages" / "settings.json"
        sections = json.loads(
            run_binary(binary, "settings", "get", "--settings", str(settings_file))
        )
        if sections["sections"][0]["id"] != "general":
            raise SystemExit(f"Unexpected settings sections: {sections}")
        events = smoke_parts_list(binary, Path(workdir))
        events += smoke_report(binary, Path(workdir))
        events += smoke_soumission(binary, Path(workdir))
        anyio.run(smoke_mcp, binary, settings_file)
        smoke_assistant(binary, Path(workdir))
    sys.stdout.write(f"Smoke OK: {len(events)} events\n")


async def smoke_mcp(binary: Path, settings_file: Path) -> None:
    """Handshakes with the frozen MCP server, as the assistant does."""
    parameters = StdioServerParameters(
        command=str(binary), args=["mcp", "--settings", str(settings_file)]
    )
    async with (
        stdio_client(parameters) as (read, write),
        ClientSession(read, write, read_timeout_seconds=MCP_REQUEST_TIMEOUT) as session,
    ):
        await session.initialize()
        tools = sorted(tool.name for tool in (await session.list_tools()).tools)
        features = await session.call_tool("list_features", {})
        guide = await session.call_tool("read_help", {"topic": "premiers-pas"})
    if tools != EXPECTED_MCP_TOOLS or features.isError or guide.isError:
        raise SystemExit(f"Unexpected MCP server answer: {tools} {features} {guide}")


def smoke_assistant(binary: Path, workdir: Path) -> None:
    """The model client is bundled: an absent model yields a readable error event."""
    with socket.socket() as probe:
        probe.bind(("127.0.0.1", 0))
        closed_port = probe.getsockname()[1]
    settings_file = workdir / "assistant-settings.json"
    url = f"http://127.0.0.1:{closed_port}/v1"
    settings_file.write_text(json.dumps({"assistant": {"model_server_url": url}}))
    completed = subprocess.run(
        [str(binary), "assistant", "models", "--settings", str(settings_file)],
        capture_output=True,
        text=True,
        encoding="utf-8",
        check=False,
    )
    if completed.returncode != 1 or "ne répond pas" not in completed.stdout:
        raise SystemExit(
            f"Unexpected assistant answer:\n{completed.stdout}{completed.stderr}"
        )


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
        json.dumps(
            {"folders": [str(plans)], "output_folder": str(workdir / "Sortie"), "preview": False}
        ),
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


def run_module(
    binary: Path, workdir: Path, module_id: str, inputs: dict[str, object]
) -> list[dict[str, object]]:
    input_file = workdir / f"{module_id}.json"
    input_file.write_text(json.dumps(inputs), encoding="utf-8")
    stdout = run_binary(binary, "run", module_id, "--input", str(input_file))
    events = [json.loads(line) for line in stdout.splitlines()]
    last = events[-1]
    if last["type"] != "result" or not Path(str(last["outputs"][0])).is_file():  # type: ignore[index]
        raise SystemExit(f"{module_id} failed: {last}")
    return events


def smoke_report(binary: Path, workdir: Path) -> list[dict[str, object]]:
    """Exercises pdfplumber/pdfminer and docxtpl/python-docx data files."""
    plan = build_report_plan(workdir / "F-101.pdf", "F-101", "B", ["EQ-40"])
    return run_module(
        binary,
        workdir,
        "pdf-report",
        {"files": [str(plan)], "output_folder": str(workdir / "Sortie")},
    )


def smoke_soumission(binary: Path, workdir: Path) -> list[dict[str, object]]:
    """Exercises pypdf attachments and read-only openpyxl."""
    spec = PdfSpec(
        pages=[[TextItem(50, 50, "Offre")]],
        attachments={"lot.xlsx": submission_bytes()},
    )
    pdf = write_pdf(workdir / "Offre.pdf", spec)
    return run_module(
        binary,
        workdir,
        "soumission",
        {"files": [str(pdf)], "output_folder": str(workdir / "Sortie"), "preview": False},
    )


if __name__ == "__main__":
    main(Path(sys.argv[1]))
