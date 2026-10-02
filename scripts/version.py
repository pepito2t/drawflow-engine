"""Keeps the app version identical everywhere.

Usage:
  python scripts/version.py check [--tag vX.Y.Z]
  python scripts/version.py bump X.Y.Z
"""

import argparse
import json
import re
import sys
from dataclasses import dataclass
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SEMVER = re.compile(r"^\d+\.\d+\.\d+(-[0-9A-Za-z.]+)?$")
TAG_PREFIX = "v"


@dataclass(frozen=True)
class VersionSource:
    path: Path
    pattern: re.Pattern[str]


SOURCES = [
    VersionSource(ROOT / "ui" / "package.json", re.compile(r'(?m)^(  "version": ")([^"]+)(")')),
    VersionSource(
        ROOT / "src-tauri" / "tauri.conf.json",
        re.compile(r'(?m)^(  "version": ")([^"]+)(")'),
    ),
    VersionSource(ROOT / "src-tauri" / "Cargo.toml", re.compile(r'(?m)^(version = ")([^"]+)(")')),
    VersionSource(
        ROOT / "src-tauri" / "Cargo.lock",
        re.compile(r'(?m)(^name = "drawflow"\nversion = ")([^"]+)(")'),
    ),
    VersionSource(ROOT / "engine" / "pyproject.toml", re.compile(r'(?m)^(version = ")([^"]+)(")')),
    VersionSource(
        ROOT / "engine" / "uv.lock",
        re.compile(r'(?m)(^name = "engine"\nversion = ")([^"]+)(")'),
    ),
]


def read_versions() -> dict[Path, str]:
    versions: dict[Path, str] = {}
    for source in SOURCES:
        match = source.pattern.search(source.path.read_text(encoding="utf-8"))
        if match is None:
            raise SystemExit(f"Version introuvable dans {source.path.relative_to(ROOT)}")
        versions[source.path] = match.group(2)
    return versions


def check(tag: str | None) -> None:
    versions = read_versions()
    distinct = set(versions.values())
    if len(distinct) != 1:
        details = "\n".join(
            f"  {path.relative_to(ROOT)}: {value}" for path, value in versions.items()
        )
        raise SystemExit(f"Versions incohérentes :\n{details}")
    version = distinct.pop()
    if tag is not None and tag != f"{TAG_PREFIX}{version}":
        raise SystemExit(f"Le tag {tag} ne correspond pas à la version {version}")
    sys.stdout.write(f"Version {version} cohérente\n")


def bump(version: str) -> None:
    if not SEMVER.match(version):
        raise SystemExit(f"Version invalide : {version} (attendu X.Y.Z ou X.Y.Z-rc.N)")
    for source in SOURCES:
        content = source.path.read_text(encoding="utf-8")
        updated = source.pattern.sub(
            lambda match: f"{match.group(1)}{version}{match.group(3)}", content, count=1
        )
        source.path.write_text(updated, encoding="utf-8")
    json.loads((ROOT / "src-tauri" / "tauri.conf.json").read_text(encoding="utf-8"))
    sys.stdout.write(f"Version {version} appliquée ; commit puis tag {TAG_PREFIX}{version}\n")


def main() -> None:
    parser = argparse.ArgumentParser()
    commands = parser.add_subparsers(dest="command", required=True)
    check_parser = commands.add_parser("check")
    check_parser.add_argument("--tag")
    bump_parser = commands.add_parser("bump")
    bump_parser.add_argument("version")
    arguments = parser.parse_args()
    if arguments.command == "check":
        check(arguments.tag)
    else:
        bump(arguments.version)


if __name__ == "__main__":
    main()
