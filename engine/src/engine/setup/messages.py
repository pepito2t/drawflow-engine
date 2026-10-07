"""User-facing texts of the setup scan and installers, in both languages."""

from engine.core.i18n import define_messages

t = define_messages(
    fr={
        "actions.unknown": "Action d'installation inconnue : {action}.",
        "actions.oda_windows_only": (
            "L'installation automatique d'ODA File Converter n'existe que sous Windows."
        ),
        "actions.oda_windows_only.hint": "Utilisez la page de téléchargement.",
        "actions.oda_downloading": "Téléchargement d'ODA File Converter depuis le site officiel…",
        "actions.oda_not_found": (
            "ODA File Converter est introuvable dans les dossiers d'installation habituels."
        ),
        "actions.oda_not_found.hint": (
            "Indiquez le chemin de ODAFileConverter.exe dans Paramètres → Général."
        ),
        "actions.oda_configured": "ODA File Converter configuré : {path}",
        "actions.ollama_downloading": "Téléchargement d'Ollama depuis ollama.com (1,5 Go)…",
        "actions.ollama_brew": "Installation d'Ollama avec Homebrew…",
        "actions.ollama_starting": "Démarrage d'Ollama…",
        "actions.ollama_not_up": "Ollama ne répond pas après son démarrage.",
        "actions.ollama_not_up.hint": (
            "Lancez Ollama depuis le menu Démarrer, puis analysez à nouveau."
        ),
        "actions.ollama_started": "Ollama est démarré.",
        "actions.model_downloaded": "Modèle {model} téléchargé.",
        "actions.app_version_unknown": (
            "Version de Drawflow inconnue : relancez l'installation depuis l'app."
        ),
        "actions.plugin_downloading": "Téléchargement du plugin Drawflow pour Stream Dock…",
        "actions.autocad_plugin_downloading": "Téléchargement du plugin AutoCAD pour Stream Dock…",
        "actions.stream_dock_not_found": "Le logiciel Stream Dock est introuvable sur ce poste.",
        "actions.stream_dock_not_found.hint": (
            "Installez Stream Dock depuis la page de téléchargement de Mirabox."
        ),
        "actions.ollama_not_installed": "Ollama n'est pas installé.",
        "actions.ollama_not_installed.hint": "Utilisez le bouton Installer.",
        "actions.downloading": "Téléchargement de {name}",
        "actions.installing": "Installation de {name}…",
        "actions.install_failed": "L'installation de {name} a échoué (code {code}).",
        "actions.retry_or_page": "Réessayez, ou utilisez la page de téléchargement.",
        "commands.timeout": "Le programme « {program} » ne s'est pas terminé après {minutes} min.",
        "commands.timeout.hint": "Réessayez ; si cela se reproduit, installez-le depuis sa page.",
        "commands.start_failed": "Impossible de lancer le programme « {program} ».",
        "commands.start_failed.hint": "Vérifiez qu'il est installé, puis analysez à nouveau.",
        "installer_download.unavailable": (
            "{name} : l'installeur n'est plus disponible sur le site officiel (HTTP {status})."
        ),
        "installer_download.unavailable.hint": (
            "Cliquez sur « Page de téléchargement », installez {name}, puis sur « Analyser à "
            "nouveau » : Drawflow le détectera."
        ),
        "installer_download.failed": "{name} : téléchargement impossible.",
        "installer_download.failed.hint": "Vérifiez la connexion Internet, puis réessayez.",
        "installer_download.too_large": (
            "{name} : l'installeur téléchargé est anormalement volumineux."
        ),
        "installer_download.save_failed": (
            "{name} : impossible d'enregistrer l'installeur sur le disque."
        ),
        "installer_download.save_failed.hint": (
            "Vérifiez l'espace disque et les droits sur le dossier temporaire."
        ),
        "oda_installer.download_page_hint": (
            "Cliquez sur « Page de téléchargement », installez ODA File Converter, puis sur "
            "« Analyser à nouveau » : Drawflow le détectera."
        ),
        "oda_installer.cancelled": "L'installation d'ODA File Converter a été annulée.",
        "oda_installer.cancelled.hint": (
            "Relancez l'installation et acceptez la demande d'autorisation de Windows."
        ),
        "oda_installer.another_install": "Une autre installation est en cours sur ce poste.",
        "oda_installer.another_install.hint": "Attendez qu'elle se termine, puis réessayez.",
        "oda_installer.failed": "L'installation d'ODA File Converter a échoué (code {code}).",
        "ollama_installer.failed": "L'installation d'Ollama a échoué (code {code}).",
        "ollama_installer.failed.hint": "Réessayez, ou utilisez la page de téléchargement.",
        "ollama.pull_refused": (
            "Ollama a refusé le téléchargement de « {model} » (HTTP {status})."
        ),
        "ollama.pull_refused.hint": "Vérifiez le nom du modèle sur ollama.com/library.",
        "ollama.unreadable_progress": (
            "Ollama a envoyé une progression illisible pour « {model} »."
        ),
        "ollama.unreadable_progress.hint": (
            "Relancez le téléchargement ; si cela persiste, redémarrez Ollama."
        ),
        "ollama.pull_failed": "Téléchargement de « {model} » impossible : {error}",
        "ollama.pull_failed.hint": (
            "Vérifiez la connexion Internet et l'espace disque, puis réessayez."
        ),
        "ollama.unreadable_list": "Liste des modèles d'Ollama illisible.",
        "ollama.delete_unreachable": "Ollama ne répond pas : impossible de supprimer « {model} ».",
        "ollama.delete_unreachable.hint": "Vérifiez qu'Ollama est démarré.",
        "ollama.delete_failed": "Ollama n'a pas pu supprimer « {model} » (HTTP {status}).",
        "scan.action.install": "Installer",
        "scan.action.use": "Utiliser",
        "scan.action.download_page": "Page de téléchargement",
        "scan.action.start": "Démarrer",
        "scan.action.download": "Télécharger",
        "scan.action.choose_model": "Choisir un modèle",
        "scan.action.install_plugin": "Installer le plugin",
        "scan.action.project_page": "Page du projet",
        "scan.action.update": "Mettre à jour",
        "scan.action.reinstall": "Réinstaller",
        "scan.oda.installed_not_configured": "Installé mais pas configuré : {path}",
        "scan.oda.needed": "Nécessaire pour lire les fichiers DWG.",
        "scan.model_server.label": "Serveur du modèle local",
        "scan.model_server.openai_compatible": "Serveur compatible OpenAI",
        "scan.model_server.ollama_down": "Ollama est installé mais ne répond pas.",
        "scan.model_server.ollama_pitch": (
            "Ollama fait tourner l'assistant sur ce poste, sans connexion externe."
        ),
        "scan.model.label": "Modèle d'IA",
        "scan.model.server_first": "{model} — démarrez d'abord le serveur.",
        "scan.model.available": "{model} disponible.",
        "scan.model.not_downloaded": (
            "{model} pas encore téléchargé. Recommandé pour ce poste : {recommended}."
        ),
        "scan.model.not_on_server": (
            "{model} introuvable sur le serveur : chargez-le dans LM Studio ou changez de modèle."
        ),
        "scan.stream_dock.label": "Plugin Drawflow pour Stream Dock",
        "scan.stream_dock.not_installed": "Logiciel Stream Dock (Mirabox) non installé.",
        "scan.stream_dock.pitch": "Pilotez Drawflow depuis les touches du Stream Dock.",
        "scan.autocad_plugin.label": "Plugin AutoCAD pour Stream Dock",
        "scan.autocad_plugin.detected": "AutoCAD détecté.",
        "scan.autocad_plugin.not_detected": (
            "AutoCAD (version complète, pas LT) non détecté sur ce poste."
        ),
        "scan.autocad_plugin.pitch": (
            "Macros, calques et bascules AutoCAD depuis le Stream Dock. {autocad}"
        ),
        "scan.plugin.version_installed": "Version {version} installée.",
        "scan.plugin.installed": "Installé.",
        "scan.plugin.update_available": "{version} Version {available} disponible.",
        "scan.plugin.restart": "{version} Redémarrez Stream Dock après chaque installation.",
        "signature.not_executed_hint": (
            "Il n'a pas été exécuté. Téléchargez l'installeur depuis la page officielle, "
            "ou réessayez plus tard."
        ),
        "signature.unverifiable": ("{name} : impossible de vérifier la signature de l'installeur."),
        "signature.untrusted": (
            "{name} : l'installeur téléchargé n'est pas signé par un éditeur de confiance "
            "({status})."
        ),
        "signature.wrong_signer": (
            "{name} : l'installeur est signé par « {subject} », pas par {expected}."
        ),
        "stream_dock.installed": (
            "Plugin {plugin_id} installé dans Stream Dock. Redémarrez Stream Dock pour l'activer."
        ),
        "stream_dock.download_failed": "Téléchargement du plugin impossible.",
        "stream_dock.download_failed.hint": "Vérifiez la connexion Internet, puis réessayez.",
        "stream_dock.not_found": "Le plugin est introuvable à cette adresse (HTTP {status}).",
        "stream_dock.not_found.hint": (
            "Aucune version publiée, ou Drawflow à mettre à jour ; réessayez plus tard."
        ),
        "stream_dock.too_large": "Le plugin téléchargé est anormalement volumineux.",
        "stream_dock.unreadable": "Le plugin téléchargé est illisible.",
        "stream_dock.incomplete": "Le plugin téléchargé est incomplet (manifest.json absent).",
        "stream_dock.in_use": "Le plugin n'a pas pu être remplacé : Stream Dock l'utilise encore.",
        "stream_dock.in_use.hint": (
            "Quittez Stream Dock, cliquez à nouveau sur Installer, puis relancez Stream Dock."
        ),
    },
    en={
        "actions.unknown": "Unknown setup action: {action}.",
        "actions.oda_windows_only": (
            "Automatic installation of ODA File Converter only exists on Windows."
        ),
        "actions.oda_windows_only.hint": "Use the download page.",
        "actions.oda_downloading": "Downloading ODA File Converter from the official site…",
        "actions.oda_not_found": "ODA File Converter was not found in the usual install folders.",
        "actions.oda_not_found.hint": (
            "Enter the path to ODAFileConverter.exe in Settings → General."
        ),
        "actions.oda_configured": "ODA File Converter configured: {path}",
        "actions.ollama_downloading": "Downloading Ollama from ollama.com (1.5 GB)…",
        "actions.ollama_brew": "Installing Ollama with Homebrew…",
        "actions.ollama_starting": "Starting Ollama…",
        "actions.ollama_not_up": "Ollama does not answer after starting.",
        "actions.ollama_not_up.hint": "Start Ollama from the Start menu, then scan again.",
        "actions.ollama_started": "Ollama is running.",
        "actions.model_downloaded": "Model {model} downloaded.",
        "actions.app_version_unknown": (
            "Unknown Drawflow version: restart the install from the app."
        ),
        "actions.plugin_downloading": "Downloading the Drawflow plugin for Stream Dock…",
        "actions.autocad_plugin_downloading": "Downloading the AutoCAD plugin for Stream Dock…",
        "actions.stream_dock_not_found": "The Stream Dock software was not found on this computer.",
        "actions.stream_dock_not_found.hint": "Install Stream Dock from Mirabox's download page.",
        "actions.ollama_not_installed": "Ollama is not installed.",
        "actions.ollama_not_installed.hint": "Use the Install button.",
        "actions.downloading": "Downloading {name}",
        "actions.installing": "Installing {name}…",
        "actions.install_failed": "The installation of {name} failed (code {code}).",
        "actions.retry_or_page": "Try again, or use the download page.",
        "commands.timeout": 'The program "{program}" did not finish after {minutes} min.',
        "commands.timeout.hint": "Try again; if it happens again, install it from its page.",
        "commands.start_failed": 'The program "{program}" could not be started.',
        "commands.start_failed.hint": "Check that it is installed, then scan again.",
        "installer_download.unavailable": (
            "{name}: the installer is no longer available on the official site (HTTP {status})."
        ),
        "installer_download.unavailable.hint": (
            'Click "Download page", install {name}, then "Scan again": Drawflow will detect it.'
        ),
        "installer_download.failed": "{name}: download failed.",
        "installer_download.failed.hint": "Check the Internet connection, then try again.",
        "installer_download.too_large": "{name}: the downloaded installer is unusually large.",
        "installer_download.save_failed": "{name}: the installer could not be saved to disk.",
        "installer_download.save_failed.hint": (
            "Check the disk space and the permissions on the temporary folder."
        ),
        "oda_installer.download_page_hint": (
            'Click "Download page", install ODA File Converter, then "Scan again": Drawflow '
            "will detect it."
        ),
        "oda_installer.cancelled": "The installation of ODA File Converter was cancelled.",
        "oda_installer.cancelled.hint": (
            "Start the installation again and accept the Windows permission prompt."
        ),
        "oda_installer.another_install": "Another installation is running on this computer.",
        "oda_installer.another_install.hint": "Wait for it to finish, then try again.",
        "oda_installer.failed": "The installation of ODA File Converter failed (code {code}).",
        "ollama_installer.failed": "The installation of Ollama failed (code {code}).",
        "ollama_installer.failed.hint": "Try again, or use the download page.",
        "ollama.pull_refused": 'Ollama refused the download of "{model}" (HTTP {status}).',
        "ollama.pull_refused.hint": "Check the model name on ollama.com/library.",
        "ollama.unreadable_progress": 'Ollama sent unreadable progress for "{model}".',
        "ollama.unreadable_progress.hint": (
            "Start the download again; if it persists, restart Ollama."
        ),
        "ollama.pull_failed": 'Download of "{model}" failed: {error}',
        "ollama.pull_failed.hint": (
            "Check the Internet connection and the disk space, then try again."
        ),
        "ollama.unreadable_list": "Ollama's model list is unreadable.",
        "ollama.delete_unreachable": 'Ollama does not answer: "{model}" could not be removed.',
        "ollama.delete_unreachable.hint": "Check that Ollama is running.",
        "ollama.delete_failed": 'Ollama could not remove "{model}" (HTTP {status}).',
        "scan.action.install": "Install",
        "scan.action.use": "Use",
        "scan.action.download_page": "Download page",
        "scan.action.start": "Start",
        "scan.action.download": "Download",
        "scan.action.choose_model": "Choose a model",
        "scan.action.install_plugin": "Install the plugin",
        "scan.action.project_page": "Project page",
        "scan.action.update": "Update",
        "scan.action.reinstall": "Reinstall",
        "scan.oda.installed_not_configured": "Installed but not configured: {path}",
        "scan.oda.needed": "Needed to read DWG files.",
        "scan.model_server.label": "Local model server",
        "scan.model_server.openai_compatible": "OpenAI-compatible server",
        "scan.model_server.ollama_down": "Ollama is installed but does not answer.",
        "scan.model_server.ollama_pitch": (
            "Ollama runs the assistant on this computer, with no external connection."
        ),
        "scan.model.label": "AI model",
        "scan.model.server_first": "{model} — start the server first.",
        "scan.model.available": "{model} available.",
        "scan.model.not_downloaded": (
            "{model} not downloaded yet. Recommended for this computer: {recommended}."
        ),
        "scan.model.not_on_server": (
            "{model} not found on the server: load it in LM Studio or change the model."
        ),
        "scan.stream_dock.label": "Drawflow plugin for Stream Dock",
        "scan.stream_dock.not_installed": "Stream Dock software (Mirabox) not installed.",
        "scan.stream_dock.pitch": "Drive Drawflow from the Stream Dock keys.",
        "scan.autocad_plugin.label": "AutoCAD plugin for Stream Dock",
        "scan.autocad_plugin.detected": "AutoCAD detected.",
        "scan.autocad_plugin.not_detected": (
            "AutoCAD (full version, not LT) not detected on this computer."
        ),
        "scan.autocad_plugin.pitch": (
            "AutoCAD macros, layers and toggles from the Stream Dock. {autocad}"
        ),
        "scan.plugin.version_installed": "Version {version} installed.",
        "scan.plugin.installed": "Installed.",
        "scan.plugin.update_available": "{version} Version {available} available.",
        "scan.plugin.restart": "{version} Restart Stream Dock after each installation.",
        "signature.not_executed_hint": (
            "It was not executed. Download the installer from the official page, or try again "
            "later."
        ),
        "signature.unverifiable": "{name}: the installer's signature could not be verified.",
        "signature.untrusted": (
            "{name}: the downloaded installer is not signed by a trusted publisher ({status})."
        ),
        "signature.wrong_signer": (
            '{name}: the installer is signed by "{subject}", not by {expected}.'
        ),
        "stream_dock.installed": (
            "Plugin {plugin_id} installed in Stream Dock. Restart Stream Dock to enable it."
        ),
        "stream_dock.download_failed": "The plugin could not be downloaded.",
        "stream_dock.download_failed.hint": "Check the Internet connection, then try again.",
        "stream_dock.not_found": "The plugin was not found at this address (HTTP {status}).",
        "stream_dock.not_found.hint": (
            "No published version, or Drawflow needs an update; try again later."
        ),
        "stream_dock.too_large": "The downloaded plugin is unusually large.",
        "stream_dock.unreadable": "The downloaded plugin is unreadable.",
        "stream_dock.incomplete": "The downloaded plugin is incomplete (manifest.json missing).",
        "stream_dock.in_use": "The plugin could not be replaced: Stream Dock is still using it.",
        "stream_dock.in_use.hint": (
            "Quit Stream Dock, click Install again, then start Stream Dock again."
        ),
    },
)
