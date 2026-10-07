# ruff: noqa: E402
import argparse
import json
import sys
import traceback

from engine.core.i18n import LANGUAGES, configure_from_argv

# Labels and manifests are built when their modules load: the language must be known first.
configure_from_argv(sys.argv[1:])
from collections.abc import Sequence
from dataclasses import asdict
from pathlib import Path
from typing import Any

from engine.assistant.events import make_assistant_emitter
from engine.core.diagnostics import record_failure
from engine.core.errors import EngineError
from engine.core.events import Emit, ErrorEvent, make_stream_emitter
from engine.core.guide import sections as guide_sections
from engine.core.history import (
    HISTORY_ACTIONS,
    HistoryStore,
    UsageCounters,
    handle_history,
    run_with_history,
)
from engine.core.registry import discover_modules, get_module
from engine.core.runner import read_input_file, run_module
from engine.core.settings import (
    describe_settings,
    load_general_settings,
    load_run_settings,
    save_settings,
)
from engine.core.shutdown import exit_when_stdin_closes
from engine.core.stats import StatsStore
from engine.core.templates import TemplateLibrary
from engine.messages import t
from engine.requests import (
    MAIL_ACTIONS,
    PRESET_ACTIONS,
    PROFILE_ACTIONS,
    SETTINGS_FILE_ACTIONS,
    TEMPLATE_ACTIONS,
    handle_mail,
    handle_presets,
    handle_profile,
    handle_settings_file,
    handle_templates,
)

EXIT_SUCCESS = 0
EXIT_BUSINESS_ERROR = 1
EXIT_INTERNAL_ERROR = 2
ASSISTANT_ACTIONS = {
    "chat": "Un tour de conversation (flux NDJSON).",
    "models": "Modèles disponibles sur le serveur local (JSON).",
    "history-get": "Conversation enregistrée (JSON).",
    "history-save": "Enregistre la conversation en cours (JSON).",
    "catalog": "Modèles conseillés, installés et recommandé pour ce poste (JSON).",
    "model-delete": "Supprime un modèle d'Ollama (JSON).",
}


