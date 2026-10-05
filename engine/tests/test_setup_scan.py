from pathlib import Path
from typing import Any

import httpx
import pytest

from engine.core.settings_models import AssistantSettings
from engine.setup import service
from engine.setup.machine import LocalMachine
from engine.setup.scan import ModelServerState, build_report
from engine.testing.fake_machine import APPDATA, LOCALAPPDATA, PROGRAM_FILES, FakeMachine

ODA_2025 = PROGRAM_FILES / "ODA" / "ODAFileConverter 25.12.0" / "ODAFileConverter.exe"
ODA_2026 = PROGRAM_FILES / "ODA" / "ODAFileConverter 26.4.0" / "ODAFileConverter.exe"
SERVER_DOWN = ModelServerState(reachable=False, is_ollama=False, available=[])


def report(
    machine: FakeMachine,
    server: ModelServerState = SERVER_DOWN,
    oda: Path | None = None,
    app_version: str | None = None,
    autocad_latest: str | None = None,
) -> dict[str, Any]:
    built = build_report(machine, oda, AssistantSettings(), server, app_version, autocad_latest)
    return {item.id: item for item in built.items}


STREAM_DOCK = APPDATA / "HotSpot" / "StreamDock"
DRAWFLOW_MANIFEST = STREAM_DOCK / "plugins" / "ch.drawflow.sdPlugin" / "manifest.json"
AUTOCAD_MANIFEST = (
    STREAM_DOCK / "plugins" / "com.tmbk.streamdock.autocad.sdPlugin" / "manifest.json"
)
AUTOCAD_EXE = PROGRAM_FILES / "Autodesk" / "AutoCAD 2025" / "acad.exe"
AUTOCAD_LT_EXE = PROGRAM_FILES / "Autodesk" / "AutoCAD LT 2025" / "acadlt.exe"


def action_ids(item: Any) -> list[str]:
    return [action.id for action in item.actions]


def test_fresh_windows_with_winget_offers_direct_installs() -> None:
    items = report(FakeMachine(programs={"winget"}))

    assert action_ids(items["oda"]) == ["oda.install", "oda.open-page"]
    assert action_ids(items["model-server"]) == ["ollama.install", "ollama.open-page"]
    assert items["model"].status == "missing"
    assert items["stream-dock"].status == "optional"


def test_windows_without_winget_still_installs_from_the_official_installers() -> None:
    items = report(FakeMachine())

    assert action_ids(items["oda"]) == ["oda.install", "oda.open-page"]
    assert action_ids(items["model-server"]) == ["ollama.install", "ollama.open-page"]


def test_macos_without_homebrew_only_offers_the_download_pages() -> None:
    items = report(FakeMachine(os="macos"))

    assert action_ids(items["oda"]) == ["oda.open-page"]
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


def test_drawflow_plugin_reports_an_update_when_its_version_differs_from_the_app() -> None:
    files = {STREAM_DOCK / "config.json"}
    outdated = FakeMachine(files=files, contents={DRAWFLOW_MANIFEST: '{"Version": "0.7.0"}'})
    current = FakeMachine(files=files, contents={DRAWFLOW_MANIFEST: '{"Version": "0.8.1"}'})

    update = report(outdated, app_version="0.8.1")["stream-dock"]
    ok = report(current, app_version="0.8.1")["stream-dock"]

    assert update.status == "update"
    assert "0.7.0" in update.detail and "0.8.1" in update.detail
    assert [(a.id, a.label) for a in update.actions] == [
        ("streamdock.install-plugin", "Mettre à jour")
    ]
    assert ok.status == "ok"
    assert action_ids(ok) == ["streamdock.install-plugin"]


def test_autocad_plugin_item_follows_stream_dock_autocad_and_the_latest_release() -> None:
    absent = report(FakeMachine())["autocad-plugin"]
    installable = report(FakeMachine(files={STREAM_DOCK / "config.json", AUTOCAD_LT_EXE}))[
        "autocad-plugin"
    ]
    installed = FakeMachine(
        files={STREAM_DOCK / "config.json", AUTOCAD_EXE},
        contents={AUTOCAD_MANIFEST: '{"Version": "1.2.0"}'},
    )

    up_to_date = report(installed, autocad_latest="1.2.0")["autocad-plugin"]
    outdated = report(installed, autocad_latest="1.3.0")["autocad-plugin"]
    unknown = report(installed)["autocad-plugin"]

    assert absent.status == "optional"
    assert action_ids(absent) == ["autocad-plugin.open-page"]
    assert installable.status == "optional"
    assert "non détecté" in installable.detail
    assert action_ids(installable) == [
        "streamdock.install-autocad-plugin",
        "autocad-plugin.open-page",
    ]
    assert up_to_date.status == "ok"
    assert "AutoCAD détecté" in up_to_date.detail
    assert outdated.status == "update"
    assert outdated.actions[0].label == "Mettre à jour"
    assert unknown.status == "ok"


def test_local_machine_reads_a_manifest_or_nothing(tmp_path: Path) -> None:
    manifest = tmp_path / "manifest.json"
    manifest.write_text('{"Version": "1.0.0"}', encoding="utf-8")

    assert LocalMachine().read_text(manifest) == '{"Version": "1.0.0"}'
    assert LocalMachine().read_text(tmp_path / "absent.json") is None
