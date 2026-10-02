from engine.core.errors import EngineError

SETTINGS_HINT = "Vérifiez l'adresse et le modèle dans Paramètres → Assistant."


class AssistantError(EngineError):
    pass


class ModelUnavailableError(AssistantError):
    pass
