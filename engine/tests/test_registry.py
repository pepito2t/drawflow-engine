import pytest

from engine.core.errors import UnknownModuleError
from engine.core.fields import UI_KIND_SCHEMA_KEY
from engine.core.registry import discover_modules, get_module


def test_discovers_hello_module_automatically() -> None:
    modules = discover_modules()

    assert "hello" in modules
    assert modules["hello"].manifest.name == "Test de fonctionnement"


def test_inputs_schema_exposes_ui_kinds() -> None:
    schema = get_module("hello").inputs_model.model_json_schema()

    properties = schema["properties"]
    assert properties["name"][UI_KIND_SCHEMA_KEY] == "text"
    assert properties["output_folder"][UI_KIND_SCHEMA_KEY] == "output_folder"
    assert set(schema["required"]) == {"name", "output_folder"}


def test_unknown_module_lists_available_ones() -> None:
    with pytest.raises(UnknownModuleError) as caught:
        get_module("does-not-exist")

    assert caught.value.hint is not None
    assert "hello" in caught.value.hint


def test_every_module_documents_how_to_use_it() -> None:
    for module in discover_modules().values():
        assert module.manifest.instructions, module.manifest.id
