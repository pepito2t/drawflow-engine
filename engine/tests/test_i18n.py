import json
import subprocess
import sys
from pathlib import Path

import pytest

from engine.core import i18n
from engine.core.i18n import (
    CATALOGS,
    catalog_issues,
    current_language,
    define_messages,
    language_from_argv,
    set_language,
)


@pytest.fixture(autouse=True)
def _french_by_default() -> None:
    set_language("fr")


def test_messages_follow_the_current_language() -> None:
    t = define_messages(fr={"hello": "Bonjour {name}"}, en={"hello": "Hello {name}"})
    try:
        assert t("hello", name="Léa") == "Bonjour Léa"
        set_language("en")
        assert t("hello", name="Léa") == "Hello Léa" and current_language() == "en"
    finally:
        CATALOGS.remove({"fr": {"hello": "Bonjour {name}"}, "en": {"hello": "Hello {name}"}})


def test_every_catalog_has_the_same_keys_and_placeholders() -> None:
    assert CATALOGS, "aucun catalogue chargé"
    assert [issue for catalog in CATALOGS for issue in catalog_issues(catalog)] == []


def test_catalog_issues_are_named() -> None:
    issues = catalog_issues({"fr": {"a": "{x}", "b": "y"}, "en": {"a": "{z}"}})
    assert issues == [
        "clé « b » absente d'une langue",
        "clé « a » : paramètres différents entre fr et en",
    ]


def test_language_comes_from_the_flag_or_the_settings(tmp_path: Path) -> None:
    settings = tmp_path / "settings.json"
    settings.write_text(json.dumps({"general": {"language": "en"}}), encoding="utf-8")

    assert language_from_argv(["run", "x", "--lang", "en"]) == "en"
    assert language_from_argv(["run", "--lang=fr", "--settings", str(settings)]) == "fr"
    assert language_from_argv(["run", "--settings", str(settings)]) == "en"
    assert language_from_argv(["run", "--settings", str(tmp_path / "absent.json")]) is None
    assert language_from_argv(["run", "--lang", "de"]) is None
    assert i18n.DEFAULT_LANGUAGE == "fr"


def test_cli_lists_modules_in_english_on_request() -> None:
    listed = subprocess.run(
        [sys.executable, "-m", "engine.cli", "--lang", "en", "list-modules"],
        capture_output=True,
        encoding="utf-8",
        check=True,
    )
    names = [item["manifest"]["name"] for item in json.loads(listed.stdout)]
    assert "Parts list" in names
