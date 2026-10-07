import subprocess
import sys

HEAVY_PACKAGES = {"openpyxl", "pypdf", "ezdxf", "pdfplumber", "numpy"}
PROBE = (
    "import engine.cli, sys; "
    f"print(sorted(m for m in sys.modules if m.split('.')[0] in {sorted(HEAVY_PACKAGES)!r}))"
)


def test_the_cli_starts_without_the_document_libraries() -> None:
    """Listing modules or reading settings must not pay for the DWG, PDF and XLSX readers."""
    completed = subprocess.run(
        [sys.executable, "-c", PROBE], capture_output=True, text=True, check=True
    )

    assert completed.stdout.strip() == "[]"
