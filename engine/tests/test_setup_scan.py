from pathlib import Path
from typing import Any

import httpx
import pytest

from engine.core.settings_models import AssistantSettings
from engine.setup import service
from engine.setup.scan import ModelServerState, build_report
from engine.testing.fake_machine import APPDATA, LOCALAPPDATA, PROGRAM_FILES, FakeMachine

ODA_2025 = PROGRAM_FILES / "ODA" / "ODAFileConverter 25.12.0" / "ODAFileConverter.exe"
ODA_2026 = PROGRAM_FILES / "ODA" / "ODAFileConverter 26.4.0" / "ODAFileConverter.exe"
SERVER_DOWN = ModelServerState(reachable=False, is_ollama=False, available=[])


def report(
    machine: FakeMachine,
    server: ModelServerState = SERVER_DOWN,
    oda: Path | None = None,
) -> dict[str, Any]:
    built = build_report(machine, oda, AssistantSettings(), server)
    return {item.id: item for item in built.items}


def action_ids(item: Any) -> list[str]:
    return [action.id for action in item.actions]


def test_fresh_windows_with_winget_offers_direct_installs() -> None:
    items = report(FakeMachine(programs={"winget"}))

    assert action_ids(items["oda"]) == ["oda.install", "oda.open-page"]
    assert action_ids(items["model-server"]) == ["ollama.install", "ollama.open-page"]
    assert items["model"].status == "missing"
    assert items["stream-dock"].status == "optional"


def test_without_package_manager_oda_still_installs_from_its_own_installer() -> None:
    items = report(FakeMachine())

    assert action_ids(items["oda"]) == ["oda.install", "oda.open-page"]
    assert action_ids(items["model-server"]) == ["ollama.open-page"]


def test_installed_but_unconfigured_oda_is_detected_with_the_latest_version() -> None:
    items = report(FakeMachine(files={ODA_2025, ODA_2026}))

    assert action_ids(items["oda"]) == ["oda.use-detected"]
    assert items["oda"].detail.endswith(str(ODA_2026))


def test_configured_oda_that_exists_is_ok() -> None:
    items = report(FakeMachine(files={ODA_2026}), oda=ODA_2026)

    assert items["oda"].status == "ok"


def test_installed_ollama_that_does_not_answer_can_be_started() -> None:
    machine = FakeMachine(files={LOCALAPPDATA / "Programs" / "Ollama" / "ollama.exe"})

    assert action_ids(report(machine)["model-server"]) == ["ollama.start"]


def test_missing_model_on_ollama_can_be_pulled() -> None:
    server = ModelServerState(reachable=True, is_ollama=True, available=["llama3.1:8b"])

    items = report(FakeMachine(), server)

    assert items["model-server"].status == "ok"
    assert action_ids(items["model"]) == ["model.pull", "models.open"]
    assert "Recommandé pour ce poste" in items["model"].detail


def test_missing_model_on_another_server_cannot_be_pulled() -> None:
    server = ModelServerState(reachable=True, is_ollama=False, available=[])

    assert action_ids(report(FakeMachine(), server)["model"]) == []


def test_stream_dock_plugin_install_is_offered_once_stream_dock_is_there() -> None:
    stream_dock = APPDATA / "HotSpot" / "StreamDock" / "config.json"
    plugin = (
        APPDATA / "HotSpot" / "StreamDock" / "plugins" / "ch.drawflow.sdPlugin" / "manifest.json"
    )

    absent = report(FakeMachine())["stream-dock"]
    without_plugin = report(FakeMachine(files={stream_dock}))["stream-dock"]
    with_plugin = report(FakeMachine(files={stream_dock, plugin}))["stream-dock"]

    assert action_ids(absent) == ["streamdock.open-page"]
    assert absent.actions[0].url == "https://mirabox.net/pages/download"
    assert action_ids(without_plugin) == ["streamdock.install-plugin"]
    assert with_plugin.status == "ok"
    assert action_ids(with_plugin) == ["streamdock.install-plugin"]


def test_macos_installs_ollama_with_homebrew_but_not_oda() -> None:
    items = report(FakeMachine(os="macos", programs={"brew"}))

    assert action_ids(items["oda"]) == ["oda.open-page"]
    assert action_ids(items["model-server"]) == ["ollama.install", "ollama.open-page"]


def _server(version_body: object) -> httpx.MockTransport:
    def handle(request: httpx.Request) -> httpx.Response:
        if request.url.path.endswith("/models"):
            return httpx.Response(200, json={"data": [{"id": "qwen2.5:7b"}]})
        return httpx.Response(200, json=version_body)

    return httpx.MockTransport(handle)


@pytest.mark.parametrize(
    ("version_body", "is_ollama"),
    [({"version": "0.12.0"}, True), ({"error": "Unexpected endpoint"}, False)],
)
def test_scan_tells_ollama_from_other_servers(
    tmp_path: Path, version_body: object, is_ollama: bool
) -> None:
    scanned = service.scan(tmp_path / "settings.json", FakeMachine(), _server(version_body))

    server_item = next(item for item in scanned["items"] if item["id"] == "model-server")
    assert server_item["status"] == "ok"
    assert server_item["detail"].startswith("Ollama") is is_ollama


def test_scan_reports_an_unreachable_server(tmp_path: Path) -> None:
    def refuse(request: httpx.Request) -> httpx.Response:
        raise httpx.ConnectError("refused", request=request)

    scanned = service.scan(tmp_path / "settings.json", FakeMachine(), httpx.MockTransport(refuse))

    statuses = {item["id"]: item["status"] for item in scanned["items"]}
    assert statuses["model-server"] == "missing"
    assert scanned["system"] == {"os": "windows", "arch": "amd64", "package_manager": None}
