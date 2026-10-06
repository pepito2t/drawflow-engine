from pathlib import Path

from pydantic import model_validator

from engine.core.contract import ModuleInputs
from engine.core.fields import ui_field


class DwgPartsInputs(ModuleInputs):
    files: list[Path] = ui_field(
        "files", label="Plans", default=[], description="Fichiers DWG ou DXF."
    )
    folders: list[Path] = ui_field("folders", label="Dossiers de plans", default=[])
    recursive: bool = ui_field("bool", label="Inclure les sous-dossiers", default=True)
    project: str = ui_field("text", label="Nom du projet", default="")
    template: Path | None = ui_field("template", label="Modèle Excel", default=None)
    output_folder: Path = ui_field("output_folder", label="Dossier de sortie")
    preview: bool = ui_field(
        "bool",
        label="Aperçu avant export",
        default=True,
        description="Affiche la liste et ses anomalies avant d'écrire le fichier Excel.",
    )

    @model_validator(mode="after")
    def require_plans(self) -> "DwgPartsInputs":
        if not self.files and not self.folders:
            raise ValueError("indiquez au moins un plan ou un dossier de plans")
        return self
