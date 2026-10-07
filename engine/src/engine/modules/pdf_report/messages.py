from engine.core.i18n import define_messages

t = define_messages(
    fr={
        "manifest.name": "Rapport",
        "manifest.description": (
            "Relève le cartouche et les références des plans PDF et génère un rapport Word."
        ),
        "manifest.instructions.sources": (
            "Ajoutez des plans PDF et/ou des dossiers de plans (Parcourir ou glisser-déposer)."
        ),
        "manifest.instructions.project": (
            "Indiquez le nom du projet et, si besoin, un modèle Word à balises."
        ),
        "manifest.instructions.run": "Choisissez le dossier de sortie puis cliquez sur « Lancer ».",
        "manifest.instructions.settings": (
            "Zone du cartouche, champs relevés et nom du fichier se règlent dans "
            "Paramètres → Rapport."
        ),
        "manifest.instructions.tags": (
            "Balises du modèle : {project}, {date}, boucle {loop} avec {file}, {references} "
            "et chaque champ (ex. {example})."
        ),
        "schema.files.label": "Plans PDF",
        "schema.folders.label": "Dossiers de plans",
        "schema.recursive.label": "Inclure les sous-dossiers",
        "schema.project.label": "Nom du projet",
        "schema.template.label": "Modèle Word",
        "schema.output_folder.label": "Dossier de sortie",
        "schema.require_plans": "indiquez au moins un plan PDF ou un dossier de plans",
        "settings.title_block_left.label": "Cartouche : bord gauche (% de la largeur)",
        "settings.title_block_top.label": "Cartouche : bord haut (% de la hauteur)",
        "settings.title_block_right.label": "Cartouche : bord droit (% de la largeur)",
        "settings.title_block_bottom.label": "Cartouche : bord bas (% de la hauteur)",
        "settings.fields.label": "Champs du cartouche",
        "settings.fields.key_label": "Balise Word",
        "settings.fields.value_label": "Libellé dans le cartouche",
        "settings.fields.description": (
            "La valeur est le texte qui suit le libellé (ou la ligne suivante). "
            "Préfixe « re: » pour une expression régulière avec un groupe, "
            "ex. re:Ind\\.?\\s*(\\w+)."
        ),
        "settings.reference_pattern.label": "Format des références",
        "settings.reference_pattern.description": (
            "Expression régulière des références relevées sur tout le plan."
        ),
        "settings.invalid_tag": (
            "balise « {tag} » invalide : minuscules, chiffres et _ uniquement"
        ),
        "settings.references_owner": "références",
        "settings.invalid_regex": "expression régulière invalide pour « {owner} » : {error}",
        "settings.title_block_no_width": (
            "zone du cartouche vide : le bord gauche ({left} %) doit être inférieur "
            "au bord droit ({right} %)"
        ),
        "settings.title_block_no_height": (
            "zone du cartouche vide : le bord haut ({top} %) doit être inférieur "
            "au bord bas ({bottom} %)"
        ),
        "reader.inaccessible": "Le PDF est inaccessible.",
        "reader.protected": "Le PDF est protégé par un mot de passe.",
        "reader.protected.hint": "Enregistrez une copie sans protection puis relancez.",
        "reader.unreadable": "Le PDF est illisible ou endommagé.",
        "reader.unreadable.hint": "Ré-exportez le plan en PDF depuis le logiciel d'origine.",
        "docx.fix_template_hint": (
            "Corrigez la balise dans le modèle Word ou ajoutez-la dans Paramètres → Rapport."
        ),
        "docx.default.title": "Rapport de plans",
        "docx.default.summary": "Projet : {project} — Date : {date} — {count} plan(s)",
        "docx.default.plan_heading": "{file} ({pages} page(s))",
        "docx.default.field": "{label} : {value}",
        "docx.default.references": "Références : {references}",
        "docx.unknown_tag": "Balise inconnue dans le modèle Word : {detail}.",
        "docx.malformed_tag": "Le modèle Word contient une balise mal écrite : {detail}.",
        "docx.malformed_tag.hint": "Vérifiez les accolades {{ }} et {% %} du modèle.",
        "docx.unreadable": "Le modèle Word est illisible.",
        "docx.unreadable.hint": "Choisissez un fichier .docx valide.",
        "docx.save_failed": "Impossible d'enregistrer le rapport.",
        "docx.save_failed.hint": (
            "Fermez le fichier s'il est ouvert dans Word et vérifiez le dossier de sortie."
        ),
        "pipeline.read_label": "Lecture",
        "pipeline.nothing_read": "Aucun PDF n'a pu être lu.",
        "pipeline.nothing_read.hint": "Consultez les avertissements du journal.",
        "pipeline.writing": "Écriture de {name}",
        "pipeline.summary": "Rapport de {count} plan(s) ({read}/{total} lu(s))",
        "worker.no_text": "Aucun texte trouvé : le PDF est peut-être une image scannée.",
        "worker.no_text.hint": (
            "Exportez le PDF depuis le logiciel de dessin (texte sélectionnable) plutôt qu'un scan."
        ),
        "worker.missing_fields": "Champs introuvables : {fields}.",
        "worker.missing_fields.location": "cartouche",
        "worker.missing_fields.hint": (
            "Vérifiez la zone du cartouche et les libellés cherchés dans Paramètres → Rapport."
        ),
    },
    en={
        "manifest.name": "PDF report",
        "manifest.description": (
            "Reads the title block and references of PDF drawings and generates a Word report."
        ),
        "manifest.instructions.sources": (
            "Add PDF drawings and/or drawing folders (Browse or drag and drop)."
        ),
        "manifest.instructions.project": (
            "Enter the project name and, if needed, a Word template with tags."
        ),
        "manifest.instructions.run": "Choose the output folder, then click “Run”.",
        "manifest.instructions.settings": (
            "The title block area, extracted fields and file name are set in Settings → PDF report."
        ),
        "manifest.instructions.tags": (
            "Template tags: {project}, {date}, loop {loop} with {file}, {references} "
            "and each field (e.g. {example})."
        ),
        "schema.files.label": "PDF drawings",
        "schema.folders.label": "Drawing folders",
        "schema.recursive.label": "Include subfolders",
        "schema.project.label": "Project name",
        "schema.template.label": "Word template",
        "schema.output_folder.label": "Output folder",
        "schema.require_plans": "add at least one PDF drawing or a drawing folder",
        "settings.title_block_left.label": "Title block: left edge (% of width)",
        "settings.title_block_top.label": "Title block: top edge (% of height)",
        "settings.title_block_right.label": "Title block: right edge (% of width)",
        "settings.title_block_bottom.label": "Title block: bottom edge (% of height)",
        "settings.fields.label": "Title block fields",
        "settings.fields.key_label": "Word tag",
        "settings.fields.value_label": "Label in the title block",
        "settings.fields.description": (
            "The value is the text that follows the label (or the next line). "
            "Prefix “re:” for a regular expression with a group, "
            "e.g. re:Ind\\.?\\s*(\\w+)."
        ),
        "settings.reference_pattern.label": "Reference format",
        "settings.reference_pattern.description": (
            "Regular expression of the references collected across the whole drawing."
        ),
        "settings.invalid_tag": "invalid tag “{tag}”: lowercase letters, digits and _ only",
        "settings.references_owner": "references",
        "settings.invalid_regex": "invalid regular expression for “{owner}”: {error}",
        "settings.title_block_no_width": (
            "empty title block area: the left edge ({left} %) must be less than "
            "the right edge ({right} %)"
        ),
        "settings.title_block_no_height": (
            "empty title block area: the top edge ({top} %) must be less than "
            "the bottom edge ({bottom} %)"
        ),
        "reader.inaccessible": "The PDF cannot be opened.",
        "reader.protected": "The PDF is password-protected.",
        "reader.protected.hint": "Save an unprotected copy, then run again.",
        "reader.unreadable": "The PDF is unreadable or damaged.",
        "reader.unreadable.hint": "Export the drawing to PDF again from the original software.",
        "docx.fix_template_hint": (
            "Fix the tag in the Word template or add it in Settings → PDF report."
        ),
        "docx.default.title": "Drawing report",
        "docx.default.summary": "Project: {project} — Date: {date} — {count} drawing(s)",
        "docx.default.plan_heading": "{file} ({pages} page(s))",
        "docx.default.field": "{label}: {value}",
        "docx.default.references": "References: {references}",
        "docx.unknown_tag": "Unknown tag in the Word template: {detail}.",
        "docx.malformed_tag": "The Word template contains a malformed tag: {detail}.",
        "docx.malformed_tag.hint": "Check the braces {{ }} and {% %} in the template.",
        "docx.unreadable": "The Word template cannot be read.",
        "docx.unreadable.hint": "Choose a valid .docx file.",
        "docx.save_failed": "The report could not be saved.",
        "docx.save_failed.hint": (
            "Close the file if it is open in Word and check the output folder."
        ),
        "pipeline.read_label": "Reading",
        "pipeline.nothing_read": "No PDF could be read.",
        "pipeline.nothing_read.hint": "See the warnings in the log.",
        "pipeline.writing": "Writing {name}",
        "pipeline.summary": "Report of {count} drawing(s) ({read}/{total} read)",
        "worker.no_text": "No text found: the PDF may be a scanned image.",
        "worker.no_text.hint": (
            "Export the PDF from the drawing software (selectable text) rather than a scan."
        ),
        "worker.missing_fields": "Fields not found: {fields}.",
        "worker.missing_fields.location": "title block",
        "worker.missing_fields.hint": (
            "Check the title block area and the labels searched for in Settings → PDF report."
        ),
    },
)
