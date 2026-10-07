from engine.core.i18n import define_messages

t = define_messages(
    fr={
        "general.language.label": "Langue / Language",
        "general.language.description": "fr : français · en : English.",
        "general.oda_converter_path.label": "ODA File Converter",
        "general.oda_converter_path.description": (
            "Chemin de ODAFileConverter.exe, nécessaire pour lire les fichiers DWG."
        ),
        "general.cache_folder.label": "Dossier de cache",
        "general.cache_folder.description": (
            "Laisser vide pour utiliser le dossier de cache de l'application."
        ),
        "general.batch_size.label": "Fichiers traités en parallèle",
        "general.notification_threshold_seconds.label": "Notifier après (secondes)",
        "general.notification_threshold_seconds.description": (
            "Une notification système signale la fin des traitements plus longs que cette durée, "
            "ou de tout traitement terminé pendant que l'application est en arrière-plan."
        ),
        "general.usage_counters.label": "Compteurs d'utilisation",
        "general.usage_counters.description": (
            "Compte les traitements et fichiers sur ce poste (Paramètres → À propos). "
            "Rien n'est envoyé."
        ),
        "general.minutes_saved_per_file.label": "Minutes gagnées par fichier",
        "general.minutes_saved_per_file.description": (
            "Estimation utilisée par les compteurs : temps manuel évité pour chaque fichier traité."
        ),
        "assistant.model_server_url.label": "Serveur du modèle",
        "assistant.model_server_url.description": (
            "Adresse de l'API compatible OpenAI du modèle local (Ollama, LM Studio, llama.cpp). "
            "Elle doit désigner ce poste : aucune donnée ne quitte la machine."
        ),
        "assistant.model_server_url.invalid": (
            "l'adresse doit commencer par http:// et désigner ce poste (localhost ou 127.0.0.1)"
        ),
        "assistant.model.label": "Modèle",
        "assistant.model.description": (
            "Nom du modèle installé, par exemple qwen3.5:9b pour Ollama."
        ),
        "mail.client_id.label": "Identifiant d'application (Entra ID)",
        "mail.client_id.description": (
            "Client ID de l'application inscrite dans Microsoft Entra ID pour lire la boîte "
            "Exchange / Microsoft 365. Vide : la fonctionnalité Courriels est désactivée."
        ),
        "mail.tenant.label": "Tenant",
        "mail.tenant.description": (
            "« common » pour tout compte professionnel, ou l'identifiant du tenant."
        ),
        "mail.local_folder.label": "Dossier des conversations",
        "mail.local_folder.description": (
            "Laisser vide pour conserver les conversations dans le dossier de l'application."
        ),
        "mail.lookback_days.label": "Récupérer les messages des derniers (jours)",
        "mail.max_conversations.label": "Conversations conservées au maximum",
        "mail.max_conversations.description": (
            "Au-delà, les conversations les plus anciennes sont retirées du dossier local."
        ),
        "settings.general_title": "Général",
        "settings.assistant_title": "Assistant",
        "settings.mail_title": "Courriel",
        "settings.fix_hint": "Ouvrez Paramètres pour corriger les valeurs indiquées.",
        "settings.reset_hint": (
            "Restaurez une sauvegarde ou supprimez ce fichier pour revenir aux valeurs par défaut."
        ),
        "settings.reserved_id": "L'identifiant « {module_id} » est réservé.",
        "settings.unreadable": "Le fichier de paramètres est illisible ; il n'a pas été modifié.",
        "settings.wrong_format": "Le fichier de paramètres n'a pas le bon format.",
        "settings.section_invalid": "Paramètres « {title} » invalides : {details}",
        "settings.section_errors": "{title} : {details}",
        "settings.invalid": "Paramètres invalides — {errors}",
        "settings.save_failed": "Impossible d'enregistrer les paramètres.",
        "settings.save_failed_hint": (
            "Vérifiez que le dossier de configuration est accessible en écriture."
        ),
        "settings.export_failed": "Impossible d'exporter les paramètres.",
        "settings.not_an_export": "Ce fichier n'est pas un export de paramètres Drawflow.",
        "settings.unknown_section": (
            "La catégorie de paramètres « {section_id} » n'existe pas dans cette version."
        ),
        "presets.unreadable": "Le fichier des préréglages est illisible ; il n'a pas été modifié.",
        "presets.unreadable_hint": "Supprimez-le pour repartir d'une liste vide.",
        "presets.duplicate": "Un préréglage « {name} » existe déjà.",
        "presets.save_failed": "Impossible d'enregistrer les préréglages.",
        "presets.incomplete": "Préréglage « {name} » incomplet : {details}",
        "presets.incomplete_hint": "Complétez le formulaire avant de l'enregistrer.",
        "templates.unsupported": "Seuls les modèles Excel (.xlsx) et Word (.docx) sont acceptés.",
        "templates.unreadable": "Le modèle est illisible.",
        "templates.unreadable_hint": "Vérifiez qu'il s'ouvre normalement.",
        "templates.import_failed": "Impossible d'importer le modèle.",
        "templates.remove_failed": "Impossible de supprimer le modèle.",
        "templates.wrong_kind": (
            "« {template_id} » n'est pas un modèle {kind} adapté à « {module_name} »."
        ),
        "templates.invalid_id": "Identifiant de modèle invalide.",
        "templates.missing": "Le modèle « {template_id} » n'existe plus.",
        "templates.default_save_failed": "Impossible d'enregistrer le modèle par défaut.",
        "history.unreadable": "Le fichier d'historique est illisible ; il n'a pas été modifié.",
        "history.unreadable_hint": "Supprimez-le pour repartir d'un historique vide.",
        "history.save_failed": "Impossible d'enregistrer l'historique.",
        "history.missing_id": "Identifiant de traitement manquant.",
        "history.unknown_action": "Action d'historique inconnue : {action}.",
        "stats.unreadable": "Le fichier des compteurs est illisible ; il n'a pas été modifié.",
        "stats.unreadable_hint": "Supprimez-le pour repartir de zéro.",
        "stats.save_failed": "Impossible d'enregistrer les compteurs.",
        "naming.variable.projet": "nom du projet",
        "naming.variable.type": "type de document",
        "naming.variable.date": "date (AAAAMMJJ)",
        "naming.variable.heure": "heure (HHMM)",
        "naming.variable.source": "nom du fichier source",
        "naming.variable.indice": "indice",
        "naming.empty_template": "le modèle de nom ne peut pas être vide",
        "naming.unbalanced_braces": "accolades mal fermées dans le modèle de nom",
        "naming.forbidden_characters": (
            'caractères interdits dans un nom de fichier : < > : " / \\ | ? *'
        ),
        "naming.unknown_variable": (
            "variable inconnue {{{variable}}} ; variables possibles : {allowed}"
        ),
        "naming.format_option": "la variable {{{variable}}} ne prend pas d'option de format",
        "naming.file_name_template.label": "Nom des fichiers exportés",
        "naming.file_name_template.description": "Variables disponibles — {variables}.",
        "naming.variable_item": "{{{name}}} : {label}",
        "naming.output_folder_unreachable": "Le dossier de sortie est inaccessible.",
        "naming.output_folder_unreachable_hint": (
            "Choisissez un autre dossier de sortie, ou vérifiez vos droits dessus."
        ),
        "cache.invalid_entry": "Entrée de cache invalide, nouveau calcul.",
        "cache.folder_unreachable": "Le dossier de cache est inaccessible.",
        "cache.folder_unreachable_hint": "Choisissez un autre dossier de cache dans Paramètres.",
        "batch.unexpected_item_error": "Fichier non traité : erreur inattendue.",
        "batch.unexpected_item_hint": "Consultez les journaux (Paramètres → Installation).",
        "batch.progress": "{label} : {name}",
        "collect.ignored": "Fichier ignoré : ce n'est pas un {kind}.",
        "collect.none_found": "Aucun fichier {kind} trouvé.",
        "collect.none_found_hint": (
            "Vérifiez les fichiers et dossiers choisis (et l'option sous-dossiers)."
        ),
        "collect.count": "{count} fichier(s) à traiter.",
        "collect.folder_missing": "Dossier introuvable.",
        "collect.missing": "Fichier introuvable : il a été déplacé ou supprimé.",
        "collect.missing_hint": "Réenregistrez le préréglage ou vérifiez le chemin.",
        "guide.unavailable": "Le guide utilisateur est introuvable.",
        "guide.unavailable_hint": "Réinstallez Drawflow.",
        "guide.section_missing": "Section « {topic} » absente du guide.",
        "guide.section_missing_hint": "Sections : {available}.",
        "validation.form_label": "formulaire",
        "runner.input_missing": "Le fichier de paramètres est introuvable.",
        "runner.input_unreadable": "Le fichier de paramètres est illisible.",
        "runner.input_unreadable_hint": "Relancez la fonctionnalité depuis l'application.",
        "runner.input_not_object": "Le fichier de paramètres doit contenir un objet JSON.",
        "runner.default_template": "Modèle par défaut : {name}",
        "runner.invalid_fields": "Champs invalides : {details}",
        "runner.invalid_fields_hint": "Corrigez les champs indiqués puis relancez.",
        "profile.export_failed": "Impossible d'exporter le profil.",
        "profile.apply_failed": "Impossible d'appliquer le profil.",
        "profile.not_a_profile": "Ce fichier n'est pas un profil Drawflow.",
        "profile.newer_version": (
            "Ce profil vient de Drawflow {version}, plus récent que cette version."
        ),
        "profile.newer_version_hint": "Mettez Drawflow à jour, puis réimportez le profil.",
        "profile.template_too_large": "Le modèle « {name} » du profil est trop volumineux.",
        "profile.template_unreadable": "Le modèle « {name} » du profil est illisible.",
        "profile.template_unreadable_hint": (
            "Vérifiez le modèle sur le poste d'origine (il doit s'ouvrir dans Excel ou Word), "
            "puis réexportez le profil."
        ),
        "profile.member_unreadable": "Le profil est incomplet ou illisible ({member}).",
        "profile.corrupt": "Le fichier de profil est endommagé ; rien n'a été modifié.",
        "profile.corrupt_hint": "Réexportez le profil depuis le poste d'origine.",
        "profile.no_settings": "Le profil ne contient aucun paramètre.",
        "profile.section_invalid": "Paramètres « {title} » invalides dans le profil.",
        "profile.presets_unreadable": "Les préréglages du profil sont illisibles.",
        "profile.presets_invalid": "Les préréglages du profil sont invalides.",
        "registry.duplicate_id": "Deux modules utilisent l'identifiant « {module_id} ».",
        "registry.none": "aucun",
        "registry.unknown": "La fonctionnalité « {module_id} » n'existe pas.",
        "registry.unknown_hint": "Fonctionnalités disponibles : {available}.",
        "registry.invalid_attribute": (
            "Le module « {package} » n'expose pas d'attribut {attribute} valide."
        ),
        "xlsx.sheet_missing": "La feuille « {sheet} » n'existe pas dans le modèle.",
        "xlsx.sheet_missing_hint": (
            "Feuilles disponibles : {available}. Corrigez le nom dans Paramètres."
        ),
        "xlsx.save_failed": "Impossible d'enregistrer le classeur.",
        "xlsx.save_failed_hint": (
            "Fermez le fichier s'il est ouvert dans Excel et vérifiez le dossier de sortie."
        ),
        "xlsx.template_unreadable": "Le modèle Excel est illisible.",
        "xlsx.template_unreadable_hint": "Choisissez un fichier .xlsx valide (pas .xls ni .xlsm).",
        "xlsx.no_sheet": "Le modèle Excel ne contient pas de feuille de calcul.",
    },
    en={
        "general.language.label": "Langue / Language",
        "general.language.description": "fr : français · en : English.",
        "general.oda_converter_path.label": "ODA File Converter",
        "general.oda_converter_path.description": (
            "Path to ODAFileConverter.exe, required to read DWG files."
        ),
        "general.cache_folder.label": "Cache folder",
        "general.cache_folder.description": "Leave empty to use the application's cache folder.",
        "general.batch_size.label": "Files processed in parallel",
        "general.notification_threshold_seconds.label": "Notify after (seconds)",
        "general.notification_threshold_seconds.description": (
            "A system notification reports the end of any run longer than this, "
            "or of any run that finishes while the application is in the background."
        ),
        "general.usage_counters.label": "Usage counters",
        "general.usage_counters.description": (
            "Counts runs and files on this computer (Settings → About). Nothing is sent."
        ),
        "general.minutes_saved_per_file.label": "Minutes saved per file",
        "general.minutes_saved_per_file.description": (
            "Estimate used by the counters: manual time avoided for each file processed."
        ),
        "assistant.model_server_url.label": "Model server",
        "assistant.model_server_url.description": (
            "Address of the local model's OpenAI-compatible API (Ollama, LM Studio, llama.cpp). "
            "It must point to this computer: no data leaves the machine."
        ),
        "assistant.model_server_url.invalid": (
            "the address must start with http:// and point to this computer "
            "(localhost or 127.0.0.1)"
        ),
        "assistant.model.label": "Model",
        "assistant.model.description": (
            "Name of the installed model, for example qwen3.5:9b for Ollama."
        ),
        "mail.client_id.label": "Application ID (Entra ID)",
        "mail.client_id.description": (
            "Client ID of the application registered in Microsoft Entra ID to read the "
            "Exchange / Microsoft 365 mailbox. Empty: the Mail feature is disabled."
        ),
        "mail.tenant.label": "Tenant",
        "mail.tenant.description": '"common" for any work account, or the tenant\'s identifier.',
        "mail.local_folder.label": "Conversations folder",
        "mail.local_folder.description": (
            "Leave empty to keep conversations in the application's folder."
        ),
        "mail.lookback_days.label": "Fetch messages from the last (days)",
        "mail.max_conversations.label": "Maximum conversations kept",
        "mail.max_conversations.description": (
            "Beyond this, the oldest conversations are removed from the local folder."
        ),
        "settings.general_title": "General",
        "settings.assistant_title": "Assistant",
        "settings.mail_title": "Mail",
        "settings.fix_hint": "Open Settings to correct the values listed.",
        "settings.reset_hint": "Restore a backup or delete this file to go back to the defaults.",
        "settings.reserved_id": 'The identifier "{module_id}" is reserved.',
        "settings.unreadable": "The settings file is unreadable; it was left untouched.",
        "settings.wrong_format": "The settings file does not have the expected format.",
        "settings.section_invalid": 'Invalid "{title}" settings: {details}',
        "settings.section_errors": "{title}: {details}",
        "settings.invalid": "Invalid settings — {errors}",
        "settings.save_failed": "The settings could not be saved.",
        "settings.save_failed_hint": "Check that the configuration folder is writable.",
        "settings.export_failed": "The settings could not be exported.",
        "settings.not_an_export": "This file is not a Drawflow settings export.",
        "settings.unknown_section": (
            'The settings category "{section_id}" does not exist in this version.'
        ),
        "presets.unreadable": "The presets file is unreadable; it was left untouched.",
        "presets.unreadable_hint": "Delete it to start from an empty list.",
        "presets.duplicate": 'A preset named "{name}" already exists.',
        "presets.save_failed": "The presets could not be saved.",
        "presets.incomplete": 'Preset "{name}" is incomplete: {details}',
        "presets.incomplete_hint": "Complete the form before saving it.",
        "templates.unsupported": "Only Excel (.xlsx) and Word (.docx) templates are accepted.",
        "templates.unreadable": "The template is unreadable.",
        "templates.unreadable_hint": "Check that it opens normally.",
        "templates.import_failed": "The template could not be imported.",
        "templates.remove_failed": "The template could not be deleted.",
        "templates.wrong_kind": (
            '"{template_id}" is not a {kind} template suitable for "{module_name}".'
        ),
        "templates.invalid_id": "Invalid template identifier.",
        "templates.missing": 'The template "{template_id}" no longer exists.',
        "templates.default_save_failed": "The default template could not be saved.",
        "history.unreadable": "The history file is unreadable; it was left untouched.",
        "history.unreadable_hint": "Delete it to start from an empty history.",
        "history.save_failed": "The history could not be saved.",
        "history.missing_id": "Run identifier missing.",
        "history.unknown_action": "Unknown history action: {action}.",
        "stats.unreadable": "The counters file is unreadable; it was left untouched.",
        "stats.unreadable_hint": "Delete it to start from zero.",
        "stats.save_failed": "The counters could not be saved.",
        "naming.variable.projet": "project name",
        "naming.variable.type": "document type",
        "naming.variable.date": "date (YYYYMMDD)",
        "naming.variable.heure": "time (HHMM)",
        "naming.variable.source": "source file name",
        "naming.variable.indice": "revision",
        "naming.empty_template": "the file name template cannot be empty",
        "naming.unbalanced_braces": "unbalanced braces in the file name template",
        "naming.forbidden_characters": (
            'characters not allowed in a file name: < > : " / \\ | ? *'
        ),
        "naming.unknown_variable": "unknown variable {{{variable}}}; available: {allowed}",
        "naming.format_option": "the variable {{{variable}}} does not take a format option",
        "naming.file_name_template.label": "Exported file names",
        "naming.file_name_template.description": "Available variables — {variables}.",
        "naming.variable_item": "{{{name}}}: {label}",
        "naming.output_folder_unreachable": "The output folder cannot be accessed.",
        "naming.output_folder_unreachable_hint": (
            "Choose another output folder, or check your permissions on it."
        ),
        "cache.invalid_entry": "Invalid cache entry, computing again.",
        "cache.folder_unreachable": "The cache folder cannot be accessed.",
        "cache.folder_unreachable_hint": "Choose another cache folder in Settings.",
        "batch.unexpected_item_error": "File not processed: unexpected error.",
        "batch.unexpected_item_hint": "See the logs (Settings → Setup).",
        "batch.progress": "{label}: {name}",
        "collect.ignored": "File ignored: it is not a {kind}.",
        "collect.none_found": "No {kind} file found.",
        "collect.none_found_hint": (
            "Check the selected files and folders (and the subfolders option)."
        ),
        "collect.count": "{count} file(s) to process.",
        "collect.folder_missing": "Folder not found.",
        "collect.missing": "File not found: it was moved or deleted.",
        "collect.missing_hint": "Save the preset again or check the path.",
        "guide.unavailable": "The user guide cannot be found.",
        "guide.unavailable_hint": "Reinstall Drawflow.",
        "guide.section_missing": 'Section "{topic}" is not in the guide.',
        "guide.section_missing_hint": "Sections: {available}.",
        "validation.form_label": "form",
        "runner.input_missing": "The parameters file cannot be found.",
        "runner.input_unreadable": "The parameters file is unreadable.",
        "runner.input_unreadable_hint": "Start the feature again from the application.",
        "runner.input_not_object": "The parameters file must contain a JSON object.",
        "runner.default_template": "Default template: {name}",
        "runner.invalid_fields": "Invalid fields: {details}",
        "runner.invalid_fields_hint": "Correct the fields listed, then run again.",
        "profile.export_failed": "The profile could not be exported.",
        "profile.apply_failed": "The profile could not be applied.",
        "profile.not_a_profile": "This file is not a Drawflow profile.",
        "profile.newer_version": (
            "This profile comes from Drawflow {version}, which is newer than this version."
        ),
        "profile.newer_version_hint": "Update Drawflow, then import the profile again.",
        "profile.template_too_large": 'The template "{name}" in the profile is too large.',
        "profile.template_unreadable": 'The template "{name}" in the profile is unreadable.',
        "profile.template_unreadable_hint": (
            "Check the template on the original computer (it must open in Excel or Word), "
            "then export the profile again."
        ),
        "profile.member_unreadable": "The profile is incomplete or unreadable ({member}).",
        "profile.corrupt": "The profile file is damaged; nothing was changed.",
        "profile.corrupt_hint": "Export the profile again from the original computer.",
        "profile.no_settings": "The profile contains no settings.",
        "profile.section_invalid": 'Invalid "{title}" settings in the profile.',
        "profile.presets_unreadable": "The profile's presets are unreadable.",
        "profile.presets_invalid": "The profile's presets are invalid.",
        "registry.duplicate_id": 'Two modules use the identifier "{module_id}".',
        "registry.none": "none",
        "registry.unknown": 'The feature "{module_id}" does not exist.',
        "registry.unknown_hint": "Available features: {available}.",
        "registry.invalid_attribute": (
            'The module "{package}" does not expose a valid {attribute} attribute.'
        ),
        "xlsx.sheet_missing": 'The sheet "{sheet}" does not exist in the template.',
        "xlsx.sheet_missing_hint": "Available sheets: {available}. Correct the name in Settings.",
        "xlsx.save_failed": "The workbook could not be saved.",
        "xlsx.save_failed_hint": (
            "Close the file if it is open in Excel and check the output folder."
        ),
        "xlsx.template_unreadable": "The Excel template is unreadable.",
        "xlsx.template_unreadable_hint": "Choose a valid .xlsx file (not .xls or .xlsm).",
        "xlsx.no_sheet": "The Excel template contains no worksheet.",
    },
)
