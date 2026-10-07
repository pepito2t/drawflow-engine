"""Keeps the app version identical everywhere, and the changelog ready for a release.

Usage:
  python scripts/version.py check [--tag vX.Y.Z]
  python scripts/version.py notes
  python scripts/version.py bump X.Y.Z
"""

from __future__ import annotations

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
    VersionSource(
        ROOT / "ui" / "package.json", re.compile(r'(?m)^(  "version": ")([^"]+)(")')
    ),
    VersionSource(
        ROOT / "src-tauri" / "tauri.conf.json",
        re.compile(r'(?m)^(  "version": ")([^"]+)(")'),
    ),
    VersionSource(
        ROOT / "src-tauri" / "Cargo.toml", re.compile(r'(?m)^(version = ")([^"]+)(")')
    ),
    VersionSource(
        ROOT / "src-tauri" / "Cargo.lock",
        re.compile(r'(?m)(^name = "drawflow"\nversion = ")([^"]+)(")'),
    ),
    VersionSource(
        ROOT / "engine" / "pyproject.toml", re.compile(r'(?m)^(version = ")([^"]+)(")')
    ),
    VersionSource(
        ROOT / "streamdock" / "package.json",
        re.compile(r'(?m)^(  "version": ")([^"]+)(")'),
    ),
    VersionSource(
        ROOT / "engine" / "uv.lock",
        re.compile(r'(?m)(^name = "engine"\nversion = ")([^"]+)(")'),
    ),
]


# The Stream Dock manifest takes a plain X.Y.Z version, without pre-release suffix.
STREAMDOCK_MANIFEST = ROOT / "streamdock" / "ch.drawflow.sdPlugin" / "manifest.json"
MANIFEST_VERSION = re.compile(r'(?m)^(  "Version": ")([^"]+)(")')
PRERELEASE_SEPARATOR = "-"

CHANGELOG = ROOT / "CHANGELOG.md"
CHANGELOG_HEADING = re.compile(r"(?m)^## (.+)$")
UNRELEASED_TITLE = "Non publié"
RELEASE_TITLE_SEPARATOR = " — "


def manifest_version(version: str) -> str:
    return version.split(PRERELEASE_SEPARATOR)[0]


def read_versions() -> dict[Path, str]:
    versions: dict[Path, str] = {}
    for source in SOURCES:
        match = source.pattern.search(source.path.read_text(encoding="utf-8"))
        if match is None:
            raise SystemExit(
                f"Version introuvable dans {source.path.relative_to(ROOT)}"
            )
        versions[source.path] = match.group(2)
    return versions


def current_version() -> str:
    versions = read_versions()
    distinct = set(versions.values())
    if len(distinct) != 1:
        details = "\n".join(
            f"  {path.relative_to(ROOT)}: {value}" for path, value in versions.items()
        )
        raise SystemExit(f"Versions incohérentes :\n{details}")
    version = distinct.pop()
    manifest = MANIFEST_VERSION.search(STREAMDOCK_MANIFEST.read_text(encoding="utf-8"))
    if manifest is None or manifest.group(2) != manifest_version(version):
        raise SystemExit(
            f"Version du plugin Stream Dock incohérente (attendu {manifest_version(version)})"
        )
    return version


def changelog_sections() -> dict[str, str]:
    """Section bodies keyed by title: the version number, or 'Non publié'."""
    content = CHANGELOG.read_text(encoding="utf-8")
    headings = list(CHANGELOG_HEADING.finditer(content))
    sections: dict[str, str] = {}
    for index, heading in enumerate(headings):
        end = headings[index + 1].start() if index + 1 < len(headings) else len(content)
        title = heading.group(1).split(RELEASE_TITLE_SEPARATOR)[0]
        sections[title] = content[heading.end() : end].strip()
    return sections


def release_notes(version: str) -> str:
    notes = changelog_sections().get(version, "")
    if not notes:
        raise SystemExit(f"Section « ## {version} » absente ou vide dans CHANGELOG.md")
    return notes


def check_changelog_ready(version: str) -> None:
    release_notes(version)
    if changelog_sections().get(UNRELEASED_TITLE):
        raise SystemExit(
            f"La section « ## {UNRELEASED_TITLE} » de CHANGELOG.md doit être vide avant le tag"
        )


def check(tag: str | None) -> None:
    version = current_version()
    if tag is not None:
        if tag != f"{TAG_PREFIX}{version}":
            raise SystemExit(f"Le tag {tag} ne correspond pas à la version {version}")
        check_changelog_ready(version)
    sys.stdout.write(f"Version {version} cohérente\n")


def notes() -> None:
    sys.stdout.write(release_notes(current_version()) + "\n")


def bump(version: str) -> None:
    if not SEMVER.match(version):
        raise SystemExit(f"Version invalide : {version} (attendu X.Y.Z ou X.Y.Z-rc.N)")
    for source in SOURCES:
        content = source.path.read_text(encoding="utf-8")
        updated = source.pattern.sub(
            lambda match: f"{match.group(1)}{version}{match.group(3)}", content, count=1
        )
        source.path.write_text(updated, encoding="utf-8")
    content = STREAMDOCK_MANIFEST.read_text(encoding="utf-8")
    replacement = manifest_version(version)
    content = MANIFEST_VERSION.sub(
        lambda match: f"{match.group(1)}{replacement}{match.group(3)}", content, count=1
    )
    STREAMDOCK_MANIFEST.write_text(content, encoding="utf-8")
    for path in (ROOT / "src-tauri" / "tauri.conf.json", STREAMDOCK_MANIFEST):
        json.loads(path.read_text(encoding="utf-8"))
    sys.stdout.write(
        f"Version {version} appliquée ; commit puis tag {TAG_PREFIX}{version}\n"
    )


def main() -> None:
    parser = argparse.ArgumentParser()
    commands = parser.add_subparsers(dest="command", required=True)
    check_parser = commands.add_parser("check")
    check_parser.add_argument("--tag")
    commands.add_parser("notes")
    bump_parser = commands.add_parser("bump")
    bump_parser.add_argument("version")
    arguments = parser.parse_args()
    if arguments.command == "check":
        check(arguments.tag)
    elif arguments.command == "notes":
        notes()
    else:
        bump(arguments.version)


if __name__ == "__main__":
    main()
