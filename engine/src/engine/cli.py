import argparse
import json
import sys
import traceback
from collections.abc import Sequence
from pathlib import Path
from typing import Any

from engine.core.errors import EngineError
from engine.core.events import Emit, ErrorEvent, make_stream_emitter
from engine.core.registry import discover_modules, get_module
from engine.core.runner import read_input_file, run_module
from engine.core.settings import describe_settings, load_run_settings, save_settings
from engine.core.templates import TemplateLibrary
from engine.requests import (
    SETTINGS_FILE_ACTIONS,
    TEMPLATE_ACTIONS,
    handle_settings_file,
    handle_templates,
)

EXIT_SUCCESS = 0
EXIT_BUSINESS_ERROR = 1
EXIT_INTERNAL_ERROR = 2
INTERNAL_ERROR_MESSAGE = "Erreur interne inattendue."
INTERNAL_ERROR_HINT = "Réessayez ; si le problème persiste, transmettez le journal au support."


def main(argv: Sequence[str] | None = None) -> int:
    _force_utf8_output()
    arguments = _build_parser().parse_args(argv)
    emit = make_stream_emitter(sys.stdout)
    try:
        _dispatch(arguments, emit)
    except EngineError as error:
        file = str(error.file) if error.file else None
        emit(ErrorEvent(message=error.message, file=file, hint=error.hint))
        return EXIT_BUSINESS_ERROR
    except Exception:
        # Boundary of the sidecar: details go to stderr, the user gets a readable event.
        traceback.print_exc(file=sys.stderr)
        emit(ErrorEvent(message=INTERNAL_ERROR_MESSAGE, hint=INTERNAL_ERROR_HINT))
        return EXIT_INTERNAL_ERROR
    return EXIT_SUCCESS


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="engine")
    commands = parser.add_subparsers(dest="command", required=True)
    commands.add_parser("list-modules", help="Liste les manifestes des modules (JSON).")

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


def _dispatch(arguments: argparse.Namespace, emit: Emit) -> None:
    if arguments.command == "list-modules":
        _write_json(_module_catalog())
    elif arguments.command == "run":
        _run(arguments, emit)
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
    module = get_module(arguments.module_id)
    settings = load_run_settings(arguments.settings, module)
    default_template = None
    if arguments.settings is not None and module.manifest.template_kind is not None:
        default_template = TemplateLibrary(arguments.settings).default_for(module.manifest.id)
    run_module(module, read_input_file(arguments.input), settings, emit, default_template)


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
