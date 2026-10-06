"""The parts-list norm lives in the shared `engine.parts` library; this module registers it."""

from engine.parts.settings import (
    DEFAULT_COLUMNS,
    DEFAULT_FILE_NAME_TEMPLATE,
    PartsListSettings,
)

DwgPartsSettings = PartsListSettings

__all__ = ["DEFAULT_COLUMNS", "DEFAULT_FILE_NAME_TEMPLATE", "DwgPartsSettings"]
