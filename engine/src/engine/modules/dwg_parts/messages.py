from engine.core.i18n import define_messages

t = define_messages(
    fr={
        "manifest.name": "Liste de pièces",
        "manifest.description": (
            "Extrait les blocs des plans DWG/DXF et produit la liste des pièces en Excel."
        ),
        "manifest.instructions.add_plans": (
            "Ajoutez des plans DWG/DXF et/ou des dossiers de plans (Parcourir ou glisser-déposer)."
        ),
        "manifest.instructions.project": (
            "Indiquez le nom du projet : il sert à nommer le fichier exporté."
        ),
        "manifest.instructions.template": (
            "Choisissez éventuellement un modèle Excel, puis le dossier de sortie."
        ),
        "manifest.instructions.run": (
            "Cliquez sur « Lancer » : les plans sont lus en parallèle et la liste est créée."
        ),
        "manifest.instructions.settings": (
            "Blocs retenus, colonnes et nom du fichier se règlent dans Paramètres → "
            "Liste de pièces."
        ),
        "schema.files.label": "Plans",
        "schema.files.description": "Fichiers DWG ou DXF.",
        "schema.folders.label": "Dossiers de plans",
        "schema.recursive.label": "Inclure les sous-dossiers",
        "schema.project.label": "Nom du projet",
        "schema.template.label": "Modèle Excel",
        "schema.output_folder.label": "Dossier de sortie",
        "schema.multi_project.label": "Un projet par dossier",
        "schema.multi_project.description": (
            "Chaque dossier de plans devient un projet : colonne « Projet » dans la "
            "liste et onglet « Total » toutes origines confondues."
        ),
        "schema.preview.label": "Aperçu avant export",
        "schema.preview.description": (
            "Affiche la liste et ses anomalies avant d'écrire le fichier Excel."
        ),
        "schema.require_plans": "indiquez au moins un plan ou un dossier de plans",
        "export.quantity_header": "Quantité",
        "export.sources_header": "Plans",
        "export.total_sheet": "Total",
        "pipeline.read_label": "Lecture",
        "pipeline.no_file": "Aucun plan n'a pu être lu.",
        "pipeline.no_file_hint": "Consultez les avertissements du journal.",
        "pipeline.preview_summary": "Aperçu : {summary}",
        "pipeline.writing": "Écriture de {name}",
        "service.project_header": "Projet",
        "service.files_project": "Fichiers",
        "service.quantity_header": "Quantité",
        "service.sources_header": "Plans",
        "service.empty_cell": "Colonne « {column} » vide",
        "service.summary": "{lines} ligne(s), {pieces} pièce(s), {read}/{total} plan(s) lu(s)",
    },
    en={
        "manifest.name": "Parts list",
        "manifest.description": (
            "Extracts the blocks of DWG/DXF drawings and produces the parts list in Excel."
        ),
        "manifest.instructions.add_plans": (
            "Add DWG/DXF drawings and/or drawing folders (Browse or drag and drop)."
        ),
        "manifest.instructions.project": "Enter the project name: it names the exported file.",
        "manifest.instructions.template": (
            "Optionally choose an Excel template, then the output folder."
        ),
        "manifest.instructions.run": (
            "Click “Run”: the drawings are read in parallel and the list is created."
        ),
        "manifest.instructions.settings": (
            "Selected blocks, columns and file name are set in Settings → Parts list."
        ),
        "schema.files.label": "Drawings",
        "schema.files.description": "DWG or DXF files.",
        "schema.folders.label": "Drawing folders",
        "schema.recursive.label": "Include subfolders",
        "schema.project.label": "Project name",
        "schema.template.label": "Excel template",
        "schema.output_folder.label": "Output folder",
        "schema.multi_project.label": "One project per folder",
        "schema.multi_project.description": (
            "Each drawing folder becomes a project: a “Project” column in the list "
            "and a “Total” sheet across all origins."
        ),
        "schema.preview.label": "Preview before export",
        "schema.preview.description": (
            "Shows the list and its anomalies before writing the Excel file."
        ),
        "schema.require_plans": "add at least one drawing or drawing folder",
        "export.quantity_header": "Quantity",
        "export.sources_header": "Drawings",
        "export.total_sheet": "Total",
        "pipeline.read_label": "Reading",
        "pipeline.no_file": "No drawing could be read.",
        "pipeline.no_file_hint": "Check the warnings in the log.",
        "pipeline.preview_summary": "Preview: {summary}",
        "pipeline.writing": "Writing {name}",
        "service.project_header": "Project",
        "service.files_project": "Files",
        "service.quantity_header": "Quantity",
        "service.sources_header": "Drawings",
        "service.empty_cell": "Column “{column}” empty",
        "service.summary": "{lines} line(s), {pieces} part(s), {read}/{total} drawing(s) read",
    },
)
