from pathlib import Path

from pydantic import model_validator

from engine.core.contract import ModuleInputs
from engine.core.fields import ui_field


class DwgDiffInputs(ModuleInputs):
    before_files: list[Path] = ui_field(
        "files", label="Plans de l'indice précédent (A)", default=[], description="DWG ou DXF."
    )
    before_folders: list[Path] = ui_field("folders", label="Dossiers de l'indice A", default=[])
    after_files: list[Path] = ui_field(
        "files", label="Plans du nouvel indice (B)", default=[], description="DWG ou DXF."
    )
    after_folders: list[Path] = ui_field("folders", label="Dossiers de l'indice B", default=[])
    recursive: bool = ui_field("bool", label="Inclure les sous-dossiers", default=True)
    project: str = ui_field("text", label="Nom du projet", default="")
    output_folder: Path = ui_field("output_folder", label="Dossier de sortie")
    preview: bool = ui_field(
        "bool",
        label="Aperçu avant export",
        default=True,
        description="Affiche la comparaison avant d'écrire le fichier Excel.",
    )

    @model_validator(mode="after")
    def require_both_sides(self) -> "DwgDiffInputs":
        if not self.before_files and not self.before_folders:
            raise ValueError("indiquez les plans de l'indice précédent (A)")
        if not self.after_files and not self.after_folders:
            raise ValueError("indiquez les plans du nouvel indice (B)")
        return self
