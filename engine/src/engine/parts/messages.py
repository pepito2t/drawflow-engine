from engine.core.i18n import define_messages

t = define_messages(
    fr={
        "collect.plan_kind": "plan DWG/DXF",
        "listing.no_part": (
            "Aucun bloc ne correspond aux blocs retenus (Paramètres → Liste de pièces)."
        ),
        "listing.no_part_hint": "Vérifiez les blocs retenus (jokers * et ?) et les plans choisis.",
        "mapping.block_column": "Bloc",
        "mapping.missing_attribute": (
            "Attribut « {tag} » absent sur {blocks} (cellule laissée vide)."
        ),
        "mapping.missing_attribute_hint": (
            "Ajoutez l'attribut {tag} aux blocs dans AutoCAD, ou changez la colonne dans "
            "Paramètres → Liste de pièces."
        ),
        "mapping.invalid_quantity": (
            "Quantité « {tag} » illisible sur {count} bloc(s) : compté(s) 1."
        ),
        "mapping.invalid_quantity_hint": "Saisissez un nombre dans l'attribut {tag} de ces blocs.",
        "mapping.blocks.one": "{count} bloc",
        "mapping.blocks.many": "{count} blocs",
        "oda.configure_hint": (
            "Installez ODA File Converter puis indiquez le chemin de ODAFileConverter.exe "
            "dans Paramètres → Général."
        ),
        "oda.not_configured": "ODA File Converter n'est pas configuré.",
        "oda.not_found": "ODA File Converter est introuvable à l'emplacement indiqué.",
        "oda.not_converted": (
            "Le plan n'a pas pu être converti "
            "(fichier DWG corrompu ou version non prise en charge)."
        ),
        "oda.not_converted_hint": "Ouvrez-le dans AutoCAD, faites un AUDIT puis réenregistrez-le.",
        "oda.timeout": "La conversion du plan a pris trop de temps.",
        "oda.timeout_hint": "Vérifiez que le fichier n'est pas exceptionnellement lourd.",
        "oda.failed": "ODA File Converter a échoué sur ce plan.",
        "reader.nesting_truncated": (
            "Blocs imbriqués au-delà de {depth} niveaux : leur contenu n'est pas compté."
        ),
        "reader.nesting_location": "blocs {names}",
        "reader.nesting_hint": (
            "Simplifiez l'imbrication dans AutoCAD, ou vérifiez qu'aucune pièce ne se "
            "trouve à ce niveau."
        ),
        "reader.unreadable": "Le plan est illisible.",
        "reader.unreadable_hint": "Vérifiez qu'il s'ouvre dans AutoCAD, puis réenregistrez-le.",
        "settings.column.reference": "Référence",
        "settings.column.designation": "Désignation",
        "settings.column.length": "Longueur",
        "settings.column.material": "Matière",
        "settings.column.finish": "Finition",
        "settings.file_name_stem": "liste-pieces",
        "settings.included_blocks.label": "Blocs retenus",
        "settings.included_blocks.description": (
            "Noms de blocs séparés par « ; », jokers * et ? acceptés (ex. PANNEAU*;EQUERRE). "
            "* = tous les blocs."
        ),
        "settings.columns.label": "Colonnes de la liste",
        "settings.columns.key_label": "Colonne",
        "settings.columns.value_label": "Attribut du bloc",
        "settings.columns.description": (
            "Chaque colonne du fichier exporté reprend la valeur d'un attribut AutoCAD."
        ),
        "settings.quantity_attribute.label": "Attribut de quantité",
        "settings.quantity_attribute.description": (
            "Laisser vide ou absent du bloc : chaque bloc compte pour 1."
        ),
        "settings.include_block_name.label": "Ajouter une colonne « Bloc »",
        "settings.group_identical.label": "Regrouper les pièces identiques",
        "settings.group_identical.description": (
            "Les pièces dont toutes les colonnes sont égales forment une seule ligne."
        ),
        "settings.template_sheet.label": "Feuille du modèle Excel",
        "settings.template_sheet.description": (
            "Laisser vide pour utiliser la feuille active du modèle."
        ),
        "settings.header_row.label": "Ligne d'en-tête",
        "settings.header_row.description": "Les pièces sont écrites à partir de la ligne suivante.",
    },
    en={
        "collect.plan_kind": "DWG/DXF drawing",
        "listing.no_part": "No block matches the selected blocks (Settings → Parts list).",
        "listing.no_part_hint": (
            "Check the selected blocks (wildcards * and ?) and the chosen drawings."
        ),
        "mapping.block_column": "Block",
        "mapping.missing_attribute": 'Attribute "{tag}" missing on {blocks} (cell left empty).',
        "mapping.missing_attribute_hint": (
            "Add the {tag} attribute to the blocks in AutoCAD, or change the column in "
            "Settings → Parts list."
        ),
        "mapping.invalid_quantity": (
            'Quantity "{tag}" unreadable on {count} block(s): counted as 1.'
        ),
        "mapping.invalid_quantity_hint": "Enter a number in the {tag} attribute of these blocks.",
        "mapping.blocks.one": "{count} block",
        "mapping.blocks.many": "{count} blocks",
        "oda.configure_hint": (
            "Install ODA File Converter, then enter the path to ODAFileConverter.exe "
            "in Settings → General."
        ),
        "oda.not_configured": "ODA File Converter is not configured.",
        "oda.not_found": "ODA File Converter cannot be found at the given location.",
        "oda.not_converted": (
            "The drawing could not be converted (corrupted DWG file or unsupported version)."
        ),
        "oda.not_converted_hint": "Open it in AutoCAD, run AUDIT, then save it again.",
        "oda.timeout": "Converting the drawing took too long.",
        "oda.timeout_hint": "Check that the file is not unusually large.",
        "oda.failed": "ODA File Converter failed on this drawing.",
        "reader.nesting_truncated": (
            "Blocks nested deeper than {depth} levels: their contents are not counted."
        ),
        "reader.nesting_location": "blocks {names}",
        "reader.nesting_hint": (
            "Simplify the nesting in AutoCAD, or check that no part sits at that level."
        ),
        "reader.unreadable": "The drawing is unreadable.",
        "reader.unreadable_hint": "Check that it opens in AutoCAD, then save it again.",
        "settings.column.reference": "Reference",
        "settings.column.designation": "Description",
        "settings.column.length": "Length",
        "settings.column.material": "Material",
        "settings.column.finish": "Finish",
        "settings.file_name_stem": "parts-list",
        "settings.included_blocks.label": "Selected blocks",
        "settings.included_blocks.description": (
            'Block names separated by ";", wildcards * and ? accepted (e.g. PANEL*;BRACKET). '
            "* = every block."
        ),
        "settings.columns.label": "List columns",
        "settings.columns.key_label": "Column",
        "settings.columns.value_label": "Block attribute",
        "settings.columns.description": (
            "Each column of the exported file takes the value of an AutoCAD attribute."
        ),
        "settings.quantity_attribute.label": "Quantity attribute",
        "settings.quantity_attribute.description": (
            "Leave empty or missing from the block: each block counts as 1."
        ),
        "settings.include_block_name.label": 'Add a "Block" column',
        "settings.group_identical.label": "Group identical parts",
        "settings.group_identical.description": (
            "Parts whose columns are all equal form a single line."
        ),
        "settings.template_sheet.label": "Excel template sheet",
        "settings.template_sheet.description": ("Leave empty to use the template's active sheet."),
        "settings.header_row.label": "Header row",
        "settings.header_row.description": "Parts are written from the next row down.",
    },
)