def main(argv: Sequence[str] | None = None) -> int:
    _force_utf8_output()
    if argv is not None:
        configure_from_argv(argv)
    arguments = _build_parser().parse_args(argv)
    emit = make_stream_emitter(sys.stdout)
    settings = getattr(arguments, "settings", None)
    command = list(argv) if argv is not None else sys.argv[1:]
    try:
        _dispatch(arguments, emit)
    except EngineError as error:
        record_failure(settings, command, error)
        file = str(error.file) if error.file else None
        emit(ErrorEvent(message=error.message, file=file, hint=error.hint))
        return EXIT_BUSINESS_ERROR
    except Exception as error:
        # Boundary of the sidecar: details go to the log and stderr, the user gets a readable event.
        record_failure(settings, command, error)
        traceback.print_exc(file=sys.stderr)
        emit(ErrorEvent(message=t("cli.internal_error"), hint=t("cli.internal_error.hint")))
        return EXIT_INTERNAL_ERROR
    return EXIT_SUCCESS


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="engine")
    parser.add_argument("--lang", choices=LANGUAGES, help="Langue des textes (défaut : réglage).")
    commands = parser.add_subparsers(dest="command", required=True)
    list_parser = commands.add_parser(
        "list-modules", help="Liste les manifestes des modules (JSON)."
    )
    list_parser.add_argument("--settings", type=Path, help="Fichier des paramètres (langue).")

    run_parser = commands.add_parser("run", help="Exécute un module (flux NDJSON).")
    run_parser.add_argument("module_id")
    run_parser.add_argument("--input", type=Path, required=True, help="Paramètres du formulaire.")
    run_parser.add_argument("--settings", type=Path, help="Fichier des paramètres de l'app.")

    settings_parser = commands.add_parser("settings", help="Lit ou enregistre les paramètres.")
    settings_commands = settings_parser.add_subparsers(dest="settings_command", required=True)
    get_parser = settings_commands.add_parser("get", help="Sections, schémas et valeurs (JSON).")
    get_parser.add_argument("--settings", type=Path)
    set_parser = settings_commands.add_parser("set", help="Valide et enregistre des sections.")
    set_parser.add_argument("--settings", type=Path, required=True)
    set_parser.add_argument("--input", type=Path, required=True, help="Sections à enregistrer.")
    for action, help_text in SETTINGS_FILE_ACTIONS.items():
        _add_request_parser(settings_commands, action, help_text)

    profile_parser = commands.add_parser("profile", help="Profil complet du poste (zip).")
    profile_commands = profile_parser.add_subparsers(dest="profile_command", required=True)
    for action, help_text in PROFILE_ACTIONS.items():
        _add_request_parser(profile_commands, action, help_text)

    mail_parser = commands.add_parser("mail", help="Courriels : boîte Microsoft 365 en lecture.")
    mail_commands = mail_parser.add_subparsers(dest="mail_command", required=True)
    for action, help_text in MAIL_ACTIONS.items():
        _add_request_parser(mail_commands, action, help_text)

    presets_parser = commands.add_parser("presets", help="Préréglages des fonctionnalités.")
    presets_commands = presets_parser.add_subparsers(dest="presets_command", required=True)
    for action, help_text in PRESET_ACTIONS.items():
        _add_request_parser(presets_commands, action, help_text)

    history_parser = commands.add_parser("history", help="Historique des traitements.")
    history_commands = history_parser.add_subparsers(dest="history_command", required=True)
    for action, help_text in HISTORY_ACTIONS.items():
        _add_request_parser(history_commands, action, help_text)

    mcp_parser = commands.add_parser("mcp", help="Serveur MCP de l'assistant (stdio).")
    mcp_parser.add_argument("--settings", type=Path, required=True)

    assistant_parser = commands.add_parser("assistant", help="Assistant local (modèle + MCP).")
    assistant_commands = assistant_parser.add_subparsers(dest="assistant_command", required=True)
    for action, help_text in ASSISTANT_ACTIONS.items():
        _add_request_parser(assistant_commands, action, help_text)
    pull_parser = assistant_commands.add_parser("pull", help="Télécharge un modèle (NDJSON).")
    pull_parser.add_argument("model")
    pull_parser.add_argument("--settings", type=Path, required=True)

    help_parser = commands.add_parser("help", help="Guide utilisateur, par section.")
    help_commands = help_parser.add_subparsers(dest="help_command", required=True)
    _add_request_parser(help_commands, "guide", "Toutes les sections du guide (JSON).")

    setup_parser = commands.add_parser("setup", help="Prérequis de l'installation.")
    setup_commands = setup_parser.add_subparsers(dest="setup_command", required=True)
    _add_request_parser(setup_commands, "scan", "État des prérequis et actions proposées (JSON).")
    setup_run = setup_commands.add_parser("run", help="Exécute une action d'installation (NDJSON).")
    setup_run.add_argument("action")
    setup_run.add_argument("--settings", type=Path, required=True)
    setup_run.add_argument("--app-version", help="Version de Drawflow (plugin Stream Dock).")

    templates_parser = commands.add_parser("templates", help="Bibliothèque de modèles de sortie.")
    templates_commands = templates_parser.add_subparsers(dest="templates_command", required=True)
    for action, help_text in TEMPLATE_ACTIONS.items():
        _add_request_parser(templates_commands, action, help_text)
    return parser


def _add_request_parser(
    commands: "argparse._SubParsersAction[argparse.ArgumentParser]", action: str, help_text: str
) -> None:
    parser = commands.add_parser(action, help=help_text)
    parser.add_argument("--settings", type=Path, required=True)
    parser.add_argument("--input", type=Path, help="Requête JSON.")
    parser.add_argument("--app-version", help="Version de Drawflow (plugins Stream Dock).")


