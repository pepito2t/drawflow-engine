from engine.core.i18n import define_messages

t = define_messages(
    fr={
        "manifest.name": "Soumission",
        "manifest.description": (
            "Rassemble les soumissions XLSX (ou PDF avec XLSX joint) en un tableau normalisé."
        ),
        "manifest.instructions.sources": (
            "Ajoutez des soumissions XLSX ou PDF, et/ou les dossiers qui les contiennent."
        ),
        "manifest.instructions.folders": "Plusieurs dossiers sont possibles.",
        "manifest.instructions.duplicates": (
            "Un même fichier présent deux fois n'est compté qu'une fois."
        ),
        "manifest.instructions.run": (
            "Indiquez le nom du projet et le dossier de sortie, puis cliquez sur « Lancer »."
        ),
        "manifest.instructions.settings": (
            "Les colonnes et les en-têtes reconnus se règlent dans Paramètres → Soumission."
        ),
        "schema.files.label": "Soumissions",
        "schema.files.description": "Fichiers XLSX ou PDF.",
        "schema.folders.label": "Dossiers de soumissions",
        "schema.recursive.label": "Inclure les sous-dossiers",
        "schema.project.label": "Nom du projet",
        "schema.output_folder.label": "Dossier de sortie",
        "schema.preview.label": "Aperçu avant export",
        "schema.preview.description": (
            "Affiche le tableau et ses anomalies avant d'écrire le fichier Excel."
        ),
        "schema.require_sources": "indiquez au moins une soumission ou un dossier",
        "settings.columns.label": "Colonnes normalisées",
        "settings.columns.key_label": "Colonne exportée",
        "settings.columns.value_label": "En-têtes reconnus (séparés par ;)",
        "settings.columns.description": (
            "L'en-tête du tableau est repéré grâce à ces libellés (sans accents ni casse)."
        ),
        "settings.numeric_columns.label": "Colonnes numériques",
        "settings.numeric_columns.description": (
            "Colonnes converties en nombres (formats 1'234.50 et 1 234,50 acceptés)."
        ),
        "settings.header_search_rows.label": "Lignes parcourues pour trouver l'en-tête",
        "settings.no_synonyms": "aucun en-tête reconnu pour « {column} »",
        "headers.section_title": "Soumission",
        "headers.file_not_found": "Fichier introuvable.",
        "headers.unsupported": (
            "Seuls les fichiers XLSX et PDF (avec classeur joint) peuvent être inspectés."
        ),
        "headers.unknown_column": "La colonne « {column} » n'existe pas.",
        "headers.unknown_column.hint": "Colonnes : {available}.",
        "headers.nothing_to_add": "Aucun en-tête nouveau à ajouter.",
        "reader.no_table": "Aucun tableau de soumission reconnu (en-têtes introuvables).",
        "reader.no_table.location": "en-têtes trouvés : {found}",
        "reader.no_table.hint": (
            "Ajoutez ces en-têtes aux colonnes dans Paramètres → Soumission, ou "
            "demandez à l'assistant de les associer."
        ),
        "reader.unreadable": "Le classeur Excel est illisible.",
        "reader.unreadable.hint": "Vérifiez qu'il s'ouvre dans Excel (format .xlsx).",
        "reader.sheet_unreadable": "La feuille « {sheet} » du classeur Excel est illisible.",
        "reader.unreadable_amounts": "{count} montant(s) illisible(s) gardé(s) en texte.",
        "reader.unreadable_amounts.location": "feuille « {sheet} »",
        "reader.unreadable_amounts.hint": (
            "Vérifiez les colonnes converties en nombres dans Paramètres → Soumission."
        ),
        "attachments.no_workbook": "Aucun classeur Excel joint à ce PDF.",
        "attachments.no_workbook.hint": (
            "Traitez le classeur Excel directement, ou demandez un PDF avec le classeur joint."
        ),
        "attachments.unreadable": "Le PDF est illisible ou endommagé.",
        "attachments.unreadable.hint": (
            "Ré-exportez la soumission en PDF depuis le logiciel d'origine."
        ),
        "attachments.protected": "Le PDF est protégé par un mot de passe.",
        "attachments.protected.hint": "Enregistrez une copie sans protection puis relancez.",
        "export.source_header": "Fichier source",
        "export.sheet_header": "Feuille",
        "preview.text_amount_issue": "Montant illisible : colonne « {column} »",
        "pipeline.source_kind": "XLSX ou PDF",
        "pipeline.read_label": "Lecture",
        "pipeline.no_table": "Aucun tableau de soumission n'a été reconnu.",
        "pipeline.no_table.hint": "Vérifiez les en-têtes reconnus dans Paramètres → Soumission.",
        "pipeline.preview_summary": "Aperçu : {rows} ligne(s) issues de {tables} tableau(x)",
        "pipeline.writing": "Écriture de {name}",
        "pipeline.summary": "{rows} ligne(s) issues de {tables} tableau(x), {files} fichier(s)",
        "pipeline.duplicate": "Doublon ignoré : même contenu que {name}.",
        "pipeline.no_source": "Aucune soumission n'a pu être lue.",
        "pipeline.no_source.hint": (
            "Les avertissements ci-dessus indiquent le problème de chaque fichier."
        ),
        "worker.unreadable_source": "Fichier introuvable ou illisible, ignoré.",
        "worker.unreadable_source.hint": "Réenregistrez le préréglage ou vérifiez le chemin.",
    },
    en={
        "manifest.name": "Submission",
        "manifest.description": (
            "Gathers XLSX submissions (or PDFs with an attached XLSX) into one normalized table."
        ),
        "manifest.instructions.sources": (
            "Add XLSX or PDF submissions, and/or the folders that contain them."
        ),
        "manifest.instructions.folders": "Several folders are allowed.",
        "manifest.instructions.duplicates": "A file present twice is only counted once.",
        "manifest.instructions.run": (
            "Enter the project name and the output folder, then click “Run”."
        ),
        "manifest.instructions.settings": (
            "Columns and recognized headers are set in Settings → Submission."
        ),
        "schema.files.label": "Submissions",
        "schema.files.description": "XLSX or PDF files.",
        "schema.folders.label": "Submission folders",
        "schema.recursive.label": "Include subfolders",
        "schema.project.label": "Project name",
        "schema.output_folder.label": "Output folder",
        "schema.preview.label": "Preview before export",
        "schema.preview.description": (
            "Shows the table and its anomalies before writing the Excel file."
        ),
        "schema.require_sources": "add at least one submission or a folder",
        "settings.columns.label": "Normalized columns",
        "settings.columns.key_label": "Exported column",
        "settings.columns.value_label": "Recognized headers (separated by ;)",
        "settings.columns.description": (
            "The table header is located using these labels (ignoring accents and case)."
        ),
        "settings.numeric_columns.label": "Numeric columns",
        "settings.numeric_columns.description": (
            "Columns converted to numbers (formats 1'234.50 and 1 234,50 accepted)."
        ),
        "settings.header_search_rows.label": "Rows scanned to find the header",
        "settings.no_synonyms": "no recognized header for “{column}”",
        "headers.section_title": "Submission",
        "headers.file_not_found": "File not found.",
        "headers.unsupported": (
            "Only XLSX and PDF files (with an attached workbook) can be inspected."
        ),
        "headers.unknown_column": "Column “{column}” does not exist.",
        "headers.unknown_column.hint": "Columns: {available}.",
        "headers.nothing_to_add": "No new header to add.",
        "reader.no_table": "No submission table recognized (headers not found).",
        "reader.no_table.location": "headers found: {found}",
        "reader.no_table.hint": (
            "Add these headers to the columns in Settings → Submission, or "
            "ask the assistant to map them."
        ),
        "reader.unreadable": "The Excel workbook cannot be read.",
        "reader.unreadable.hint": "Check that it opens in Excel (.xlsx format).",
        "reader.sheet_unreadable": "Sheet “{sheet}” of the Excel workbook cannot be read.",
        "reader.unreadable_amounts": "{count} unreadable amount(s) kept as text.",
        "reader.unreadable_amounts.location": "sheet “{sheet}”",
        "reader.unreadable_amounts.hint": (
            "Check the columns converted to numbers in Settings → Submission."
        ),
        "attachments.no_workbook": "No Excel workbook attached to this PDF.",
        "attachments.no_workbook.hint": (
            "Process the Excel workbook directly, or request a PDF with the workbook attached."
        ),
        "attachments.unreadable": "The PDF is unreadable or damaged.",
        "attachments.unreadable.hint": (
            "Export the submission to PDF again from the original software."
        ),
        "attachments.protected": "The PDF is password-protected.",
        "attachments.protected.hint": "Save an unprotected copy, then run again.",
        "export.source_header": "Source file",
        "export.sheet_header": "Sheet",
        "preview.text_amount_issue": "Unreadable amount: column “{column}”",
        "pipeline.source_kind": "XLSX or PDF",
        "pipeline.read_label": "Reading",
        "pipeline.no_table": "No submission table was recognized.",
        "pipeline.no_table.hint": "Check the recognized headers in Settings → Submission.",
        "pipeline.preview_summary": "Preview: {rows} row(s) from {tables} table(s)",
        "pipeline.writing": "Writing {name}",
        "pipeline.summary": "{rows} row(s) from {tables} table(s), {files} file(s)",
        "pipeline.duplicate": "Duplicate skipped: same content as {name}.",
        "pipeline.no_source": "No submission could be read.",
        "pipeline.no_source.hint": "The warnings above tell what is wrong with each file.",
        "worker.unreadable_source": "File not found or unreadable, skipped.",
        "worker.unreadable_source.hint": "Save the preset again or check the path.",
    },
)
