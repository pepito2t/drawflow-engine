"""User-facing texts of the mailbox features, in both languages."""

from engine.core.i18n import define_messages

t = define_messages(
    fr={
        "graph.no_device_code": "Microsoft n'a pas fourni de code de connexion.",
        "graph.login_refused": "Connexion à Microsoft refusée : {error}",
        "graph.login_refused.hint": (
            "Vérifiez l'identifiant d'application et le tenant dans Paramètres → Courriel."
        ),
        "graph.unreadable_login_reply": "Réponse de connexion illisible.",
        "graph.login_failed": "Connexion à Microsoft échouée : {error}",
        "graph.code_expired": "Le code de connexion a expiré.",
        "graph.code_expired.hint": "Relancez la connexion et saisissez le nouveau code.",
        "graph.session_expired": "La session Microsoft n'est plus valable.",
        "graph.session_expired.hint": "Reconnectez la boîte mail dans l'onglet Courriels.",
        "graph.attachment_refused": "Téléchargement d'une pièce jointe refusé par Microsoft.",
        "graph.unreachable": "Microsoft 365 est injoignable.",
        "graph.unreachable.hint": "Vérifiez la connexion Internet.",
        "graph.unreadable_reply": "Réponse de Microsoft 365 illisible.",
        "graph.read_refused": "Microsoft 365 a refusé la lecture : {error}",
        "graph.unknown_error": "erreur inconnue",
        "service.not_configured_hint": (
            "Renseignez l'identifiant d'application Entra ID dans Paramètres → Courriel."
        ),
        "service.not_connected_hint": "Connectez la boîte mail dans l'onglet Courriels.",
        "service.missing_code": "Code de connexion manquant.",
        "service.not_connected": "Aucune boîte mail connectée.",
        "service.not_configured": "La boîte mail n'est pas configurée.",
        "service.attachment_default_name": "pièce jointe",
        "store.no_subject": "(sans objet)",
        "store.no_name": "sans nom",
        "store.index_unreadable": (
            "L'index des conversations est illisible ; il n'a pas été modifié."
        ),
        "store.index_unreadable.hint": (
            "Supprimez-le pour le reconstruire à la prochaine récupération."
        ),
        "store.conversation_gone": "Cette conversation n'est plus dans Drawflow.",
        "store.message_save_failed": "Impossible d'enregistrer un message.",
        "store.attachment_save_failed": "Impossible d'enregistrer une pièce jointe.",
        "store.remove_failed": "Impossible de supprimer la conversation.",
        "store.export_failed": "Impossible d'exporter la conversation.",
        "store.export.from": "- De : {sender}",
        "store.export.to": "- À : {recipients}",
        "store.export.received": "- Reçu : {date}",
        "store.export.attachments": "- Pièces jointes : {names}",
        "tokens.save_failed": "Impossible d'enregistrer la session Microsoft.",
        "tokens.clear_failed": "Impossible d'effacer la session Microsoft.",
        "tokens.unprotected_hint": (
            "Les droits du fichier de session n'ont pas pu être restreints : "
            "vérifiez que le dossier de configuration n'est lisible que par vous."
        ),
    },
    en={
        "graph.no_device_code": "Microsoft did not provide a sign-in code.",
        "graph.login_refused": "Sign-in to Microsoft refused: {error}",
        "graph.login_refused.hint": (
            "Check the application id and the tenant in Settings → Email."
        ),
        "graph.unreadable_login_reply": "Unreadable sign-in reply.",
        "graph.login_failed": "Sign-in to Microsoft failed: {error}",
        "graph.code_expired": "The sign-in code has expired.",
        "graph.code_expired.hint": "Start the sign-in again and enter the new code.",
        "graph.session_expired": "The Microsoft session is no longer valid.",
        "graph.session_expired.hint": "Reconnect the mailbox in the Emails tab.",
        "graph.attachment_refused": "Microsoft refused the download of an attachment.",
        "graph.unreachable": "Microsoft 365 is unreachable.",
        "graph.unreachable.hint": "Check the Internet connection.",
        "graph.unreadable_reply": "Unreadable reply from Microsoft 365.",
        "graph.read_refused": "Microsoft 365 refused the read: {error}",
        "graph.unknown_error": "unknown error",
        "service.not_configured_hint": ("Enter the Entra ID application id in Settings → Email."),
        "service.not_connected_hint": "Connect the mailbox in the Emails tab.",
        "service.missing_code": "Sign-in code missing.",
        "service.not_connected": "No mailbox connected.",
        "service.not_configured": "The mailbox is not configured.",
        "service.attachment_default_name": "attachment",
        "store.no_subject": "(no subject)",
        "store.no_name": "unnamed",
        "store.index_unreadable": "The conversation index is unreadable; it was not modified.",
        "store.index_unreadable.hint": "Delete it to rebuild it at the next fetch.",
        "store.conversation_gone": "This conversation is no longer in Drawflow.",
        "store.message_save_failed": "A message could not be saved.",
        "store.attachment_save_failed": "An attachment could not be saved.",
        "store.remove_failed": "The conversation could not be removed.",
        "store.export_failed": "The conversation could not be exported.",
        "store.export.from": "- From: {sender}",
        "store.export.to": "- To: {recipients}",
        "store.export.received": "- Received: {date}",
        "store.export.attachments": "- Attachments: {names}",
        "tokens.save_failed": "The Microsoft session could not be saved.",
        "tokens.clear_failed": "The Microsoft session could not be cleared.",
        "tokens.unprotected_hint": (
            "The session file's permissions could not be restricted: "
            "check that the configuration folder is readable by you only."
        ),
    },
)
