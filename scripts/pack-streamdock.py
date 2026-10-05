"""Packs the built Stream Dock plugin as the zip Drawflow downloads and unpacks into Stream Dock."""

import sys
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
PLUGIN_FOLDER = ROOT / "streamdock" / "ch.drawflow.sdPlugin"
OUTPUT = ROOT / "streamdock" / "dist" / "ch.drawflow.sdPlugin.zip"
REQUIRED = ("manifest.json", "bin/plugin.js")
EXCLUDED_PARTS = {"logs"}
EXCLUDED_SUFFIXES = {".svg", ".map"}


def main() -> None:
    missing = [name for name in REQUIRED if not (PLUGIN_FOLDER / name).is_file()]
    if missing:
        raise SystemExit(f"Plugin incomplet, lancez d'abord pnpm build : {', '.join(missing)}")
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(OUTPUT, "w", zipfile.ZIP_DEFLATED) as archive:
        for path in sorted(PLUGIN_FOLDER.rglob("*")):
            relative = path.relative_to(PLUGIN_FOLDER)
            if path.is_file() and _shipped(relative):
                archive.write(path, f"{PLUGIN_FOLDER.name}/{relative.as_posix()}")
    sys.stdout.write(f"{OUTPUT}\n")


def _shipped(relative: Path) -> bool:
    return not EXCLUDED_PARTS.intersection(relative.parts) and relative.suffix not in EXCLUDED_SUFFIXES


if __name__ == "__main__":
    main()
