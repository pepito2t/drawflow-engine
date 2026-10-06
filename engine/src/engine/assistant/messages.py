"""User-facing texts of the assistant, in both languages."""

from engine.core.i18n import define_messages

t = define_messages(
    fr={
        "agent.system_prompt": (
            "Tu es l'assistant de Drawflow, une application qui automatise le travail d'un "
            "dessinateur en façade : listes de pièces depuis des plans DWG, rapports DOCX depuis "
            "des PDF et soumissions. Réponds en français, de façon brève et concrète. Utilise les "
            "outils pour consulter les fonctionnalités, les préréglages et les modèles au lieu de "
            "supposer. Pour expliquer comment installer, configurer ou dépanner, lis directement "
            "la rubrique du guide concernée avec read_help et suis sa marche à suivre sans "
            "inventer de bouton ni de menu. Pour répondre à « qu'est-ce qui m'attend ? » ou parler "
            "des derniers traitements, lis read_today. Quand le message contient des fichiers "
            "joints (chemins), lis-les avec inspect_file puis propose l'action adaptée (DWG → "
            "liste de pièces, PDF → rapport, XLSX → soumission). Pour expliquer un résultat (pièce "
            "ou champ manquant, fichier ignoré), lis le traitement concerné avec list_runs puis "
            "read_run et cite le fichier et l'endroit de l'avertissement. Pour lancer un "
            "traitement, propose-le avec propose_preset ou propose_feature : l'utilisateur voit "
            "une carte et décide. Quand une soumission n'est pas reconnue, "
            "inspect_submission_headers puis propose_column_synonyms pour associer ses en-têtes "
            "aux colonnes. Ne dis jamais qu'un traitement est lancé ; dis qu'il attend sa "
            "confirmation. N'invente aucun chemin de fichier : demande-le s'il manque. "
            "Réponds en français."
        ),
        "agent.help_topics_heading": "Rubriques du guide (identifiant : titre) : ",
        "agent.proposal_shown": (
            "Proposition affichée à l'utilisateur : le traitement démarrera seulement s'il clique "
            "sur Lancer. Rien n'est lancé pour l'instant."
        ),
        "agent.invalid_arguments": "Arguments JSON invalides : corrige l'appel.",
        "agent.too_many_tool_rounds": (
            "L'assistant a dépassé {rounds} séries d'appels d'outils pour cette question."
        ),
        "agent.too_many_tool_rounds.hint": "Reformulez la demande de façon plus précise.",
        "catalog.qwen35_27b": "Le plus capable, pour les postes très équipés.",
        "catalog.qwen35_9b": "Le meilleur équilibre pour un poste récent.",
        "catalog.qwen3_8b": "Génération précédente, très éprouvée.",
        "catalog.llama31_8b": "Alternative de Meta, moins bonne en français.",
        "catalog.qwen35_4b": "Pour les postes avec peu de mémoire.",
        "catalog.qwen35_2b": "Très léger, réponses plus simples.",
        "conversation.last_message_not_user": "le dernier message doit venir de l'utilisateur",
        "errors.settings_hint": "Vérifiez l'adresse et le modèle dans Paramètres → Assistant.",
        "history.previous_unreadable": "Conversation précédente illisible.",
        "history.invalid": "Conversation invalide.",
        "history.save_failed": "Impossible d'enregistrer la conversation.",
        "inspect.file_not_found": "Fichier introuvable.",
        "inspect.file_not_found.hint": "Donne le chemin complet.",
        "inspect.file_too_large": "Fichier trop volumineux pour être inspecté.",
        "inspect.unsupported_type": "Type de fichier non pris en charge.",
        "inspect.unsupported_type.hint": "Drawflow lit les DWG, DXF, PDF, XLSX et DOCX.",
        "mcp_server.instructions": (
            "Drawflow automatise le travail d'un dessinateur en façade : listes de pièces depuis "
            "des plans DWG, rapports DOCX depuis des PDF et soumissions. Ces outils décrivent les "
            "fonctionnalités, les préréglages et les modèles disponibles, et proposent des "
            "lancements que l'utilisateur confirme."
        ),
        "mcp_server.list_features": (
            "Liste les fonctionnalités de Drawflow, leur mode d'emploi et leurs entrées."
        ),
        "mcp_server.list_presets": (
            "Liste les préréglages enregistrés (jeux de paramètres prêts à lancer)."
        ),
        "mcp_server.list_templates": (
            "Liste les modèles de sortie importés et le modèle par défaut de chaque fonctionnalité."
        ),
        "mcp_server.read_today": (
            "Ce qui attend l'utilisateur aujourd'hui : derniers traitements (résultat, fichiers "
            "produits, avertissements) et préréglages lançables en un clic."
        ),
        "mcp_server.inspect_file": (
            "Inspecte un fichier donné par l'utilisateur (chemin complet) : plan DWG/DXF (blocs "
            "et attributs), PDF (pages, texte de la première page), XLSX (feuilles, premières "
            "lignes) ou DOCX (premiers paragraphes), et la fonctionnalité conseillée."
        ),
        "mcp_server.list_runs": (
            "Liste les derniers traitements (identifiant, fonctionnalité, résultat, fichiers "
            "produits, nombre d'avertissements), du plus récent au plus ancien."
        ),
        "mcp_server.read_run": (
            "Détail d'un traitement : entrées, fichiers produits et chaque avertissement avec le "
            "fichier, l'endroit (feuille, cartouche, bloc) et le conseil. À utiliser pour "
            "expliquer pourquoi une pièce ou un champ manque."
        ),
        "mcp_server.list_help_topics": (
            "Liste les sections du guide utilisateur de Drawflow (installation, fonctionnalités, "
            "assistant, Stream Dock, dépannage…)."
        ),
        "mcp_server.read_help": (
            "Lit une section du guide utilisateur (identifiant ou titre) : la marche à suivre "
            "officielle, à utiliser pour expliquer comment faire."
        ),
        "mcp_server.inspect_submission_headers": (
            "Inspecte une soumission (XLSX, ou PDF avec classeur joint) : en-têtes trouvés dans "
            "chaque feuille, colonnes déjà reconnues, colonnes normalisées et leurs en-têtes "
            "connus. À utiliser quand une soumission n'est pas reconnue."
        ),
        "mcp_server.propose_column_synonyms": (
            "Propose d'ajouter des en-têtes reconnus à des colonnes normalisées de la soumission, "
            'ex. {"Quantité": ["Nbre"]}. Rien n\'est enregistré : l\'utilisateur voit une carte '
            "et doit cliquer sur Appliquer."
        ),
        "mcp_server.propose_preset": (
            "Propose de lancer un préréglage. Rien n'est lancé : l'utilisateur voit une carte et "
            "doit cliquer sur Lancer."
        ),
        "mcp_server.propose_feature": (
            "Propose de lancer une fonctionnalité avec des entrées conformes à son inputs_schema "
            "(voir list_features). Rien n'est lancé : l'utilisateur voit une carte et doit "
            "cliquer sur Lancer."
        ),
        "model_client.unreadable_server_reply": "Réponse illisible du serveur du modèle.",
        "model_client.model_not_found": (
            "Le modèle « {model} » est introuvable sur le serveur local."
        ),
        "model_client.model_not_found.hint": (
            "Installez-le (par exemple : ollama pull {model}). {settings_hint}"
        ),
        "model_client.out_of_memory": (
            "Le modèle « {model} » est trop gros pour la mémoire de ce poste."
        ),
        "model_client.out_of_memory.hint": (
            "Choisissez un modèle plus petit dans Paramètres → Modèles d'IA : le modèle "
            "recommandé pour ce poste y est indiqué."
        ),
        "model_client.refused": "Le serveur du modèle a refusé la demande (HTTP {status}).",
        "model_client.refused_with_detail": (
            "Le serveur du modèle a refusé la demande (HTTP {status}) : {detail}"
        ),
        "model_client.unreachable": "Le modèle local ne répond pas à l'adresse {url}.",
        "model_client.unreachable.hint": (
            "Lancez Ollama ou LM Studio, puis réessayez. {settings_hint}"
        ),
        "model_client.unreadable_model_reply": "Réponse illisible du modèle local.",
        "models.not_ollama_hint": (
            "Le téléchargement passe par Ollama. Avec LM Studio, téléchargez le modèle depuis "
            "LM Studio puis choisissez-le dans le panneau de l'assistant."
        ),
        "models.ollama_not_responding": "Ollama ne répond pas.",
        "models.downloaded": "Modèle {model} téléchargé.",
        "models.invalid_name": "« {model} » n'est pas un nom de modèle valide.",
        "models.invalid_name.hint": "Exemple : qwen3.5:9b (voir ollama.com/library).",
        "service.tools_not_started": "Les outils Drawflow de l'assistant n'ont pas démarré.",
        "service.tools_not_started.hint": (
            "Réessayez ; si le problème persiste, redémarrez l'application."
        ),
        "service.invalid_conversation": "Conversation invalide.",
        "toolbox.truncated": "\n[… réponse tronquée]",
        "toolbox.tool_failed": "L'outil {name} n'a pas répondu : {error}",
        "tools.preset_not_found": "Le préréglage « {preset_id} » n'existe pas.",
        "tools.preset_not_found.hint": "Utilise list_presets.",
        "tools.invalid_inputs": "Entrées invalides pour « {feature} ».",
        "tools.invalid_inputs.hint": "{details}. Consulte inputs_schema avec list_features.",
        "tools.synonyms_label": "En-têtes reconnus",
        "tools.run_not_found": "Aucun traitement « {run_id} » dans l'historique.",
        "tools.run_not_found.hint": "Utilise list_runs.",
    },
    en={
        "agent.system_prompt": (
            "You are the assistant of Drawflow, an application that automates the work of a "
            "facade draughtsman: parts lists from DWG drawings, DOCX reports from PDFs and "
            "submissions. Answer briefly and concretely. Use the tools to look up the features, "
            "the presets and the templates instead of guessing. To explain how to install, "
            "configure or troubleshoot, read the relevant guide topic directly with read_help and "
            'follow its steps without inventing any button or menu. To answer "what is waiting '
            'for me?" or talk about the latest runs, read read_today. When the message contains '
            "attached files (paths), read them with inspect_file then suggest the fitting action "
            "(DWG → parts list, PDF → report, XLSX → submission). To explain a result (missing "
            "part or field, skipped file), read the run concerned with list_runs then read_run "
            "and quote the file and the place of the warning. To start a run, propose it with "
            "propose_preset or propose_feature: the user sees a card and decides. When a "
            "submission is not recognised, inspect_submission_headers then "
            "propose_column_synonyms to map its headers to the columns. Never say that a run has "
            "started; say that it is waiting for confirmation. Never invent a file path: ask for "
            "it if it is missing. Answer in English."
        ),
        "agent.help_topics_heading": "Guide topics (id: title): ",
        "agent.proposal_shown": (
            "Proposal shown to the user: the run will only start if they click Run. Nothing is "
            "running for now."
        ),
        "agent.invalid_arguments": "Invalid JSON arguments: fix the call.",
        "agent.too_many_tool_rounds": (
            "The assistant exceeded {rounds} rounds of tool calls for this question."
        ),
        "agent.too_many_tool_rounds.hint": "Rephrase the request more precisely.",
        "catalog.qwen35_27b": "The most capable, for very well-equipped computers.",
        "catalog.qwen35_9b": "The best balance for a recent computer.",
        "catalog.qwen3_8b": "Previous generation, well proven.",
        "catalog.llama31_8b": "Meta's alternative, weaker in French.",
        "catalog.qwen35_4b": "For computers with little memory.",
        "catalog.qwen35_2b": "Very light, simpler answers.",
        "conversation.last_message_not_user": "the last message must come from the user",
        "errors.settings_hint": "Check the address and the model in Settings → Assistant.",
        "history.previous_unreadable": "Previous conversation unreadable.",
        "history.invalid": "Invalid conversation.",
        "history.save_failed": "The conversation could not be saved.",
        "inspect.file_not_found": "File not found.",
        "inspect.file_not_found.hint": "Give the full path.",
        "inspect.file_too_large": "File too large to be inspected.",
        "inspect.unsupported_type": "Unsupported file type.",
        "inspect.unsupported_type.hint": "Drawflow reads DWG, DXF, PDF, XLSX and DOCX files.",
        "mcp_server.instructions": (
            "Drawflow automates the work of a facade draughtsman: parts lists from DWG drawings, "
            "DOCX reports from PDFs and submissions. These tools describe the available features, "
            "presets and templates, and propose runs that the user confirms."
        ),
        "mcp_server.list_features": (
            "Lists Drawflow's features, their instructions and their inputs."
        ),
        "mcp_server.list_presets": "Lists the saved presets (parameter sets ready to run).",
        "mcp_server.list_templates": (
            "Lists the imported output templates and the default template of each feature."
        ),
        "mcp_server.read_today": (
            "What awaits the user today: latest runs (result, produced files, warnings) and "
            "presets that can be run in one click."
        ),
        "mcp_server.inspect_file": (
            "Inspects a file given by the user (full path): DWG/DXF drawing (blocks and "
            "attributes), PDF (pages, text of the first page), XLSX (sheets, first rows) or DOCX "
            "(first paragraphs), and the recommended feature."
        ),
        "mcp_server.list_runs": (
            "Lists the latest runs (id, feature, result, produced files, number of warnings), "
            "newest first."
        ),
        "mcp_server.read_run": (
            "Detail of a run: inputs, produced files and each warning with the file, the place "
            "(sheet, title block, block) and the advice. Use it to explain why a part or a field "
            "is missing."
        ),
        "mcp_server.list_help_topics": (
            "Lists the sections of Drawflow's user guide (installation, features, assistant, "
            "Stream Dock, troubleshooting…)."
        ),
        "mcp_server.read_help": (
            "Reads a section of the user guide (id or title): the official steps, to use when "
            "explaining how to do something."
        ),
        "mcp_server.inspect_submission_headers": (
            "Inspects a submission (XLSX, or PDF with an attached workbook): headers found in "
            "each sheet, columns already recognised, normalised columns and their known headers. "
            "Use it when a submission is not recognised."
        ),
        "mcp_server.propose_column_synonyms": (
            "Proposes adding recognised headers to normalised columns of the submission, e.g. "
            '{"Quantity": ["Qty"]}. Nothing is saved: the user sees a card and must click Apply.'
        ),
        "mcp_server.propose_preset": (
            "Proposes running a preset. Nothing is started: the user sees a card and must click "
            "Run."
        ),
        "mcp_server.propose_feature": (
            "Proposes running a feature with inputs matching its inputs_schema (see "
            "list_features). Nothing is started: the user sees a card and must click Run."
        ),
        "model_client.unreadable_server_reply": "Unreadable reply from the model server.",
        "model_client.model_not_found": 'The model "{model}" was not found on the local server.',
        "model_client.model_not_found.hint": (
            "Install it (for example: ollama pull {model}). {settings_hint}"
        ),
        "model_client.out_of_memory": (
            'The model "{model}" is too big for this computer\'s memory.'
        ),
        "model_client.out_of_memory.hint": (
            "Choose a smaller model in Settings → AI models: the model recommended for this "
            "computer is shown there."
        ),
        "model_client.refused": "The model server refused the request (HTTP {status}).",
        "model_client.refused_with_detail": (
            "The model server refused the request (HTTP {status}): {detail}"
        ),
        "model_client.unreachable": "The local model does not answer at {url}.",
        "model_client.unreachable.hint": (
            "Start Ollama or LM Studio, then try again. {settings_hint}"
        ),
        "model_client.unreadable_model_reply": "Unreadable reply from the local model.",
        "models.not_ollama_hint": (
            "Downloads go through Ollama. With LM Studio, download the model from LM Studio then "
            "choose it in the assistant panel."
        ),
        "models.ollama_not_responding": "Ollama does not answer.",
        "models.downloaded": "Model {model} downloaded.",
        "models.invalid_name": '"{model}" is not a valid model name.',
        "models.invalid_name.hint": "Example: qwen3.5:9b (see ollama.com/library).",
        "service.tools_not_started": "The assistant's Drawflow tools did not start.",
        "service.tools_not_started.hint": (
            "Try again; if the problem persists, restart the application."
        ),
        "service.invalid_conversation": "Invalid conversation.",
        "toolbox.truncated": "\n[… reply truncated]",
        "toolbox.tool_failed": "The tool {name} did not answer: {error}",
        "tools.preset_not_found": 'The preset "{preset_id}" does not exist.',
        "tools.preset_not_found.hint": "Use list_presets.",
        "tools.invalid_inputs": 'Invalid inputs for "{feature}".',
        "tools.invalid_inputs.hint": "{details}. Check inputs_schema with list_features.",
        "tools.synonyms_label": "Recognised headers",
        "tools.run_not_found": 'No run "{run_id}" in the history.',
        "tools.run_not_found.hint": "Use list_runs.",
    },
)
