from engine.core.contract import ModuleManifest

TAB_ORDER = 10

MANIFEST = ModuleManifest(
    id="dwg-parts",
    name="Liste de pièces",
    description="Extrait les blocs des plans DWG/DXF et produit la liste des pièces en Excel.",
    version="0.1.0",
    order=TAB_ORDER,
    icon="list",
    template_kind="xlsx",
    instructions=[
        "Ajoutez des plans DWG/DXF et/ou des dossiers de plans (Parcourir ou glisser-déposer).",
        "Indiquez le nom du projet : il sert à nommer le fichier exporté.",
        "Choisissez éventuellement un modèle Excel, puis le dossier de sortie.",
        "Cliquez sur « Lancer » : les plans sont lus en parallèle et la liste est créée.",
        "Blocs retenus, colonnes et nom du fichier se règlent dans Paramètres → Liste de pièces.",
    ],
)
