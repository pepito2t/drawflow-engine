from pathlib import Path

from pydantic import model_validator

from engine.core.contract import ModuleInputs
from engine.core.fields import ui_field
from engine.modules.dwg_parts.messages import t


class DwgPartsInputs(ModuleInputs):
    files: list[Path] = ui_field(
        "files",
        label=t("schema.files.label"),
        default=[],
        description=t("schema.files.description"),
    )
    folders: list[Path] = ui_field("folders", label=t("schema.folders.label"), default=[])
    recursive: bool = ui_field("bool", label=t("schema.recursive.label"), default=True)
    project: str = ui_field("text", label=t("schema.project.label"), default="")
    template: Path | None = ui_field("template", label=t("schema.template.label"), default=None)
    output_folder: Path = ui_field("output_folder", label=t("schema.output_folder.label"))
    multi_project: bool = ui_field(
        "bool",
        label=t("schema.multi_project.label"),
        default=False,
        description=t("schema.multi_project.description"),
    )
    preview: bool = ui_field(
        "bool",
        label=t("schema.preview.label"),
        default=True,
        description=t("schema.preview.description"),
    )

    @model_validator(mode="after")
    def require_plans(self) -> "DwgPartsInputs":
        if not self.files and not self.folders:
            raise ValueError(t("schema.require_plans"))
        return self
