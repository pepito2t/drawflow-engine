"""Installs a plugin into Stream Dock: download its release zip, unpack it in place."""

import io
import shutil
import zipfile
from pathlib import Path, PurePosixPath, PureWindowsPath

import anyio
import httpx

from engine.core.errors import EngineError
from engine.setup.locations import AUTOCAD_PLUGIN, DRAWFLOW_PLUGIN
from engine.setup.messages import t

DRAWFLOW_PLUGIN_ASSET_URL = (
    "https://github.com/pepito2t/drawflow-engine/releases/download/"
    f"v{{version}}/{DRAWFLOW_PLUGIN}.zip"
)
AUTOCAD_PLUGIN_REPOSITORY = "https://github.com/pepito2t/streamdock_autocad"
AUTOCAD_PLUGIN_LATEST_URL = f"{AUTOCAD_PLUGIN_REPOSITORY}/releases/latest"
# The plugin has its own release cycle: Drawflow always installs the newest one.
AUTOCAD_PLUGIN_ASSET_URL = f"{AUTOCAD_PLUGIN_LATEST_URL}/download/{AUTOCAD_PLUGIN}.zip"
RELEASE_TAG_MARKER = "/releases/tag/"
TAG_PREFIX = "v"
DOWNLOAD_TIMEOUT = httpx.Timeout(connect=10.0, read=60.0, write=30.0, pool=10.0)
VERSION_LOOKUP_TIMEOUT = httpx.Timeout(3.0)
MAX_PLUGIN_BYTES = 50_000_000
STAGING_PREFIX = "."
STAGING_SUFFIX = ".new"
REPLACED_SUFFIX = ".old"
PARENT_PART = ".."
BACKSLASH = "\\"
DRIVE_SEPARATOR = ":"


class StreamDockError(EngineError):
    pass


def install_plugin(
    plugins: Path,
    plugin_id: str,
    asset_url: str,
    transport: httpx.AsyncBaseTransport | None = None,
) -> str:
    archive = anyio.run(_download, asset_url, transport)
    staging = plugins / f"{STAGING_PREFIX}{plugin_id}{STAGING_SUFFIX}"
    _remove(staging)
    _unpack(archive, staging, plugin_id)
    _swap_in(staging, plugins / plugin_id, plugin_id)
    return t("stream_dock.installed", plugin_id=plugin_id)


async def latest_release_version(
    latest_url: str, transport: httpx.AsyncBaseTransport | None = None
) -> str | None:
    """GitHub redirects `releases/latest` to the tag page; unreachable or unreleased gives None."""
    async with httpx.AsyncClient(
        timeout=VERSION_LOOKUP_TIMEOUT, transport=transport, follow_redirects=False
    ) as http:
        try:
            response = await http.head(latest_url)
        except httpx.TransportError:
            return None
    location: str = response.headers.get("location", "")
    if RELEASE_TAG_MARKER not in location:
        return None
    return location.rsplit(RELEASE_TAG_MARKER, 1)[1].strip("/").removeprefix(TAG_PREFIX)


async def _download(url: str, transport: httpx.AsyncBaseTransport | None) -> bytes:
    async with httpx.AsyncClient(
        timeout=DOWNLOAD_TIMEOUT, transport=transport, follow_redirects=True
    ) as http:
        try:
            response = await http.get(url)
        except httpx.TransportError as error:
            raise StreamDockError(
                t("stream_dock.download_failed"), hint=t("stream_dock.download_failed.hint")
            ) from error
    if not response.is_success:
        raise StreamDockError(
            t("stream_dock.not_found", status=response.status_code),
            hint=t("stream_dock.not_found.hint"),
        )
    if len(response.content) > MAX_PLUGIN_BYTES:
        raise StreamDockError(t("stream_dock.too_large"))
    return response.content


def _unpack(archive: bytes, staging: Path, plugin_id: str) -> None:
    """Only files under <plugin_id>/ are written, never outside the staging folder."""
    try:
        with zipfile.ZipFile(io.BytesIO(archive)) as plugin_zip:
            for member in plugin_zip.infolist():
                relative = _relative_member(member.filename, plugin_id)
                if relative is None or member.is_dir():
                    continue
                target = _inside(staging, relative)
                if target is None:
                    continue
                target.parent.mkdir(parents=True, exist_ok=True)
                target.write_bytes(plugin_zip.read(member))
    except zipfile.BadZipFile as error:
        raise StreamDockError(t("stream_dock.unreadable")) from error
    if not (staging / "manifest.json").is_file():
        raise StreamDockError(t("stream_dock.incomplete"))


def _relative_member(name: str, plugin_id: str) -> PurePosixPath | None:
    # Zip names are "/"-separated; a backslash or a colon only means something to Windows.
    if BACKSLASH in name or DRIVE_SEPARATOR in name or _escapes(name):
        return None
    path = PurePosixPath(name)
    inside = path.parts[1:]
    if not path.parts or path.parts[0] != plugin_id or not inside:
        return None
    return PurePosixPath(*inside)


def _escapes(name: str) -> bool:
    posix, windows = PurePosixPath(name), PureWindowsPath(name)
    if posix.is_absolute() or windows.is_absolute():
        return True
    return PARENT_PART in posix.parts or PARENT_PART in windows.parts


def _inside(staging: Path, relative: PurePosixPath) -> Path | None:
    target = staging.joinpath(*relative.parts)
    root = staging.resolve()
    return target if target.resolve().is_relative_to(root) else None


def _swap_in(staging: Path, target: Path, plugin_id: str) -> None:
    replaced = target.with_name(f"{STAGING_PREFIX}{plugin_id}{REPLACED_SUFFIX}")
    try:
        _remove(replaced)
        if target.exists():
            target.rename(replaced)
        staging.rename(target)
    except OSError as error:
        raise StreamDockError(
            t("stream_dock.in_use"), file=target, hint=t("stream_dock.in_use.hint")
        ) from error
    _remove(replaced)


def _remove(folder: Path) -> None:
    if folder.exists():
        shutil.rmtree(folder)
