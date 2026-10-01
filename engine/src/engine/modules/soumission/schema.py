from pathlib import Path

from pydantic import model_validator

from engine.core.contract import ModuleInputs
from engine.core.fields import ui_field


class SoumissionInputs(ModuleInputs):
    files: list[Path] = ui_field(
        "files", label="Soumissions", default=[], description="Fichiers XLSX ou PDF."
    )
    folders: list[Path] = ui_field("folders", label="Dossiers de soumissions", default=[])
    recursive: bool = ui_field("bool", label="Inclure les sous-dossiers", default=True)
    project: str = ui_field("text", label="Nom du projet", default="")
    output_folder: Path = ui_field("output_folder", label="Dossier de sortie")

    @model_validator(mode="after")
    def require_sources(self) -> "SoumissionInputs":
        if not self.files and not self.folders:
            raise ValueError("indiquez au moins une soumission ou un dossier")
        return self
