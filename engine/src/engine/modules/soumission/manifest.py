from engine.core.contract import ModuleManifest

TAB_ORDER = 30

MANIFEST = ModuleManifest(
    id="soumission",
    name="Soumission",
    description="Rassemble les soumissions XLSX (ou PDF avec XLSX joint) en un tableau normalisé.",
    version="0.1.0",
    order=TAB_ORDER,
    instructions=[
        "Ajoutez des soumissions XLSX ou PDF, et/ou les dossiers qui les contiennent.",
        "Plusieurs dossiers sont possibles.",
        "Un même fichier présent deux fois n'est compté qu'une fois.",
        "Indiquez le nom du projet et le dossier de sortie, puis cliquez sur « Lancer ».",
        "Les colonnes et les en-têtes reconnus se règlent dans Paramètres → Soumission.",
    ],
)