def _dispatch(arguments: argparse.Namespace, emit: Emit) -> None:
    if arguments.command == "list-modules":
        _write_json(_module_catalog())
    elif arguments.command == "run":
        _run(arguments, emit)
    elif arguments.command == "mcp":
        _serve_mcp(arguments.settings)
    elif arguments.command == "assistant":
        _assistant(arguments, emit)
    elif arguments.command == "setup":
        _setup(arguments, emit)
    elif arguments.command == "help":
        _write_json({"sections": [asdict(section) for section in guide_sections()]})
    elif arguments.command == "history":
        _write_json(
            handle_history(arguments.history_command, arguments.settings, _request(arguments))
        )
    elif arguments.command == "profile":
        _write_json(
            handle_profile(
                arguments.profile_command,
                arguments.settings,
                _request(arguments),
                arguments.app_version,
            )
        )
    elif arguments.command == "mail":
        _write_json(handle_mail(arguments.mail_command, arguments.settings, _request(arguments)))
    elif arguments.command == "presets":
        _write_json(
            handle_presets(arguments.presets_command, arguments.settings, _request(arguments))
        )
    elif arguments.command == "templates":
        _write_json(
            handle_templates(arguments.templates_command, arguments.settings, _request(arguments))
        )
    elif arguments.settings_command in SETTINGS_FILE_ACTIONS:
        _write_json(
            handle_settings_file(
                arguments.settings_command, arguments.settings, _request(arguments)
            )
        )
    elif arguments.settings_command == "set":
        save_settings(arguments.settings, read_input_file(arguments.input), discover_modules())
        _write_json({"sections": describe_settings(arguments.settings, discover_modules())})
    else:
        _write_json({"sections": describe_settings(arguments.settings, discover_modules())})


def _run(arguments: argparse.Namespace, emit: Emit) -> None:
    exit_when_stdin_closes()
    module = get_module(arguments.module_id)
    settings = load_run_settings(arguments.settings, module)
    default_template = None
    if arguments.settings is not None and module.manifest.template_kind is not None:
        default_template = TemplateLibrary(arguments.settings).default_for(module.manifest.id)
    raw_inputs = read_input_file(arguments.input)
    history = HistoryStore(arguments.settings) if arguments.settings is not None else None
    run_with_history(
        history,
        module,
        raw_inputs,
        emit,
        lambda observed: run_module(module, raw_inputs, settings, observed, default_template),
        counters=_usage_counters(arguments.settings),
    )


def _usage_counters(settings_file: Path | None) -> UsageCounters | None:
    if settings_file is None:
        return None
    general = load_general_settings(settings_file)
    if not general.usage_counters:
        return None
    return UsageCounters(StatsStore(settings_file), general.minutes_saved_per_file)


# The MCP SDK costs ~200 ms to import: only the commands that need it pay for it.
def _serve_mcp(settings: Path) -> None:
    from engine.assistant.mcp_server import serve

    serve(settings)


def _assistant(arguments: argparse.Namespace, emit: Emit) -> None:
    from engine.assistant import history, models, service

    if arguments.assistant_command == "catalog":
        _write_json(models.catalog(arguments.settings))
    elif arguments.assistant_command == "pull":
        models.pull(arguments.settings, arguments.model, emit)
    elif arguments.assistant_command == "model-delete":
        _write_json(models.remove(arguments.settings, _request(arguments)))
    elif arguments.assistant_command == "models":
        _write_json(service.list_models(arguments.settings))
    elif arguments.assistant_command == "history-get":
        _write_json(history.read_history(arguments.settings))
    elif arguments.assistant_command == "history-save":
        _write_json(history.save_history(arguments.settings, _request(arguments)))
    else:
        service.chat(arguments.settings, _request(arguments), make_assistant_emitter())


def _setup(arguments: argparse.Namespace, emit: Emit) -> None:
    from engine.setup import actions, service

    if arguments.setup_command == "run":
        context = actions.SetupContext(arguments.settings, emit, app_version=arguments.app_version)
        actions.run_action(arguments.action, context)
    else:
        _write_json(service.scan(arguments.settings, app_version=arguments.app_version))


def _request(arguments: argparse.Namespace) -> dict[str, Any]:
    return read_input_file(arguments.input) if arguments.input is not None else {}


def _module_catalog() -> list[dict[str, Any]]:
    return [
        {
            "manifest": module.manifest.model_dump(),
            "inputs_schema": module.inputs_model.model_json_schema(),
        }
        for module in discover_modules().values()
    ]


def _write_json(payload: object) -> None:
    sys.stdout.write(json.dumps(payload, ensure_ascii=False) + "\n")
    sys.stdout.flush()


def _force_utf8_output() -> None:
    # Windows consoles default to a legacy code page; the NDJSON contract is UTF-8.
    for stream in (sys.stdout, sys.stderr):
        if hasattr(stream, "reconfigure"):
            stream.reconfigure(encoding="utf-8")


if __name__ == "__main__":
    raise SystemExit(main())
