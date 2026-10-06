import sys
import traceback
from collections.abc import Callable, Iterator, Sequence
from concurrent.futures import Future, ProcessPoolExecutor, as_completed
from dataclasses import dataclass, field
from pathlib import Path

from engine.core.errors import EngineError
from engine.core.events import Emit, ProgressEvent, WarningEvent
from engine.core.i18n import current_language, set_language
from engine.core.messages import t

UNEXPECTED_ITEM_ERROR = t("batch.unexpected_item_error")
INLINE_BATCH_SIZE = 1

type Completed[ResultT] = Iterator[tuple[Path, ResultT | Exception]]


@dataclass(frozen=True)
class BatchFailure:
    path: Path
    message: str


@dataclass(frozen=True)
class BatchOutcome[ResultT]:
    results: list[tuple[Path, ResultT]] = field(default_factory=list)
    failures: list[BatchFailure] = field(default_factory=list)


def process_batch[ResultT](
    paths: Sequence[Path],
    worker: Callable[[Path], ResultT],
    *,
    batch_size: int,
    emit: Emit,
    label: str,
) -> BatchOutcome[ResultT]:
    """Runs `worker` on every file; a failing file is reported and never stops the others.

    In parallel mode `worker` must be picklable (a module-level function).
    """
    if batch_size <= INLINE_BATCH_SIZE or len(paths) <= 1:
        completed = _run_inline(paths, worker)
    else:
        completed = _run_in_pool(paths, worker, batch_size)
    return _collect(paths, completed, emit, label)


def _run_inline[ResultT](
    paths: Sequence[Path], worker: Callable[[Path], ResultT]
) -> Completed[ResultT]:
    for path in paths:
        try:
            yield path, worker(path)
        except Exception as error:
            yield path, error


def _run_in_pool[ResultT](
    paths: Sequence[Path], worker: Callable[[Path], ResultT], batch_size: int
) -> Completed[ResultT]:
    # Spawned workers import everything afresh: they must inherit the language of this run.
    with ProcessPoolExecutor(
        max_workers=batch_size, initializer=set_language, initargs=(current_language(),)
    ) as pool:
        futures: dict[Future[ResultT], Path] = {pool.submit(worker, path): path for path in paths}
        for future in as_completed(futures):
            error = future.exception()
            if isinstance(error, Exception):
                yield futures[future], error
            else:
                yield futures[future], future.result()


def _collect[ResultT](
    paths: Sequence[Path], completed: Completed[ResultT], emit: Emit, label: str
) -> BatchOutcome[ResultT]:
    total = max(len(paths), 1)
    by_path: dict[Path, ResultT] = {}
    failures: list[BatchFailure] = []
    for done, (path, value) in enumerate(completed, start=1):
        if isinstance(value, Exception):
            failures.append(_report_failure(path, value, emit))
        else:
            by_path[path] = value
        message = t("batch.progress", label=label, name=path.name)
        emit(ProgressEvent(current=done, total=total, message=message))
    results = [(path, by_path[path]) for path in paths if path in by_path]
    return BatchOutcome(results=results, failures=failures)


def _report_failure(path: Path, error: Exception, emit: Emit) -> BatchFailure:
    if isinstance(error, EngineError):
        message, hint = error.message, error.hint
    else:
        traceback.print_exception(error, file=sys.stderr)
        message, hint = UNEXPECTED_ITEM_ERROR, t("batch.unexpected_item_hint")
    emit(WarningEvent(message=message, file=str(path), hint=hint))
    return BatchFailure(path=path, message=message)
