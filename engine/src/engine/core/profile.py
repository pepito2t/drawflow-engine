"""A workstation profile in one zip: settings sections, presets and output templates."""

import json
import shutil
import zipfile
import zlib
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from pydantic import ValidationError

from engine.core.errors import InvalidSettingsError, SettingsFileError
from engine.core.json_files import write_json_atomically
from engine.core.messages import t
from engine.core.presets import Preset, PresetStore
from engine.core.registry import AnyModule
from engine.core.settings import (
    Document,
    load_section,
    read_document,
    save_settings,
    section_specs,
)
from engine.core.templates import DEFAULTS_FILE, SUFFIX_KINDS, TemplateLibrary
from engine.core.validation import describe_validation_error

PROFILE_FORMAT = "drawflow-profile"
PROFILE_VERSION = 1
PROFILE_FILE = "profile.json"
PRESETS_MEMBER = "presets.json"
TEMPLATES_PREFIX = "templates/"
MAX_MEMBER_BYTES = 50_000_000
UNKNOWN_VERSION = "0.0.0"
CORRUPT_ARCHIVE_ERRORS = (zipfile.BadZipFile, zlib.error)


def export_profile(
    settings_file: Path, target: Path, modules: dict[str, AnyModule], app_version: str | None
) -> dict[str, Any]:
    document = read_document(settings_file)
    sections = {
        spec.id: load_section(spec.model, spec.id, spec.title, document).model_dump(mode="json")
        for spec in section_specs(modules)
    }
    manifest = {
        "format": PROFILE_FORMAT,
        "version": PROFILE_VERSION,
        "app_version": app_version or UNKNOWN_VERSION,
        "exported_at": datetime.now(UTC).isoformat(timespec="seconds"),
        "sections": sections,
    }
    presets = [preset.model_dump(mode="json") for preset in PresetStore(settings_file).presets()]
    library = TemplateLibrary(settings_file)
    try:
        target.parent.mkdir(parents=True, exist_ok=True)
        with zipfile.ZipFile(target, "w", zipfile.ZIP_DEFLATED) as archive:
            archive.writestr(PROFILE_FILE, json.dumps(manifest, ensure_ascii=False, indent=2))
            archive.writestr(PRESETS_MEMBER, json.dumps(presets, ensure_ascii=False, indent=2))
            for template in library.templates():
                archive.write(library.folder / template.id, TEMPLATES_PREFIX + template.id)
            if library.defaults():
                archive.writestr(TEMPLATES_PREFIX + DEFAULTS_FILE, json.dumps(library.defaults()))
    except OSError as error:
        raise SettingsFileError(t("profile.export_failed"), file=target) from error
    return {
        "exported": str(target),
        "sections": len(sections),
        "presets": len(presets),
        "templates": len(library.templates()),
    }


def read_profile(
    source: Path, settings_file: Path, modules: dict[str, AnyModule], app_version: str | None
) -> dict[str, Any]:
    """What an import would replace, without touching anything."""
    contents = _read_archive(source, modules, app_version)
    library = TemplateLibrary(settings_file)
    existing_templates = {template.id for template in library.templates()}
    return {
        "app_version": contents.app_version,
        "exported_at": contents.exported_at,
        "sections": [{"id": spec.id, "title": spec.title} for spec in contents.sections],
        "presets": [preset.name for preset in contents.presets],
        "templates": [template.name for template in contents.templates],
        "replaced_presets": len(PresetStore(settings_file).presets()),
        "replaced_templates": sorted(
            existing_templates & {template.name for template in contents.templates}
        ),
    }


def import_profile(
    source: Path, settings_file: Path, modules: dict[str, AnyModule], app_version: str | None
) -> dict[str, Any]:
    contents = _read_archive(source, modules, app_version)
    # An unreadable settings file must be found before any template or preset is replaced.
    read_document(settings_file)
    library = TemplateLibrary(settings_file)
    try:
        library.folder.mkdir(parents=True, exist_ok=True)
        with zipfile.ZipFile(source) as archive:
            for template in contents.templates:
                with (
                    archive.open(template.member) as member,
                    (library.folder / template.name).open("wb") as copy,
                ):
                    shutil.copyfileobj(member, copy)
        if contents.defaults is not None:
            write_json_atomically(library.folder / DEFAULTS_FILE, contents.defaults)
        write_json_atomically(
            PresetStore(settings_file).path,
            [preset.model_dump(mode="json") for preset in contents.presets],
        )
    except CORRUPT_ARCHIVE_ERRORS as error:
        raise _corrupt(source) from error
    except OSError as error:
        raise SettingsFileError(t("profile.apply_failed"), file=source) from error
    save_settings(settings_file, contents.document, modules)
    return {
        "imported": str(source),
        "sections": len(contents.sections),
        "presets": len(contents.presets),
        "templates": len(contents.templates),
    }


class _Template:
    def __init__(self, member: str) -> None:
        self.member = member
        self.name = member.removeprefix(TEMPLATES_PREFIX)


