from engine.core.fields import ui_field
from engine.core.settings_models import ModuleSettings

PERCENT_MAX = 100


def _zone_field(label: str, default: float) -> float:
    value: float = ui_field("number", label=label, default=default, ge=0, le=PERCENT_MAX)
    return value


class PdfReportSettings(ModuleSettings):
    title_block_left: float = _zone_field("Cartouche : bord gauche (% de la largeur)", 55)
    title_block_top: float = _zone_field("Cartouche : bord haut (% de la hauteur)", 70)
    title_block_right: float = _zone_field("Cartouche : bord droit (% de la largeur)", 100)
    title_block_bottom: float = _zone_field("Cartouche : bord bas (% de la hauteur)", 100)
