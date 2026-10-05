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

cd "$engine_dir"
uv run pyinstaller \
  --onedir \
  --clean \
  --noconfirm \
  --name engine \
  --paths src \
  --additional-hooks-dir pyinstaller-hooks \
  --collect-submodules engine.modules \
  --add-data "../../docs/guide.md:docs" \
  --distpath dist \
  --workpath build \
  --specpath build \
  pyinstaller-entry.py

mkdir -p "$binaries_dir"
rm -rf "$binaries_dir/_internal"
cp "dist/engine/engine$extension" "$binaries_dir/engine-$target_triple$extension"
cp -R "dist/engine/_internal" "$binaries_dir/_internal"
echo "Sidecar: $binaries_dir/engine-$target_triple$extension"
