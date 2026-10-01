import argparse
import json
import sys
import traceback
from collections.abc import Sequence
from pathlib import Path

from engine.core.errors import EngineError
from engine.core.events import Emit, ErrorEvent, make_stream_emitter
from engine.core.registry import discover_modules, get_module
from engine.core.runner import read_input_file, run_module

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
        if arguments.command == "list-modules":
            _list_modules()
        else:
            _run(arguments.module_id, Path(arguments.input), emit)
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
    run_parser.add_argument("--input", required=True, help="Fichier JSON des paramètres.")
    return parser


def _list_modules() -> None:
    catalog = [
        {
            "manifest": module.manifest.model_dump(),
            "inputs_schema": module.inputs_model.model_json_schema(),
        }
        for module in discover_modules().values()
    ]
    sys.stdout.write(json.dumps(catalog, ensure_ascii=False) + "\n")
    sys.stdout.flush()


def _run(module_id: str, input_path: Path, emit: Emit) -> None:
    module = get_module(module_id)
    raw_inputs = read_input_file(input_path)
    run_module(module, raw_inputs, emit)


def _force_utf8_output() -> None:
    # Windows consoles default to a legacy code page; the NDJSON contract is UTF-8.
    for stream in (sys.stdout, sys.stderr):
        if hasattr(stream, "reconfigure"):
            stream.reconfigure(encoding="utf-8")


if __name__ == "__main__":
    raise SystemExit(main())
