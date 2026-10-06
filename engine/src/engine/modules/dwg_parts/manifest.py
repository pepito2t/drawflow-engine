from engine.core.contract import ModuleManifest
from engine.modules.dwg_parts.messages import t

TAB_ORDER = 10

MANIFEST = ModuleManifest(
    id="dwg-parts",
    name=t("manifest.name"),
    description=t("manifest.description"),
    version="0.1.0",
    order=TAB_ORDER,
    icon="list",
    template_kind="xlsx",
    instructions=[
        t("manifest.instructions.add_plans"),
        t("manifest.instructions.project"),
        t("manifest.instructions.template"),
        t("manifest.instructions.run"),
        t("manifest.instructions.settings"),
    ],
)
