import json
from pathlib import Path

import pytest

from engine.assistant.conversation import MAX_HISTORY_MESSAGES
from engine.assistant.history import HISTORY_FILE, read_history, save_history
from engine.core.errors import InvalidInputError


def test_saved_conversation_is_read_back(tmp_path: Path) -> None:
    settings = tmp_path / "Réglages é" / "settings.json"
    messages = [
        {"role": "user", "content": "Quels préréglages ?"},
        {"role": "assistant", "content": "Chantier Nord."},
    ]

    save_history(settings, {"messages": messages})

    assert read_history(settings) == {"messages": messages}


def test_only_the_most_recent_messages_are_kept(tmp_path: Path) -> None:
    settings = tmp_path / "settings.json"
    messages = [{"role": "user", "content": f"Question {index}"} for index in range(60)]

    kept = save_history(settings, {"messages": messages})

    assert len(kept["messages"]) == MAX_HISTORY_MESSAGES
    assert kept["messages"][-1]["content"] == "Question 59"


def test_no_conversation_yet_is_empty(tmp_path: Path) -> None:
    assert read_history(tmp_path / "settings.json") == {"messages": []}


def test_unreadable_conversation_starts_afresh_without_being_overwritten(tmp_path: Path) -> None:
    (tmp_path / HISTORY_FILE).write_text("{pas du json", encoding="utf-8")

    history = read_history(tmp_path / "settings.json")

    assert history["messages"] == []
    assert "illisible" in history["warning"]
    assert (tmp_path / HISTORY_FILE).read_text(encoding="utf-8") == "{pas du json"


def test_empty_list_clears_the_conversation(tmp_path: Path) -> None:
    settings = tmp_path / "settings.json"
    save_history(settings, {"messages": [{"role": "user", "content": "Salut"}]})

    save_history(settings, {"messages": []})

    assert json.loads((tmp_path / HISTORY_FILE).read_text(encoding="utf-8")) == {"messages": []}


def test_invalid_conversation_is_refused_without_echoing_its_content(tmp_path: Path) -> None:
    secret = "Texte confidentiel"

    with pytest.raises(InvalidInputError) as caught:
        save_history(
            tmp_path / "settings.json", {"messages": [{"role": "system", "content": secret}]}
        )

    assert caught.value.hint is not None
    assert "messages.0.role" in caught.value.hint
    assert secret not in caught.value.hint and "input_value" not in caught.value.hint
