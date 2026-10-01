from engine.core.contract import ModuleManifest

MANIFEST = ModuleManifest(
    id="hello",
    name="Test de fonctionnement",
    description=(
        "Vérifie que l'application est correctement installée : "
        "écrit un petit fichier texte dans le dossier choisi."
    ),
    version="0.1.0",
)
