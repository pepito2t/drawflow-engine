from pathlib import Path

from pydantic import model_validator

from engine.core.contract import ModuleInputs
from engine.core.fields import ui_field


class PdfReportInputs(ModuleInputs):
    files: list[Path] = ui_field("files", label="Plans PDF", default=[])
    folders: list[Path] = ui_field("folders", label="Dossiers de plans", default=[])
    recursive: bool = ui_field("bool", label="Inclure les sous-dossiers", default=True)
    project: str = ui_field("text", label="Nom du projet", default="")
    template: Path | None = ui_field("template", label="Modèle Word", default=None)
    output_folder: Path = ui_field("output_folder", label="Dossier de sortie")

    @model_validator(mode="after")
    def require_plans(self) -> "PdfReportInputs":
        if not self.files and not self.folders:
            raise ValueError("indiquez au moins un plan PDF ou un dossier de plans")
        return self
