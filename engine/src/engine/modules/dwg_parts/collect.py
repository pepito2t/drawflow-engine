from collections.abc import Sequence
from pathlib import Path

from engine.core.errors import EngineError
from engine.core.events import Emit, LogEvent, WarningEvent

PLAN_SUFFIXES = frozenset({".dwg", ".dxf"})


class PlanCollectionError(EngineError):
    pass


def collect_plans(
    files: Sequence[Path], folders: Sequence[Path], *, recursive: bool, emit: Emit
) -> list[Path]:
    plans: dict[Path, Path] = {}
    for file in files:
        if is_plan(file):
            plans.setdefault(file.resolve(), file)
        else:
            emit(
                WarningEvent(
                    message="Fichier ignoré : ce n'est pas un plan DWG/DXF.", file=str(file)
                )
            )
    for folder in folders:
        for plan in _plans_in(folder, recursive=recursive):
            plans.setdefault(plan.resolve(), plan)
    if not plans:
        raise PlanCollectionError(
            "Aucun plan DWG ou DXF trouvé.",
            hint="Vérifiez les fichiers et dossiers choisis (et l'option sous-dossiers).",
        )
    found = sorted(plans.values(), key=lambda path: str(path).casefold())
    emit(LogEvent(message=f"{len(found)} plan(s) à traiter."))
    return found


def is_plan(path: Path) -> bool:
    return path.suffix.lower() in PLAN_SUFFIXES


def _plans_in(folder: Path, *, recursive: bool) -> list[Path]:
    if not folder.is_dir():
        raise PlanCollectionError("Dossier de plans introuvable.", file=folder)
    candidates = folder.rglob("*") if recursive else folder.glob("*")
    return [path for path in candidates if path.is_file() and is_plan(path)]
