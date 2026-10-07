import io
import shutil
import zipfile
from pathlib import Path

import anyio
import httpx
import pytest

from engine.core.events import Event
from engine.setup.actions import SetupContext, SetupError, run_action
from engine.setup.stream_dock import (
    AUTOCAD_PLUGIN_ASSET_URL,
    DRAWFLOW_PLUGIN_ASSET_URL,
    StreamDockError,
    install_plugin,
    latest_release_version,
)
from engine.testing.fake_machine import FakeMachine

PLUGIN = "ch.drawflow.sdPlugin"
AUTOCAD_PLUGIN = "com.tmbk.streamdock.autocad.sdPlugin"
ASSET_URL = DRAWFLOW_PLUGIN_ASSET_URL.format(version="0.7.0")


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
    summary = install_plugin(tmp_path, PLUGIN, ASSET_URL, release(plugin_zip()))

    assert (tmp_path / PLUGIN / "manifest.json").is_file()
    assert (tmp_path / PLUGIN / "bin" / "plugin.js").read_bytes() == b"console.log('ok');"
    assert "Redémarrez Stream Dock" in summary


def test_previous_plugin_is_replaced(tmp_path: Path) -> None:
    old = tmp_path / PLUGIN / "bin" / "obsolete.js"
    old.parent.mkdir(parents=True)
    old.write_text("old")

    install_plugin(tmp_path, PLUGIN, ASSET_URL, release(plugin_zip()))

    assert not old.exists()
    assert sorted(path.name for path in tmp_path.iterdir()) == [PLUGIN]


def test_old_plugin_folder_that_cannot_be_removed_is_a_readable_error(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    (tmp_path / PLUGIN).mkdir()
    real_rmtree = shutil.rmtree

    def refuse_old(path: Path, *arguments: object, **options: object) -> None:
        if path.name.endswith(".old"):
            raise PermissionError("en cours d'utilisation")
        real_rmtree(path, *arguments, **options)

    monkeypatch.setattr(shutil, "rmtree", refuse_old)

    with pytest.raises(StreamDockError, match="supprimé") as caught:
        install_plugin(tmp_path, PLUGIN, ASSET_URL, release(plugin_zip()))

    assert caught.value.file is not None and caught.value.file.name.endswith(".old")
    assert caught.value.hint is not None and "Stream Dock" in caught.value.hint


def test_plugin_folder_that_cannot_be_written_is_a_readable_error(tmp_path: Path) -> None:
    plugins = tmp_path / "plugins"
    plugins.write_text("", encoding="utf-8")

    with pytest.raises(StreamDockError, match="écrit") as caught:
        install_plugin(plugins, PLUGIN, ASSET_URL, release(plugin_zip()))

    assert caught.value.file is not None and caught.value.hint is not None


def test_entries_outside_the_plugin_folder_are_never_written(tmp_path: Path) -> None:
    plugins = tmp_path / "plugins"
    plugins.mkdir()
    hostile = plugin_zip(
        ("../evil.txt", b"x"), (f"{PLUGIN}/../../evil2.txt", b"x"), ("other/x", b"x")
    )

    install_plugin(plugins, PLUGIN, ASSET_URL, release(hostile))

    assert not (tmp_path / "evil.txt").exists()
    assert not (tmp_path / "evil2.txt").exists()
    assert not (plugins / "other").exists()


def test_missing_release_asset_is_explained(tmp_path: Path) -> None:
    with pytest.raises(StreamDockError, match="HTTP 404"):
        install_plugin(tmp_path, PLUGIN, ASSET_URL, release(b"", status=404))


def test_unreadable_download_is_refused(tmp_path: Path) -> None:
    with pytest.raises(StreamDockError, match="illisible"):
        install_plugin(tmp_path, PLUGIN, ASSET_URL, release(b"pas un zip"))
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


def autocad_release(content: bytes) -> httpx.MockTransport:
    def handle(request: httpx.Request) -> httpx.Response:
        assert str(request.url) == AUTOCAD_PLUGIN_ASSET_URL
        return httpx.Response(200, content=content)

    return httpx.MockTransport(handle)


def autocad_zip() -> bytes:
    buffer = io.BytesIO()
    with zipfile.ZipFile(buffer, "w") as archive:
        archive.writestr(f"{AUTOCAD_PLUGIN}/manifest.json", b'{"Version": "1.2.0"}')
        archive.writestr(f"{AUTOCAD_PLUGIN}/plugin.exe", b"MZ")
    return buffer.getvalue()


def test_autocad_plugin_installs_from_its_latest_release(tmp_path: Path) -> None:
    roaming = tmp_path / "Roaming"
    machine = FakeMachine(files={roaming / "HotSpot" / "StreamDock" / "config.json"})
    machine.folders["APPDATA"] = roaming
    events: list[Event] = []
    context = SetupContext(
        settings=tmp_path / "settings.json",
        emit=events.append,
        machine=machine,
        transport=autocad_release(autocad_zip()),
    )

    run_action("streamdock.install-autocad-plugin", context)

    plugin = roaming / "HotSpot" / "StreamDock" / "plugins" / AUTOCAD_PLUGIN
    assert (plugin / "plugin.exe").read_bytes() == b"MZ"
    assert events[-1].type == "result"


def _latest(transport: httpx.MockTransport) -> str | None:
    return anyio.run(latest_release_version, "https://github.com/x/y/releases/latest", transport)


def test_latest_release_version_comes_from_the_tag_redirect() -> None:
    redirect = httpx.MockTransport(
        lambda _: httpx.Response(
            302, headers={"location": "https://github.com/x/y/releases/tag/v1.3.0"}
        )
    )

    assert _latest(redirect) == "1.3.0"


def test_latest_release_version_is_unknown_without_release_or_network() -> None:
    no_release = httpx.MockTransport(lambda _: httpx.Response(200))

    def offline(request: httpx.Request) -> httpx.Response:
        raise httpx.ConnectError("offline", request=request)

    assert _latest(no_release) is None
    assert _latest(httpx.MockTransport(offline)) is None


def test_backslash_and_drive_members_are_never_written(tmp_path: Path) -> None:
    plugins = tmp_path / "plugins"
    plugins.mkdir()
    hostile = plugin_zip(
        (f"{PLUGIN}\\..\\evil3.txt", b"x"),
        (f"{PLUGIN}/bin\\..\\..\\evil4.txt", b"x"),
        (f"{PLUGIN}/C:/evil5.txt", b"x"),
    )

    install_plugin(plugins, PLUGIN, ASSET_URL, release(hostile))

    assert not (tmp_path / "evil3.txt").exists() and not (plugins / "evil3.txt").exists()
    assert not (tmp_path / "evil4.txt").exists() and not (plugins / "evil4.txt").exists()
    written = sorted(
        str(path.relative_to(plugins / PLUGIN)) for path in (plugins / PLUGIN).rglob("*")
    )
    assert not any("evil" in name for name in written)
