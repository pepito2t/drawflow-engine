from pathlib import Path


class EngineError(Exception):
    """Business error whose message must be understandable by a non-developer."""

    def __init__(self, message: str, *, file: Path | None = None, hint: str | None = None) -> None:
        super().__init__(message)
        self.message = message
        self.file = file
        self.hint = hint


class UnknownModuleError(EngineError):
    pass


class ModuleContractError(EngineError):
    pass


class InputFileError(EngineError):
    pass


class InvalidInputError(EngineError):
    pass


class OutputWriteError(EngineError):
    pass


class SettingsFileError(EngineError):
    pass


class InvalidSettingsError(EngineError):
    pass
