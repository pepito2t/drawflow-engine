from pathlib import Path

from engine.core.contract import ModuleInputs
from engine.core.fields import ui_field


class HelloInputs(ModuleInputs):
    name: str = ui_field("text", label="Nom", min_length=1)
    output_folder: Path = ui_field("output_folder", label="Dossier de sortie")
