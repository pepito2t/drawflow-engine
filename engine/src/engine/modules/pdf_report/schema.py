from pathlib import Path

from pydantic import model_validator

from engine.core.contract import ModuleInputs
from engine.core.fields import ui_field
from engine.modules.pdf_report.messages import t


class PdfReportInputs(ModuleInputs):
    files: list[Path] = ui_field("files", label=t("schema.files.label"), default=[])
    folders: list[Path] = ui_field("folders", label=t("schema.folders.label"), default=[])
    recursive: bool = ui_field("bool", label=t("schema.recursive.label"), default=True)
    project: str = ui_field("text", label=t("schema.project.label"), default="")
    template: Path | None = ui_field("template", label=t("schema.template.label"), default=None)
    output_folder: Path = ui_field("output_folder", label=t("schema.output_folder.label"))

    @model_validator(mode="after")
    def require_plans(self) -> "PdfReportInputs":
        if not self.files and not self.folders:
            raise ValueError(t("schema.require_plans"))
        return self