class _Contents:
    def __init__(
        self,
        app_version: str,
        exported_at: str | None,
        sections: list[Any],
        document: Document,
        presets: list[Preset],
        templates: list[_Template],
        defaults: dict[str, str] | None,
    ) -> None:
        self.app_version = app_version
        self.exported_at = exported_at
        self.sections = sections
        self.document = document
        self.presets = presets
        self.templates = templates
        self.defaults = defaults


def _read_archive(
    source: Path, modules: dict[str, AnyModule], app_version: str | None
) -> _Contents:
    if not zipfile.is_zipfile(source):
        raise InvalidSettingsError(t("profile.not_a_profile"), file=source)
    try:
        with zipfile.ZipFile(source) as archive:
            return _read_members(archive, source, modules, app_version)
    except CORRUPT_ARCHIVE_ERRORS as error:
        raise _corrupt(source) from error


def _read_members(
    archive: zipfile.ZipFile, source: Path, modules: dict[str, AnyModule], app_version: str | None
) -> _Contents:
    if PROFILE_FILE not in archive.namelist():
        raise InvalidSettingsError(t("profile.not_a_profile"), file=source)
    manifest = _member_json(archive, PROFILE_FILE, source)
    if not isinstance(manifest, dict) or manifest.get("format") != PROFILE_FORMAT:
        raise InvalidSettingsError(t("profile.not_a_profile"), file=source)
    exported_by = str(manifest.get("app_version", UNKNOWN_VERSION))
    if _version_key(exported_by) > _version_key(app_version or UNKNOWN_VERSION):
        raise InvalidSettingsError(
            t("profile.newer_version", version=exported_by),
            file=source,
            hint=t("profile.newer_version_hint"),
        )
    sections, document = _validated_sections(manifest.get("sections"), modules, source)
    presets = _validated_presets(_member_json(archive, PRESETS_MEMBER, source), source)
    exported_at = manifest.get("exported_at")
    return _Contents(
        exported_by,
        exported_at if isinstance(exported_at, str) else None,
        sections,
        document,
        presets,
        _templates(archive, source),
        _defaults(archive, source),
    )


def _templates(archive: zipfile.ZipFile, source: Path) -> list[_Template]:
    templates = [
        _Template(name)
        for name in archive.namelist()
        if name.startswith(TEMPLATES_PREFIX)
        and Path(name).suffix.lower() in SUFFIX_KINDS
        and Path(name).name == name.removeprefix(TEMPLATES_PREFIX)
    ]
    for template in templates:
        if archive.getinfo(template.member).file_size > MAX_MEMBER_BYTES:
            raise InvalidSettingsError(
                t("profile.template_too_large", name=template.name), file=source
            )
        # A .docx or .xlsx is a zip: anything else would land in the library unreadable.
        with archive.open(template.member) as member:
            if not zipfile.is_zipfile(member):
                raise InvalidSettingsError(
                    t("profile.template_unreadable", name=template.name),
                    file=source,
                    hint=t("profile.template_unreadable_hint"),
                )
    return templates


def _defaults(archive: zipfile.ZipFile, source: Path) -> dict[str, str] | None:
    if TEMPLATES_PREFIX + DEFAULTS_FILE not in archive.namelist():
        return None
    raw_defaults = _member_json(archive, TEMPLATES_PREFIX + DEFAULTS_FILE, source)
    if not isinstance(raw_defaults, dict):
        return None
    return {str(key): str(value) for key, value in raw_defaults.items()}


def _member_json(archive: zipfile.ZipFile, member: str, source: Path) -> Any:
    try:
        return json.loads(archive.read(member).decode("utf-8"))
    except (KeyError, ValueError) as error:
        raise InvalidSettingsError(
            t("profile.member_unreadable", member=member), file=source
        ) from error


def _corrupt(source: Path) -> InvalidSettingsError:
    return InvalidSettingsError(t("profile.corrupt"), file=source, hint=t("profile.corrupt_hint"))


def _validated_sections(
    raw: Any, modules: dict[str, AnyModule], source: Path
) -> tuple[list[Any], Document]:
    if not isinstance(raw, dict):
        raise InvalidSettingsError(t("profile.no_settings"), file=source)
    known = {spec.id: spec for spec in section_specs(modules)}
    sections = []
    document: Document = {}
    for section_id, values in raw.items():
        spec = known.get(str(section_id))
        if spec is None:
            # A profile from a build with other modules: only what this version knows is applied.
            continue
        try:
            document[spec.id] = spec.model.model_validate(values).model_dump(mode="json")
        except ValidationError as error:
            raise InvalidSettingsError(
                t("profile.section_invalid", title=spec.title),
                file=source,
                hint=describe_validation_error(spec.model, error),
            ) from error
        sections.append(spec)
    return sections, document


def _validated_presets(raw: Any, source: Path) -> list[Preset]:
    if not isinstance(raw, list):
        raise InvalidSettingsError(t("profile.presets_unreadable"), file=source)
    try:
        return [Preset.model_validate(item) for item in raw]
    except ValidationError as error:
        raise InvalidSettingsError(t("profile.presets_invalid"), file=source) from error


def _version_key(version: str) -> tuple[int, ...]:
    numbers = []
    for part in version.split("-")[0].split("."):
        digits = "".join(character for character in part if character.isdigit())
        numbers.append(int(digits) if digits else 0)
    return tuple(numbers)
