import json
import shutil
import zipfile
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from engine.core.contract import TemplateKind
from engine.core.errors import EngineError, OutputWriteError
from engine.core.naming import unique_output_path

TEMPLATES_FOLDER = "templates"
DEFAULTS_FILE = "defaults.json"
SUFFIX_KINDS: dict[str, TemplateKind] = {".xlsx": "xlsx", ".docx": "docx"}


class TemplateError(EngineError):
    pass


@dataclass(frozen=True)
class TemplateInfo:
    id: str
    kind: TemplateKind


@dataclass(frozen=True)
class TemplateUser:
    """A feature that accepts an output template."""

    id: str
    name: str
    kind: TemplateKind


class TemplateLibrary:
    """Output templates copied into the app's configuration folder."""

    def __init__(self, settings_file: Path) -> None:
        self.folder = settings_file.parent / TEMPLATES_FOLDER

    def templates(self) -> list[TemplateInfo]:
        if not self.folder.is_dir():
            return []
        found = [
            TemplateInfo(path.name, SUFFIX_KINDS[path.suffix.lower()])
            for path in self.folder.iterdir()
            if path.is_file() and path.suffix.lower() in SUFFIX_KINDS
        ]
        return sorted(found, key=lambda template: template.id.casefold())

    def import_file(self, source: Path) -> TemplateInfo:
        kind = SUFFIX_KINDS.get(source.suffix.lower())
        if kind is None:
            raise TemplateError(
                "Seuls les modèles Excel (.xlsx) et Word (.docx) sont acceptés.", file=source
            )
        if not zipfile.is_zipfile(source):
            raise TemplateError(
                "Le modèle est illisible.", file=source, hint="Vérifiez qu'il s'ouvre normalement."
            )
        target = unique_output_path(self.folder, source.name)
        try:
            self.folder.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(source, target)
        except OSError as error:
            raise OutputWriteError("Impossible d'importer le modèle.", file=source) from error
        return TemplateInfo(target.name, kind)

    def remove(self, template_id: str) -> None:
        path = self._path(template_id)
        try:
            path.unlink()
        except OSError as error:
            raise TemplateError("Impossible de supprimer le modèle.", file=path) from error
        defaults = {
            module: chosen for module, chosen in self.defaults().items() if chosen != template_id
        }
        self._write_defaults(defaults)

    def defaults(self) -> dict[str, str]:
        path = self.folder / DEFAULTS_FILE
        if not path.is_file():
            return {}
        try:
            content = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            return {}
        return (
            {str(key): str(value) for key, value in content.items()}
            if isinstance(content, dict)
            else {}
        )

    def set_default(self, user: TemplateUser, template_id: str | None) -> None:
        defaults = self.defaults()
        if template_id is None:
            defaults.pop(user.id, None)
        else:
            path = self._path(template_id)
            if SUFFIX_KINDS.get(path.suffix.lower()) != user.kind:
                raise TemplateError(
                    f"« {template_id} » n'est pas un modèle {user.kind.upper()} "
                    f"adapté à « {user.name} »."
                )
            defaults[user.id] = template_id
        self._write_defaults(defaults)

    def default_for(self, module_id: str) -> Path | None:
        chosen = self.defaults().get(module_id)
        if chosen is None:
            return None
        path = self.folder / chosen
        return path if path.is_file() else None

    def describe(self, users: list[TemplateUser]) -> dict[str, Any]:
        defaults = self.defaults()
        return {
            "templates": [
                {"id": template.id, "kind": template.kind} for template in self.templates()
            ],
            "modules": [
                {
                    "id": user.id,
                    "name": user.name,
                    "kind": user.kind,
                    "default": defaults.get(user.id),
                }
                for user in users
            ],
        }

    def _path(self, template_id: str) -> Path:
        if Path(template_id).name != template_id:
            raise TemplateError("Identifiant de modèle invalide.")
        path = self.folder / template_id
        if not path.is_file():
            raise TemplateError(f"Le modèle « {template_id} » n'existe plus.")
        return path

    def _write_defaults(self, defaults: dict[str, str]) -> None:
        try:
            self.folder.mkdir(parents=True, exist_ok=True)
            (self.folder / DEFAULTS_FILE).write_text(
                json.dumps(defaults, ensure_ascii=False), encoding="utf-8"
            )
        except OSError as error:
            raise OutputWriteError(
                "Impossible d'enregistrer le modèle par défaut.", file=self.folder
            ) from error
