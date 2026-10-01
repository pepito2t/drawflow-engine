from engine.core.contract import ModuleManifest

# Diagnostic module: always listed after the business features.
DIAGNOSTIC_TAB_ORDER = 1000

MANIFEST = ModuleManifest(
    id="hello",
    name="Test de fonctionnement",
    description=(
        "Vérifie que l'application est correctement installée : "
        "écrit un petit fichier texte dans le dossier choisi."
    ),
    version="0.1.0",
    order=DIAGNOSTIC_TAB_ORDER,
    instructions=[
        "Saisissez un nom.",
        "Choisissez un dossier de sortie avec « Parcourir » ou par glisser-déposer.",
        "Cliquez sur « Lancer » : un fichier texte est créé dans ce dossier.",
        "Le nom du fichier suit la norme définie dans Paramètres.",
    ],
)
