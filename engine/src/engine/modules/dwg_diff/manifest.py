from engine.core.contract import ModuleManifest
from engine.modules.dwg_diff.messages import t

TAB_ORDER = 15

MANIFEST = ModuleManifest(
    id="dwg-diff",
    name=t("manifest.name"),
    description=t("manifest.description"),
    version="0.1.0",
    order=TAB_ORDER,
    icon="diff",
    instructions=[
        t("manifest.instructions.add_plans"),
        t("manifest.instructions.project"),
        t("manifest.instructions.run"),
        t("manifest.instructions.preview"),
        t("manifest.instructions.settings"),
    ],
)
