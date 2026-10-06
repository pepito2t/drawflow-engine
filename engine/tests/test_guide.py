import json
import subprocess
import sys

import pytest

from engine.core.errors import InvalidInputError
from engine.core.guide import _sections, read_section, sections, slug
from engine.setup.scan import PREREQUISITES_HELP, STREAM_DOCK_HELP


def test_guide_starts_with_the_step_by_step_walkthrough() -> None:
    assert sections()[0].title == "Premiers pas"
    assert "1. **Installer Drawflow**" in sections()[0].markdown


def test_anchors_match_github() -> None:
    assert slug("Utiliser l'assistant") == "utiliser-lassistant"
    assert slug("Installer les prérequis") == "installer-les-prérequis"


@pytest.mark.parametrize(
    "topic", ["piloter-avec-un-stream-dock", "PILOTER avec un stream dock", "stream dock"]
)
def test_sections_are_found_by_id_title_or_part_of_it(topic: str) -> None:
    assert read_section(topic).title == "Piloter avec un Stream Dock"


def test_unknown_section_lists_the_available_ones() -> None:
    with pytest.raises(InvalidInputError) as caught:
        read_section("fusée")
    assert caught.value.hint is not None
    assert "premiers-pas" in caught.value.hint


def test_every_section_linked_from_the_installation_screen_exists() -> None:
    ids = {section.id for section in sections()}
    assert {PREREQUISITES_HELP, STREAM_DOCK_HELP} <= ids


def test_cli_returns_the_whole_guide() -> None:
    completed = subprocess.run(
        [sys.executable, "-m", "engine.cli", "help", "guide", "--settings", "settings.json"],
        capture_output=True,
        text=True,
        encoding="utf-8",
        check=True,
    )
    guide = json.loads(completed.stdout)
    assert guide["sections"][0]["id"] == "premiers-pas"


def test_french_topics_open_the_same_section_of_the_english_guide() -> None:
    from engine.core.i18n import set_language

    set_language("en")
    try:
        assert len(_sections("en")) == len(_sections("fr"))
        assert read_section("installer-les-prérequis").title == "Install the prerequisites"
        assert read_section("piloter-avec-un-stream-dock").title == "Control with a Stream Dock"
        assert read_section("troubleshooting").title == "Troubleshooting"
    finally:
        set_language("fr")
