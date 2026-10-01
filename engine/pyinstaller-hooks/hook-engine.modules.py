from PyInstaller.utils.hooks import collect_submodules

# Modules are discovered at runtime via pkgutil, so PyInstaller cannot see them statically.
hiddenimports = collect_submodules("engine.modules", filter=lambda name: ".tests" not in name)
