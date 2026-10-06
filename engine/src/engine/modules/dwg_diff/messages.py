from engine.core.i18n import define_messages

t = define_messages(
    fr={
        "manifest.name": "Comparaison d'indices",
        "manifest.description": (
            "Compare deux indices d'un jeu de plans : pièces ajoutées, supprimées, quantités "
            "modifiées."
        ),
        "manifest.instructions.add_plans": (
            "Ajoutez les plans de l'indice précédent (A) et ceux du nouvel indice (B)."
        ),
        "manifest.instructions.project": "Indiquez le nom du projet et le dossier de sortie.",
        "manifest.instructions.run": (
            "Cliquez sur « Lancer » : les deux listes de pièces sont établies avec la norme de la "
            "liste de pièces, puis comparées."
        ),
        "manifest.instructions.preview": (
            "L'aperçu montre les ajouts, suppressions et quantités modifiées ; « Exporter » écrit "
            "un fichier Excel avec un onglet par catégorie et un onglet « Plans »."
        ),
        "manifest.instructions.settings": (
            "Les colonnes qui identifient une pièce et le motif d'incrément des noms de plans se "
            "règlent dans Paramètres → Comparaison d'indices."
        ),
        "schema.before_files.label": "Plans de l'indice précédent (A)",
        "schema.files.description": "DWG ou DXF.",
        "schema.before_folders.label": "Dossiers de l'indice A",
        "schema.after_files.label": "Plans du nouvel indice (B)",
        "schema.after_folders.label": "Dossiers de l'indice B",
        "schema.recursive.label": "Inclure les sous-dossiers",
        "schema.project.label": "Nom du projet",
        "schema.output_folder.label": "Dossier de sortie",
        "schema.preview.label": "Aperçu avant export",
        "schema.preview.description": "Affiche la comparaison avant d'écrire le fichier Excel.",
        "schema.require_before": "indiquez les plans de l'indice précédent (A)",
        "schema.require_after": "indiquez les plans du nouvel indice (B)",
        "settings.key_columns.label": "Colonnes qui identifient une pièce",
        "settings.key_columns.description": (
            "Noms de colonnes de la liste de pièces, séparés par « ; ». Vide : toutes "
            "les colonnes sauf la quantité."
        ),
        "settings.increment_pattern.label": "Incrément dans les noms de plans",
        "settings.increment_pattern.description": (
            "Expression régulière retirée du nom des plans pour reconnaître le même plan "
            "d'un indice à l'autre (préfixe « 01_ » ou suffixe « _02 » par défaut)."
        ),
        "settings.invalid_pattern": "expression régulière invalide ({error})",
        "export.sheet.added": "Ajouts",
        "export.sheet.removed": "Suppressions",
        "export.sheet.changed": "Modifications",
        "export.sheet.unchanged": "Inchangés",
        "export.sheet.plans": "Plans",
        "export.plan_header": "Plan",
        "export.before_header": "Indice A",
        "export.after_header": "Indice B",
        "export.present": "oui",
        "export.absent": "non",
        "pipeline.parts_list_section": "Liste de pièces",
        "pipeline.side_label": "Indice {side}",
        "pipeline.no_file": "Aucun plan de l'indice {side} n'a pu être lu.",
        "pipeline.no_file_hint": "Consultez les avertissements.",
        "pipeline.preview_summary": "Aperçu : {summary}",
        "pipeline.writing": "Écriture de {name}",
        "service.status_header": "Statut",
        "service.quantity_before_header": "Quantité A",
        "service.quantity_after_header": "Quantité B",
        "service.delta_header": "Écart",
        "service.plans_before_header": "Plans A",
        "service.plans_after_header": "Plans B",
        "service.status.added": "Ajouté",
        "service.status.removed": "Supprimé",
        "service.status.changed": "Modifié",
        "service.status.unchanged": "Inchangé",
        "service.quantity_changed": "Quantité {before} → {after}",
        "service.summary": (
            "{added} ajout(s), {removed} suppression(s), "
            "{changed} modification(s), {unchanged} inchangée(s)"
        ),
    },
    en={
        "manifest.name": "Revision comparison",
        "manifest.description": (
            "Compares two revisions of a drawing set: parts added, removed, quantities changed."
        ),
        "manifest.instructions.add_plans": (
            "Add the drawings of the previous revision (A) and those of the new revision (B)."
        ),
        "manifest.instructions.project": "Enter the project name and the output folder.",
        "manifest.instructions.run": (
            "Click “Run”: both parts lists are built with the parts-list norm, then compared."
        ),
        "manifest.instructions.preview": (
            "The preview shows additions, removals and changed quantities; “Export” writes "
            "an Excel file with one sheet per category and a “Drawings” sheet."
        ),
        "manifest.instructions.settings": (
            "The columns that identify a part and the increment pattern of drawing names are "
            "set in Settings → Revision comparison."
        ),
        "schema.before_files.label": "Drawings of the previous revision (A)",
        "schema.files.description": "DWG or DXF.",
        "schema.before_folders.label": "Folders of revision A",
        "schema.after_files.label": "Drawings of the new revision (B)",
        "schema.after_folders.label": "Folders of revision B",
        "schema.recursive.label": "Include subfolders",
        "schema.project.label": "Project name",
        "schema.output_folder.label": "Output folder",
        "schema.preview.label": "Preview before export",
        "schema.preview.description": "Shows the comparison before writing the Excel file.",
        "schema.require_before": "add the drawings of the previous revision (A)",
        "schema.require_after": "add the drawings of the new revision (B)",
        "settings.key_columns.label": "Columns that identify a part",
        "settings.key_columns.description": (
            "Column names of the parts list, separated by “;”. Empty: every column "
            "except the quantity."
        ),
        "settings.increment_pattern.label": "Increment in drawing names",
        "settings.increment_pattern.description": (
            "Regular expression removed from drawing names to recognise the same drawing "
            "from one revision to the next (prefix “01_” or suffix “_02” by default)."
        ),
        "settings.invalid_pattern": "invalid regular expression ({error})",
        "export.sheet.added": "Added",
        "export.sheet.removed": "Removed",
        "export.sheet.changed": "Changed",
        "export.sheet.unchanged": "Unchanged",
        "export.sheet.plans": "Drawings",
        "export.plan_header": "Drawing",
        "export.before_header": "Revision A",
        "export.after_header": "Revision B",
        "export.present": "yes",
        "export.absent": "no",
        "pipeline.parts_list_section": "Parts list",
        "pipeline.side_label": "Revision {side}",
        "pipeline.no_file": "No drawing of revision {side} could be read.",
        "pipeline.no_file_hint": "Check the warnings.",
        "pipeline.preview_summary": "Preview: {summary}",
        "pipeline.writing": "Writing {name}",
        "service.status_header": "Status",
        "service.quantity_before_header": "Quantity A",
        "service.quantity_after_header": "Quantity B",
        "service.delta_header": "Difference",
        "service.plans_before_header": "Drawings A",
        "service.plans_after_header": "Drawings B",
        "service.status.added": "Added",
        "service.status.removed": "Removed",
        "service.status.changed": "Changed",
        "service.status.unchanged": "Unchanged",
        "service.quantity_changed": "Quantity {before} → {after}",
        "service.summary": (
            "{added} added, {removed} removed, {changed} changed, {unchanged} unchanged"
        ),
    },
)
