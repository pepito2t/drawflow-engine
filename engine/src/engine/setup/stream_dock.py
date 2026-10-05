"""Installs a plugin into Stream Dock: download its release zip, unpack it in place."""

import io
import shutil
import zipfile
from pathlib import Path, PurePosixPath

import anyio
import httpx

from engine.core.errors import EngineError
from engine.setup.locations import AUTOCAD_PLUGIN, DRAWFLOW_PLUGIN

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
RESTART_HINT = "Redémarrez Stream Dock pour l'activer."


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
    return f"Plugin {plugin_id} installé dans Stream Dock. {RESTART_HINT}"


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
                "Téléchargement du plugin impossible.",
                hint="Vérifiez la connexion Internet, puis réessayez.",
            ) from error
    if not response.is_success:
        raise StreamDockError(
            f"Le plugin est introuvable à cette adresse (HTTP {response.status_code}).",
            hint="Aucune version publiée, ou Drawflow à mettre à jour ; réessayez plus tard.",
        )
    if len(response.content) > MAX_PLUGIN_BYTES:
        raise StreamDockError("Le plugin téléchargé est anormalement volumineux.")
    return response.content


def _unpack(archive: bytes, staging: Path, plugin_id: str) -> None:
    """Only files under <plugin_id>/ are written, never outside the staging folder."""
    try:
        with zipfile.ZipFile(io.BytesIO(archive)) as plugin_zip:
            for member in plugin_zip.infolist():
                relative = _relative_member(member.filename, plugin_id)
                if relative is None or member.is_dir():
                    continue
                target = staging.joinpath(*relative.parts)
                target.parent.mkdir(parents=True, exist_ok=True)
                target.write_bytes(plugin_zip.read(member))
    except zipfile.BadZipFile as error:
        raise StreamDockError("Le plugin téléchargé est illisible.") from error
    if not (staging / "manifest.json").is_file():
        raise StreamDockError("Le plugin téléchargé est incomplet (manifest.json absent).")


def _relative_member(name: str, plugin_id: str) -> PurePosixPath | None:
    path = PurePosixPath(name)
    if path.is_absolute() or ".." in path.parts or not path.parts:
        return None
    inside = path.parts[1:]
    if path.parts[0] != plugin_id or not inside:
        return None
    return PurePosixPath(*inside)


def _swap_in(staging: Path, target: Path, plugin_id: str) -> None:
    replaced = target.with_name(f"{STAGING_PREFIX}{plugin_id}{REPLACED_SUFFIX}")
    try:
        _remove(replaced)
        if target.exists():
            target.rename(replaced)
        staging.rename(target)
    except OSError as error:
        raise StreamDockError(
            "Le plugin n'a pas pu être remplacé : Stream Dock l'utilise encore.",
            file=target,
            hint="Quittez Stream Dock, cliquez à nouveau sur Installer, puis relancez Stream Dock.",
        ) from error
    _remove(replaced)


def _remove(folder: Path) -> None:
    if folder.exists():
        shutil.rmtree(folder)
