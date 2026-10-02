from engine.core.contract import ModuleManifest

TAB_ORDER = 20

MANIFEST = ModuleManifest(
    id="pdf-report",
    name="Rapport",
    description="Relève le cartouche et les références des plans PDF et génère un rapport Word.",
    version="0.1.0",
    order=TAB_ORDER,
    icon="report",
    template_kind="docx",
    instructions=[
        "Ajoutez des plans PDF et/ou des dossiers de plans (Parcourir ou glisser-déposer).",
        "Indiquez le nom du projet et, si besoin, un modèle Word à balises.",
        "Choisissez le dossier de sortie puis cliquez sur « Lancer ».",
        "Zone du cartouche, champs relevés et nom du fichier se règlent dans Paramètres → Rapport.",
        "Balises du modèle : {{ projet }}, {{ date }}, boucle {%p for plan in plans %} "
        "avec {{ plan.fichier }}, {{ plan.references }} et chaque champ (ex. {{ plan.indice }}).",
    ],
)
