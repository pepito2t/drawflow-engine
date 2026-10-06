from engine.core.contract import ModuleManifest
from engine.modules.soumission.messages import t

TAB_ORDER = 30

MANIFEST = ModuleManifest(
    id="soumission",
    name=t("manifest.name"),
    description=t("manifest.description"),
    version="0.1.0",
    order=TAB_ORDER,
    icon="table",
    instructions=[
        t("manifest.instructions.sources"),
        t("manifest.instructions.folders"),
        t("manifest.instructions.duplicates"),
        t("manifest.instructions.run"),
        t("manifest.instructions.settings"),
    ],
)
