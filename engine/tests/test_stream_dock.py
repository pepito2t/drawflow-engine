import io
import zipfile
from pathlib import Path

import httpx
import pytest

from engine.core.events import Event
from engine.setup.actions import SetupContext, SetupError, run_action
from engine.setup.stream_dock import StreamDockError, install_plugin
from engine.testing.fake_machine import FakeMachine

PLUGIN = "ch.drawflow.sdPlugin"


def plugin_zip(*extra: tuple[str, bytes]) -> bytes:
    buffer = io.BytesIO()
    with zipfile.ZipFile(buffer, "w") as archive:
        archive.writestr(f"{PLUGIN}/manifest.json", b'{"Name": "Drawflow"}')
        archive.writestr(f"{PLUGIN}/bin/plugin.js", b"console.log('ok');")
        for name, content in extra:
            archive.writestr(name, content)
    return buffer.getvalue()


def release(content: bytes, status: int = 200) -> httpx.MockTransport:
    def handle(request: httpx.Request) -> httpx.Response:
        assert request.url.path.endswith(f"/v0.7.0/{PLUGIN}.zip")
        return httpx.Response(status, content=content)

    return httpx.MockTransport(handle)


def test_plugin_is_unpacked_into_stream_dock(tmp_path: Path) -> None:
    summary = install_plugin(tmp_path, "0.7.0", release(plugin_zip()))

    assert (tmp_path / PLUGIN / "manifest.json").is_file()
    assert (tmp_path / PLUGIN / "bin" / "plugin.js").read_bytes() == b"console.log('ok');"
    assert "Redémarrez Stream Dock" in summary


def test_previous_plugin_is_replaced(tmp_path: Path) -> None:
    old = tmp_path / PLUGIN / "bin" / "obsolete.js"
    old.parent.mkdir(parents=True)
    old.write_text("old")

    install_plugin(tmp_path, "0.7.0", release(plugin_zip()))

    assert not old.exists()
    assert sorted(path.name for path in tmp_path.iterdir()) == [PLUGIN]


def test_entries_outside_the_plugin_folder_are_never_written(tmp_path: Path) -> None:
    plugins = tmp_path / "plugins"
    plugins.mkdir()
    hostile = plugin_zip(
        ("../evil.txt", b"x"), (f"{PLUGIN}/../../evil2.txt", b"x"), ("other/x", b"x")
    )

    install_plugin(plugins, "0.7.0", release(hostile))

    assert not (tmp_path / "evil.txt").exists()
    assert not (tmp_path / "evil2.txt").exists()
    assert not (plugins / "other").exists()


def test_missing_release_asset_is_explained(tmp_path: Path) -> None:
    with pytest.raises(StreamDockError, match="HTTP 404"):
        install_plugin(tmp_path, "0.7.0", release(b"", status=404))


def test_unreadable_download_is_refused(tmp_path: Path) -> None:
    with pytest.raises(StreamDockError, match="illisible"):
        install_plugin(tmp_path, "0.7.0", release(b"pas un zip"))
    assert not (tmp_path / PLUGIN).exists()


def test_action_installs_into_the_stream_dock_of_this_computer(tmp_path: Path) -> None:
    roaming = tmp_path / "Roaming"
    marker = roaming / "HotSpot" / "StreamDock" / "config.json"
    machine = FakeMachine(files={marker}, folders={"APPDATA": roaming})
    events: list[Event] = []
    context = SetupContext(
        settings=tmp_path / "settings.json",
        emit=events.append,
        machine=machine,
        transport=release(plugin_zip()),
        app_version="0.7.0",
    )

    run_action("streamdock.install-plugin", context)

    assert (roaming / "HotSpot" / "StreamDock" / "plugins" / PLUGIN / "manifest.json").is_file()
    assert events[-1].type == "result"


def test_action_without_stream_dock_points_to_its_download_page(tmp_path: Path) -> None:
    context = SetupContext(
        settings=tmp_path / "settings.json",
        emit=lambda _: None,
        machine=FakeMachine(),
        app_version="0.7.0",
    )

    with pytest.raises(SetupError, match="Stream Dock est introuvable"):
        run_action("streamdock.install-plugin", context)
