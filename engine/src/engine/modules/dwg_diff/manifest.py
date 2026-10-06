from engine.core.contract import ModuleManifest

TAB_ORDER = 15

MANIFEST = ModuleManifest(
    id="dwg-diff",
    name="Comparaison d'indices",
    description="Compare deux indices d'un jeu de plans : pièces ajoutées, supprimées, quantités "
    "modifiées.",
    version="0.1.0",
    order=TAB_ORDER,
    icon="diff",
    instructions=[
        "Ajoutez les plans de l'indice précédent (A) et ceux du nouvel indice (B).",
        "Indiquez le nom du projet et le dossier de sortie.",
        "Cliquez sur « Lancer » : les deux listes de pièces sont établies avec la norme de la "
        "liste de pièces, puis comparées.",
        "L'aperçu montre les ajouts, suppressions et quantités modifiées ; « Exporter » écrit "
        "un fichier Excel avec un onglet par catégorie et un onglet « Plans ».",
        "Les colonnes qui identifient une pièce et le motif d'incrément des noms de plans se "
        "règlent dans Paramètres → Comparaison d'indices.",
    ],
)
