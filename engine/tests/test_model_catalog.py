import json
from pathlib import Path

import httpx
import pytest

from engine.assistant import models
from engine.assistant.catalog import BYTES_PER_GB, recommend
from engine.assistant.errors import AssistantError
from engine.core.errors import InvalidInputError
from engine.core.events import Event
from engine.testing.fake_machine import FakeMachine

GB = BYTES_PER_GB


@pytest.mark.parametrize(
    ("memory_bytes", "expected"),
    [
        (8 * GB, "qwen3.5:4b"),
        (12 * GB, "qwen3.5:4b"),
        (17 * GB, "qwen3.5:9b"),
        (64 * GB, "qwen3.5:27b"),
        (2 * GB, "qwen3.5:2b"),
        (None, "qwen3.5:9b"),
    ],
)
def test_recommendation_is_the_most_capable_model_that_fits(
    memory_bytes: int | None, expected: str
) -> None:
    assert recommend(memory_bytes) == expected


def ollama(
    installed: dict[str, int], requests: list[httpx.Request] | None = None
) -> httpx.MockTransport:
    def handle(request: httpx.Request) -> httpx.Response:
        if requests is not None:
            requests.append(request)
        path = request.url.path
        if path == "/api/version":
            return httpx.Response(200, json={"version": "0.12.0"})
        if path == "/api/tags":
            models_json = [{"name": name, "size": size} for name, size in installed.items()]
            return httpx.Response(200, json={"models": models_json})
        if path == "/api/pull":
            lines = [{"status": "downloading", "total": 10, "completed": 5}, {"status": "success"}]
            return httpx.Response(200, content="\n".join(json.dumps(x) for x in lines).encode())
        if path == "/api/delete":
            return httpx.Response(200)
        return httpx.Response(404)

    return httpx.MockTransport(handle)


def test_catalog_lists_curated_and_other_installed_models(tmp_path: Path) -> None:
    machine = FakeMachine(memory=17 * GB)
    installed = {"qwen3.5:9b": int(6.6 * GB), "mistral-nemo:latest": int(7.1 * GB)}

    listed = models.catalog(tmp_path / "settings.json", machine, ollama(installed))

    assert listed["recommended"] == "qwen3.5:9b"
    assert listed["memory_gb"] == 17.0
    assert listed["is_ollama"] is True
    assert listed["server_url"] == "http://127.0.0.1:11434/v1"
    by_name = {model["name"]: model for model in listed["models"]}
    assert by_name["qwen3.5:9b"]["installed"] is True
    assert by_name["qwen3.5:4b"]["installed"] is False
    assert by_name["mistral-nemo:latest"] == {
        "name": "mistral-nemo:latest",
        "label": "mistral-nemo:latest",
        "size_gb": 7.1,
        "min_memory_gb": None,
        "description": "",
        "installed": True,
    }


def test_catalog_without_ollama_still_recommends(tmp_path: Path) -> None:
    def refuse(request: httpx.Request) -> httpx.Response:
        raise httpx.ConnectError("refused", request=request)

    listed = models.catalog(tmp_path / "settings.json", FakeMachine(), httpx.MockTransport(refuse))

    assert listed["is_ollama"] is False
    assert not any(model["installed"] for model in listed["models"])


def test_pull_reports_progress_then_the_result(tmp_path: Path) -> None:
    events: list[Event] = []

    models.pull(tmp_path / "settings.json", " Qwen3.5:4B ", events.append, ollama({}))

    assert [event.type for event in events] == ["progress", "result"]
    assert events[-1].type == "result"
    assert "qwen3.5:4b" in events[-1].summary


def test_pull_needs_ollama(tmp_path: Path) -> None:
    lm_studio = httpx.MockTransport(lambda _: httpx.Response(200, json={"error": "Unexpected"}))

    with pytest.raises(AssistantError, match="Ollama ne répond pas") as caught:
        models.pull(tmp_path / "settings.json", "qwen3.5:4b", lambda _: None, lm_studio)
    assert caught.value.hint is not None
    assert "LM Studio" in caught.value.hint


@pytest.mark.parametrize("name", ["", "../../etc", "qwen 3", "rm -rf /", "a:b:c"])
def test_invalid_model_names_are_refused(tmp_path: Path, name: str) -> None:
    with pytest.raises(InvalidInputError):
        models.pull(tmp_path / "settings.json", name, lambda _: None, ollama({}))


def test_delete_asks_ollama_to_remove_the_model(tmp_path: Path) -> None:
    requests: list[httpx.Request] = []

    deleted = models.remove(tmp_path / "settings.json", {"model": "qwen3:8b"}, ollama({}, requests))

    assert deleted == {"deleted": "qwen3:8b"}
    assert requests[-1].method == "DELETE"
    assert json.loads(requests[-1].content) == {"model": "qwen3:8b"}
