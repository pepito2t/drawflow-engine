"""Installs the Drawflow plugin into Stream Dock: download the release zip, unpack it in place."""

import io
import shutil
import zipfile
from pathlib import Path, PurePosixPath

import anyio
import httpx

from engine.core.errors import EngineError
from engine.setup.locations import DRAWFLOW_PLUGIN

RELEASE_ASSET_URL = (
    "https://github.com/pepito2t/drawflow-engine/releases/download/"
    "v{version}/ch.drawflow.sdPlugin.zip"
)
DOWNLOAD_TIMEOUT = httpx.Timeout(connect=10.0, read=60.0, write=30.0, pool=10.0)
MAX_PLUGIN_BYTES = 20_000_000
STAGING_PREFIX = "."
STAGING_SUFFIX = ".new"
REPLACED_SUFFIX = ".old"
RESTART_HINT = "Redémarrez Stream Dock pour l'activer."


class StreamDockError(EngineError):
    pass


def install_plugin(
    plugins: Path, app_version: str, transport: httpx.AsyncBaseTransport | None = None
) -> str:
    archive = anyio.run(_download, RELEASE_ASSET_URL.format(version=app_version), transport)
    staging = plugins / f"{STAGING_PREFIX}{DRAWFLOW_PLUGIN}{STAGING_SUFFIX}"
    _remove(staging)
    _unpack(archive, staging)
    _swap_in(staging, plugins / DRAWFLOW_PLUGIN)
    return f"Plugin Drawflow {app_version} installé dans Stream Dock. {RESTART_HINT}"


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
            f"Le plugin de cette version est introuvable (HTTP {response.status_code}).",
            hint="Mettez Drawflow à jour, puis réessayez.",
        )
    if len(response.content) > MAX_PLUGIN_BYTES:
        raise StreamDockError("Le plugin téléchargé est anormalement volumineux.")
    return response.content


def _unpack(archive: bytes, staging: Path) -> None:
    """Only files under ch.drawflow.sdPlugin/ are written, never outside the staging folder."""
    try:
        with zipfile.ZipFile(io.BytesIO(archive)) as plugin_zip:
            for member in plugin_zip.infolist():
                relative = _relative_member(member.filename)
                if relative is None or member.is_dir():
                    continue
                target = staging.joinpath(*relative.parts)
                target.parent.mkdir(parents=True, exist_ok=True)
                target.write_bytes(plugin_zip.read(member))
    except zipfile.BadZipFile as error:
        raise StreamDockError("Le plugin téléchargé est illisible.") from error
    if not (staging / "manifest.json").is_file():
        raise StreamDockError("Le plugin téléchargé est incomplet (manifest.json absent).")


def _relative_member(name: str) -> PurePosixPath | None:
    path = PurePosixPath(name)
    if path.is_absolute() or ".." in path.parts or not path.parts:
        return None
    inside = path.parts[1:]
    if path.parts[0] != DRAWFLOW_PLUGIN or not inside:
        return None
    return PurePosixPath(*inside)


def _swap_in(staging: Path, target: Path) -> None:
    replaced = target.with_name(f"{STAGING_PREFIX}{DRAWFLOW_PLUGIN}{REPLACED_SUFFIX}")
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
