"""File-based requests (templates, settings import/export) sent by the desktop bridge."""

from pathlib import Path
from typing import Any

from pydantic import BaseModel, ConfigDict, Field, ValidationError

from engine.core.errors import InvalidInputError
from engine.core.presets import PresetStore
from engine.core.profile import export_profile, import_profile, read_profile
from engine.core.registry import discover_modules, get_module
from engine.core.settings import export_section, read_section_import
from engine.core.templates import TemplateLibrary, TemplateUser
from engine.modules.soumission.headers import add_synonyms

TEMPLATE_ACTIONS = {
    "list": "Liste les modèles importés et les modèles par défaut (JSON).",
    "import": "Importe un modèle .xlsx ou .docx.",
    "remove": "Supprime un modèle importé.",
    "set-default": "Définit le modèle par défaut d'une fonctionnalité.",
}
PROFILE_ACTIONS = {
    "export": "Exporte le profil complet (paramètres, préréglages, modèles) en zip.",
    "read-import": "Décrit un profil sans l'appliquer (JSON).",
    "import": "Applique un profil : paramètres, préréglages et modèles sont remplacés.",
}
MAIL_ACTIONS = {
    "status": "État de la boîte mail connectée et du dossier local (JSON).",
    "connect-start": "Démarre la connexion Microsoft : code à saisir sur la page indiquée (JSON).",
    "connect-finish": "Attend la fin de la connexion Microsoft et enregistre la session (JSON).",
    "disconnect": "Oublie la session Microsoft ; les conversations locales restent.",
    "fetch": "Récupère les nouveaux messages et les range par conversation (JSON).",
    "list": "Liste les conversations conservées (JSON).",
    "read": "Messages d'une conversation (JSON).",
    "export": "Copie une conversation lisible dans un dossier.",
    "remove": "Retire une conversation du dossier local, jamais de la boîte mail.",
}
PRESET_ACTIONS = {
    "list": "Liste les préréglages (JSON).",
    "save": "Crée ou met à jour un préréglage.",
    "remove": "Supprime un préréglage.",
}
SETTINGS_FILE_ACTIONS = {
    "add-synonyms": "Ajoute des en-têtes reconnus aux colonnes de la soumission (JSON).",
    "export": "Exporte une catégorie de paramètres en JSON.",
    "read-import": "Valide un export de paramètres sans l'enregistrer.",
}


class _Request(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")


class SourceRequest(_Request):
    source: Path


class SynonymsRequest(_Request):
    columns: dict[str, list[str]]


class TemplateIdRequest(_Request):
    id: str


class DefaultTemplateRequest(_Request):
    module: str
    template: str | None


class SavePresetRequest(_Request):
    id: str | None = None
    name: str
    module: str
    inputs: dict[str, Any]


class ExportRequest(_Request):
    section: str
    target: Path


def handle_templates(action: str, settings: Path, raw: dict[str, Any]) -> dict[str, Any]:
    library = TemplateLibrary(settings)
    users = template_users()
    if action == "import":
        library.import_file(_parse(SourceRequest, raw).source)
    elif action == "remove":
        library.remove(_parse(TemplateIdRequest, raw).id)
    elif action == "set-default":
        request = _parse(DefaultTemplateRequest, raw)
        user = next((user for user in users if user.id == request.module), None)
        if user is None:
            raise InvalidInputError(f"« {request.module} » n'utilise pas de modèle.")
        library.set_default(user, request.template)
    return library.describe(users)


def handle_presets(action: str, settings: Path, raw: dict[str, Any]) -> dict[str, Any]:
    store = PresetStore(settings)
    if action == "save":
        request = _parse(SavePresetRequest, raw)
        store.save(get_module(request.module), request.name, request.inputs, request.id)
    elif action == "remove":
        store.remove(_parse(TemplateIdRequest, raw).id)
    return {"presets": [preset.model_dump(mode="json") for preset in store.presets()]}


def handle_settings_file(action: str, settings: Path, raw: dict[str, Any]) -> dict[str, Any]:
    modules = discover_modules()
    if action == "add-synonyms":
        return add_synonyms(settings, _parse(SynonymsRequest, raw).columns)
    if action == "export":
        request = _parse(ExportRequest, raw)
        export_section(settings, request.section, modules, request.target)
        return {"exported": str(request.target)}
    return read_section_import(_parse(SourceRequest, raw).source, modules)


def handle_profile(
    action: str, settings: Path, raw: dict[str, Any], app_version: str | None
) -> dict[str, Any]:
    modules = discover_modules()
    if action == "export":
        target = _parse(ExportRequest, raw).target
        return export_profile(settings, target, modules, app_version)
    source = _parse(SourceRequest, raw).source
    if action == "read-import":
        return read_profile(source, settings, modules, app_version)
    return import_profile(source, settings, modules, app_version)


class ConversationRequest(_Request):
    id: str = Field(min_length=1)


class ConversationExportRequest(ConversationRequest):
    target: Path


def handle_mail(action: str, settings: Path, raw: dict[str, Any]) -> dict[str, Any]:
    from engine.mail import service

    if action == "status":
        return service.status(settings)
    if action == "connect-start":
        return service.connect_start(settings)
    if action == "connect-finish":
        return service.connect_finish(settings, raw)
    if action == "disconnect":
        return service.disconnect(settings)
    if action == "fetch":
        return service.fetch(settings)
    if action == "list":
        return service.list_conversations(settings)
    if action == "read":
        return service.read_conversation(settings, _parse(ConversationRequest, raw).id)
    if action == "export":
        request = _parse(ConversationExportRequest, raw)
        return service.export_conversation(settings, request.id, request.target)
    return service.remove_conversation(settings, _parse(ConversationRequest, raw).id)


def template_users() -> list[TemplateUser]:
    return [
        TemplateUser(module.manifest.id, module.manifest.name, module.manifest.template_kind)
        for module in discover_modules().values()
        if module.manifest.template_kind is not None
    ]


def _parse[RequestT: _Request](model: type[RequestT], raw: dict[str, Any]) -> RequestT:
    try:
        return model.model_validate(raw)
    except ValidationError as error:
        raise InvalidInputError("Requête invalide.", hint=str(error)) from error
