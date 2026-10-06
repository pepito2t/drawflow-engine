from engine.core.contract import ModuleManifest
from engine.modules.pdf_report.messages import t

TAB_ORDER = 20
PROJECT_TAG = "{{ projet }}"
DATE_TAG = "{{ date }}"
PLANS_LOOP_TAG = "{%p for plan in plans %}"
FILE_TAG = "{{ plan.fichier }}"
REFERENCES_TAG = "{{ plan.references }}"
EXAMPLE_FIELD_TAG = "{{ plan.indice }}"

MANIFEST = ModuleManifest(
    id="pdf-report",
    name=t("manifest.name"),
    description=t("manifest.description"),
    version="0.1.0",
    order=TAB_ORDER,
    icon="report",
    template_kind="docx",
    instructions=[
        t("manifest.instructions.sources"),
        t("manifest.instructions.project"),
        t("manifest.instructions.run"),
        t("manifest.instructions.settings"),
        t(
            "manifest.instructions.tags",
            project=PROJECT_TAG,
            date=DATE_TAG,
            loop=PLANS_LOOP_TAG,
            file=FILE_TAG,
            references=REFERENCES_TAG,
            example=EXAMPLE_FIELD_TAG,
        ),
    ],
)
