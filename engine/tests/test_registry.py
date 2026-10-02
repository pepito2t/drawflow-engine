import pytest
from pydantic import ValidationError

from engine.core.contract import ModuleManifest
from engine.core.errors import UnknownModuleError
from engine.core.fields import UI_KIND_SCHEMA_KEY
from engine.core.registry import discover_modules, get_module


def test_discovers_modules_automatically_in_tab_order() -> None:
    modules = discover_modules()

    assert list(modules) == ["dwg-parts", "pdf-report", "soumission"]
    assert modules["dwg-parts"].manifest.name == "Liste de pièces"


def test_inputs_schema_exposes_ui_kinds() -> None:
    schema = get_module("dwg-parts").inputs_model.model_json_schema()

    properties = schema["properties"]
    assert properties["project"][UI_KIND_SCHEMA_KEY] == "text"
    assert properties["files"][UI_KIND_SCHEMA_KEY] == "files"
    assert properties["output_folder"][UI_KIND_SCHEMA_KEY] == "output_folder"
    assert set(schema["required"]) == {"output_folder"}


def test_unknown_module_lists_available_ones() -> None:
    with pytest.raises(UnknownModuleError) as caught:
        get_module("does-not-exist")

    assert caught.value.hint is not None
    assert "dwg-parts" in caught.value.hint


def test_every_module_documents_how_to_use_it() -> None:
    for module in discover_modules().values():
        assert module.manifest.instructions, module.manifest.id


def test_manifest_icon_defaults_to_generic_and_rejects_unknown() -> None:
    base = {
        "id": "x",
        "name": "X",
        "description": "",
        "version": "0.1.0",
        "order": 0,
        "instructions": ["a"],
    }

    assert ModuleManifest.model_validate(base).icon == "module"
    with pytest.raises(ValidationError):
        ModuleManifest.model_validate({**base, "icon": "rocket"})
