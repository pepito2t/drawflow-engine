import json
from pathlib import Path
from typing import Any

import pytest

from engine.core.contract import (
    EngineModule,
    ModuleInputs,
    ModuleManifest,
    ModuleResult,
    RunContext,
)
from engine.core.errors import InvalidSettingsError, ModuleContractError, SettingsFileError
from engine.core.fields import ui_field
from engine.core.registry import AnyModule
from engine.core.settings import (
    describe_settings,
    load_run_settings,
    read_document,
    save_settings,
    section_specs,
)
from engine.core.settings_models import DEFAULT_BATCH_SIZE, ModuleSettings


class SampleSettings(ModuleSettings):
    prefix: str = ui_field("text", label="Préfixe", default="LP", min_length=1)


class SampleInputs(ModuleInputs):
    pass


def _unused_run(inputs: SampleInputs, context: RunContext) -> ModuleResult:
    return ModuleResult(summary="")


def make_module(
    module_id: str = "sample", settings: type[ModuleSettings] | None = None
) -> AnyModule:
    manifest = ModuleManifest(
        id=module_id,
        name="Exemple",
        description="",
        version="0.1.0",
        order=0,
        instructions=["Lancer."],
    )
    return EngineModule(manifest, SampleInputs, _unused_run, settings_model=settings)


@pytest.fixture
def modules() -> dict[str, AnyModule]:
    return {"sample": make_module(settings=SampleSettings)}


@pytest.fixture
def settings_file(tmp_path: Path) -> Path:
    return tmp_path / "Réglages utilisateur" / "settings.json"


def test_missing_file_yields_defaults(settings_file: Path, modules: dict[str, AnyModule]) -> None:
    settings = load_run_settings(settings_file, modules["sample"])

    assert settings.general.batch_size == DEFAULT_BATCH_SIZE
    assert settings.module == SampleSettings()


def test_save_then_load_round_trip(settings_file: Path, modules: dict[str, AnyModule]) -> None:
    save_settings(settings_file, {"general": {"batch_size": 8}, "sample": {"prefix": "X"}}, modules)

    settings = load_run_settings(settings_file, modules["sample"])

    assert settings.general.batch_size == 8
    assert settings.module == SampleSettings(prefix="X")


def test_save_keeps_sections_not_submitted(
    settings_file: Path, modules: dict[str, AnyModule]
) -> None:
    save_settings(settings_file, {"sample": {"prefix": "X"}}, modules)
    save_settings(settings_file, {"general": {"batch_size": 2}}, modules)

    document = read_document(settings_file)

    assert document["modules"]["sample"] == {"prefix": "X"}
    assert document["general"]["batch_size"] == 2


def test_save_preserves_sections_of_removed_modules(
    settings_file: Path, modules: dict[str, AnyModule]
) -> None:
    settings_file.parent.mkdir(parents=True)
    settings_file.write_text(json.dumps({"modules": {"old": {"a": 1}}}), encoding="utf-8")

    save_settings(settings_file, {"general": {"batch_size": 2}}, modules)

    assert read_document(settings_file)["modules"]["old"] == {"a": 1}


def test_invalid_values_are_rejected_with_labels_and_not_written(
    settings_file: Path, modules: dict[str, AnyModule]
) -> None:
    with pytest.raises(InvalidSettingsError) as caught:
        save_settings(
            settings_file, {"general": {"batch_size": 0}, "sample": {"prefix": ""}}, modules
        )

    assert "Fichiers traités en parallèle" in caught.value.message
    assert "Préfixe" in caught.value.message
    assert not settings_file.exists()


def test_corrupted_file_is_reported_and_left_untouched(
    settings_file: Path, modules: dict[str, AnyModule]
) -> None:
    settings_file.parent.mkdir(parents=True)
    settings_file.write_text("{not json", encoding="utf-8")

    with pytest.raises(SettingsFileError) as caught:
        save_settings(settings_file, {"general": {}}, modules)

    assert caught.value.file == settings_file
    assert settings_file.read_text(encoding="utf-8") == "{not json"


def test_invalid_stored_section_fails_the_run_with_a_readable_error(
    settings_file: Path, modules: dict[str, AnyModule]
) -> None:
    settings_file.parent.mkdir(parents=True)
    settings_file.write_text(json.dumps({"general": {"batch_size": -1}}), encoding="utf-8")

    with pytest.raises(InvalidSettingsError) as caught:
        load_run_settings(settings_file, modules["sample"])

    assert caught.value.hint is not None


def test_describe_lists_general_then_module_sections(
    settings_file: Path, modules: dict[str, AnyModule]
) -> None:
    sections = describe_settings(settings_file, modules)

    assert [section["id"] for section in sections] == ["general", "sample"]
    general: dict[str, Any] = sections[0]
    assert general["values"]["batch_size"] == DEFAULT_BATCH_SIZE
    assert general["schema"]["properties"]["batch_size"]["x-ui"] == "number"
    assert general["error"] is None


def test_describe_falls_back_to_defaults_and_reports_invalid_section(
    settings_file: Path, modules: dict[str, AnyModule]
) -> None:
    settings_file.parent.mkdir(parents=True)
    settings_file.write_text(json.dumps({"modules": {"sample": {"prefix": ""}}}), encoding="utf-8")

    sample = describe_settings(settings_file, modules)[1]

    assert sample["values"] == {"prefix": "LP"}
    assert "Préfixe" in sample["error"]


def test_general_is_a_reserved_module_id() -> None:
    with pytest.raises(ModuleContractError):
        section_specs({"general": make_module("general", SampleSettings)})
