from pathlib import Path

from pydantic import model_validator

from engine.core.contract import ModuleInputs
from engine.core.fields import ui_field
from engine.modules.soumission.messages import t


class SoumissionInputs(ModuleInputs):
    files: list[Path] = ui_field(
        "files",
        label=t("schema.files.label"),
        default=[],
        description=t("schema.files.description"),
    )
    folders: list[Path] = ui_field("folders", label=t("schema.folders.label"), default=[])
    recursive: bool = ui_field("bool", label=t("schema.recursive.label"), default=True)
    project: str = ui_field("text", label=t("schema.project.label"), default="")
    output_folder: Path = ui_field("output_folder", label=t("schema.output_folder.label"))
    preview: bool = ui_field(
        "bool",
        label=t("schema.preview.label"),
        default=True,
        description=t("schema.preview.description"),
    )

    @model_validator(mode="after")
    def require_sources(self) -> "SoumissionInputs":
        if not self.files and not self.folders:
            raise ValueError(t("schema.require_sources"))
        return self
