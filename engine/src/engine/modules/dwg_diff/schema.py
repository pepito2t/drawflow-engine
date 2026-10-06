from pathlib import Path

from pydantic import model_validator

from engine.core.contract import ModuleInputs
from engine.core.fields import ui_field
from engine.modules.dwg_diff.messages import t


class DwgDiffInputs(ModuleInputs):
    before_files: list[Path] = ui_field(
        "files",
        label=t("schema.before_files.label"),
        default=[],
        description=t("schema.files.description"),
    )
    before_folders: list[Path] = ui_field(
        "folders", label=t("schema.before_folders.label"), default=[]
    )
    after_files: list[Path] = ui_field(
        "files",
        label=t("schema.after_files.label"),
        default=[],
        description=t("schema.files.description"),
    )
    after_folders: list[Path] = ui_field(
        "folders", label=t("schema.after_folders.label"), default=[]
    )
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
    def require_both_sides(self) -> "DwgDiffInputs":
        if not self.before_files and not self.before_folders:
            raise ValueError(t("schema.require_before"))
        if not self.after_files and not self.after_folders:
            raise ValueError(t("schema.require_after"))
        return self
