#!/usr/bin/env bash
# Builds the Python engine as a single executable named as Tauri's externalBin expects.
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
  --onefile \
  --clean \
  --noconfirm \
  --name engine \
  --paths src \
  --additional-hooks-dir pyinstaller-hooks \
  --collect-submodules engine.modules \
  --distpath dist \
  --workpath build \
  --specpath build \
  pyinstaller-entry.py

mkdir -p "$binaries_dir"
cp "dist/engine$extension" "$binaries_dir/engine-$target_triple$extension"
echo "Sidecar: $binaries_dir/engine-$target_triple$extension"
