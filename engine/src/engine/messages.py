"""User-facing texts of the command line entry point, in both languages."""

from engine.core.i18n import define_messages

t = define_messages(
    fr={
        "cli.internal_error": "Erreur interne inattendue.",
        "cli.internal_error.hint": (
            "Réessayez ; si le problème persiste, transmettez le journal au support."
        ),
        "requests.no_template": "« {module} » n'utilise pas de modèle.",
        "requests.invalid": "Requête invalide.",
    },
    en={
        "cli.internal_error": "Unexpected internal error.",
        "cli.internal_error.hint": ("Try again; if the problem persists, send the log to support."),
        "requests.no_template": '"{module}" does not use a template.',
        "requests.invalid": "Invalid request.",
    },
)
