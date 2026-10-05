import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from pydantic import ValidationError

from engine.core.errors import InvalidSettingsError, ModuleContractError, SettingsFileError
from engine.core.json_files import write_json_atomically
from engine.core.registry import AnyModule
from engine.core.settings_models import (
    AssistantSettings,
    GeneralSettings,
    ModuleSettings,
    SettingsSection,
)
from engine.core.validation import describe_validation_error

GENERAL_SECTION_ID = "general"
GENERAL_SECTION_TITLE = "Général"
ASSISTANT_SECTION_ID = "assistant"
ASSISTANT_SECTION_TITLE = "Assistant"
APP_SECTION_IDS = {GENERAL_SECTION_ID, ASSISTANT_SECTION_ID}
MODULES_KEY = "modules"
FIX_SETTINGS_HINT = "Ouvrez Paramètres pour corriger les valeurs indiquées."
RESET_SETTINGS_HINT = (
    "Restaurez une sauvegarde ou supprimez ce fichier pour revenir aux valeurs par défaut."
)

Document = dict[str, Any]


@dataclass(frozen=True)
class SectionSpec:
    id: str
    title: str
    model: type[SettingsSection]


@dataclass(frozen=True)
class RunSettings:
    general: GeneralSettings
    module: ModuleSettings | None


def section_specs(modules: dict[str, AnyModule]) -> list[SectionSpec]:
    specs = [SectionSpec(GENERAL_SECTION_ID, GENERAL_SECTION_TITLE, GeneralSettings)]
    for module_id, module in modules.items():
        if module_id in APP_SECTION_IDS:
            raise ModuleContractError(f"L'identifiant « {module_id} » est réservé.")
        if module.settings_model is not None:
            specs.append(SectionSpec(module_id, module.manifest.name, module.settings_model))
    specs.append(SectionSpec(ASSISTANT_SECTION_ID, ASSISTANT_SECTION_TITLE, AssistantSettings))
    return specs


def read_document(path: Path | None) -> Document:
    if path is None or not path.exists():
        return {}
    try:
        document = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeDecodeError, json.JSONDecodeError) as error:
        raise SettingsFileError(
            "Le fichier de paramètres est illisible ; il n'a pas été modifié.",
            file=path,
            hint=RESET_SETTINGS_HINT,
        ) from error
    if not isinstance(document, dict):
        raise SettingsFileError("Le fichier de paramètres n'a pas le bon format.", file=path)
    return document


def load_section[SectionT: SettingsSection](
    model: type[SectionT], section_id: str, title: str, document: Document
) -> SectionT:
    try:
        return model.model_validate(_raw_section(document, section_id))
    except ValidationError as error:
        raise InvalidSettingsError(
            f"Paramètres « {title} » invalides : {describe_validation_error(model, error)}",
            hint=FIX_SETTINGS_HINT,
        ) from error


def load_run_settings(path: Path | None, module: AnyModule) -> RunSettings:
    document = read_document(path)
    general = load_section(GeneralSettings, GENERAL_SECTION_ID, GENERAL_SECTION_TITLE, document)
    if module.settings_model is None:
        return RunSettings(general=general, module=None)
    manifest = module.manifest
    module_settings = load_section(module.settings_model, manifest.id, manifest.name, document)
    return RunSettings(general=general, module=module_settings)


def load_general_settings(path: Path | None) -> GeneralSettings:
    return load_section(
        GeneralSettings, GENERAL_SECTION_ID, GENERAL_SECTION_TITLE, read_document(path)
    )


def load_assistant_settings(path: Path | None) -> AssistantSettings:
    document = read_document(path)
    return load_section(AssistantSettings, ASSISTANT_SECTION_ID, ASSISTANT_SECTION_TITLE, document)


def describe_settings(path: Path | None, modules: dict[str, AnyModule]) -> list[dict[str, Any]]:
    document = read_document(path)
    return [_describe_section(spec, document) for spec in section_specs(modules)]


def save_settings(path: Path, submitted: Document, modules: dict[str, AnyModule]) -> None:
    document = read_document(path)
    errors: list[str] = []
    for spec in section_specs(modules):
        if spec.id not in submitted:
            continue
        try:
            section = spec.model.model_validate(submitted[spec.id])
        except ValidationError as error:
            errors.append(f"{spec.title} : {describe_validation_error(spec.model, error)}")
            continue
        _store_section(document, spec.id, section.model_dump(mode="json"))
    if errors:
        raise InvalidSettingsError(
            "Paramètres invalides — " + " ; ".join(errors), hint=FIX_SETTINGS_HINT
        )
    _write_atomically(path, document)


def _describe_section(spec: SectionSpec, document: Document) -> dict[str, Any]:
    try:
        values = load_section(spec.model, spec.id, spec.title, document)
        error = None
    except InvalidSettingsError as invalid:
        values = spec.model()
        error = invalid.message
    return {
        "id": spec.id,
        "title": spec.title,
        "schema": spec.model.model_json_schema(),
        "values": values.model_dump(mode="json"),
        "error": error,
    }


def _raw_section(document: Document, section_id: str) -> Any:
    if section_id in APP_SECTION_IDS:
        return document.get(section_id, {})
    modules = document.get(MODULES_KEY, {})
    return modules.get(section_id, {}) if isinstance(modules, dict) else {}


def _store_section(document: Document, section_id: str, values: Document) -> None:
    if section_id in APP_SECTION_IDS:
        document[section_id] = values
        return
    modules = document.get(MODULES_KEY)
    if not isinstance(modules, dict):
        modules = {}
        document[MODULES_KEY] = modules
    modules[section_id] = values


def _write_atomically(path: Path, document: Document) -> None:
    try:
        write_json_atomically(path, document)
    except OSError as error:
        raise SettingsFileError(
            "Impossible d'enregistrer les paramètres.",
            file=path,
            hint="Vérifiez que le dossier de configuration est accessible en écriture.",
        ) from error


EXPORT_FORMAT = "drawflow-settings"
EXPORT_VERSION = 1


def export_section(
    path: Path | None, section_id: str, modules: dict[str, AnyModule], target: Path
) -> None:
    spec = _spec(section_id, modules)
    values = load_section(spec.model, spec.id, spec.title, read_document(path))
    payload = {
        "format": EXPORT_FORMAT,
        "version": EXPORT_VERSION,
        "section": spec.id,
        "title": spec.title,
        "values": values.model_dump(mode="json"),
    }
    try:
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    except OSError as error:
        raise SettingsFileError("Impossible d'exporter les paramètres.", file=target) from error


def read_section_import(source: Path, modules: dict[str, AnyModule]) -> dict[str, Any]:
    """Validates an exported file without saving it, so the user can review it first."""
    payload = read_document(source)
    if payload.get("format") != EXPORT_FORMAT:
        raise InvalidSettingsError(
            "Ce fichier n'est pas un export de paramètres Drawflow.", file=source
        )
    spec = _spec(str(payload.get("section", "")), modules)
    try:
        values = spec.model.model_validate(payload.get("values", {}))
    except ValidationError as error:
        raise InvalidSettingsError(
            f"Paramètres « {spec.title} » invalides : "
            f"{describe_validation_error(spec.model, error)}",
            file=source,
        ) from error
    return {"section": spec.id, "title": spec.title, "values": values.model_dump(mode="json")}


def _spec(section_id: str, modules: dict[str, AnyModule]) -> SectionSpec:
    for spec in section_specs(modules):
        if spec.id == section_id:
            return spec
    raise InvalidSettingsError(
        f"La catégorie de paramètres « {section_id} » n'existe pas dans cette version."
    )
