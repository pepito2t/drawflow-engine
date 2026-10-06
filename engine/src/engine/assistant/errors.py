from engine.assistant.messages import t
from engine.core.errors import EngineError

SETTINGS_HINT = t("errors.settings_hint")


class AssistantError(EngineError):
    pass


class ModelUnavailableError(AssistantError):
    pass
