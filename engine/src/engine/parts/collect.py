from collections.abc import Sequence
from pathlib import Path

from engine.core.collect import collect_files
from engine.core.events import Emit
from engine.parts.messages import t

PLAN_SUFFIXES = frozenset({".dwg", ".dxf"})
PLAN_KIND = t("collect.plan_kind")


def collect_plans(
    files: Sequence[Path], folders: Sequence[Path], *, recursive: bool, emit: Emit
) -> list[Path]:
    return collect_files(
        files, folders, suffixes=PLAN_SUFFIXES, kind=PLAN_KIND, recursive=recursive, emit=emit
    )
