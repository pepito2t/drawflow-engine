#!/usr/bin/env bash
# Builds the Python engine as a folder: the executable goes to Tauri's externalBin, its
# _internal libraries are bundled next to it (a single-file build unpacks itself on every call).
set -euo pipefail

repo_root="$(cd "$(dirname "$0")/.." && pwd)"
engine_dir="$repo_root/engine"
binaries_dir="$repo_root/src-tauri/binaries"
target_triple="$(rustc --print host-tuple)"
extension=""
if [[ "$target_triple" == *windows* ]]; then
  extension=".exe"
fi

# A clean build is only worth its time on a fresh CI runner; locally the cache is reused.
clean_option=""
if [[ -n "${CI:-}" ]]; then
  clean_option="--clean"
fi

cd "$engine_dir"
# Modules are collected by pyinstaller-hooks/hook-engine.modules.py, without their tests.
uv run pyinstaller \
  --onedir \
  $clean_option \
  --noconfirm \
  --name engine \
  --paths src \
  --additional-hooks-dir pyinstaller-hooks \
  --exclude-module mypy \
  --exclude-module pydantic.mypy \
  --exclude-module pydantic.v1.mypy \
  --exclude-module pytest \
  --exclude-module _pytest \
  --add-data "../../docs/guide.md:docs" \
  --add-data "../../docs/guide.en.md:docs" \
  --distpath dist \
  --workpath build \
  --specpath build \
  pyinstaller-entry.py

mkdir -p "$binaries_dir"
rm -rf "$binaries_dir/_internal"
cp "dist/engine/engine$extension" "$binaries_dir/engine-$target_triple$extension"
cp -R "dist/engine/_internal" "$binaries_dir/_internal"
echo "Sidecar: $binaries_dir/engine-$target_triple$extension"
