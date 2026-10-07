import sys
import traceback
from collections.abc import Callable, Iterator, Sequence
from concurrent.futures import Future, ProcessPoolExecutor, as_completed
from dataclasses import dataclass, field
from functools import partial
from pathlib import Path

from engine.core.diagnostics import record_failure
from engine.core.errors import EngineError
from engine.core.events import Emit, ProgressEvent, WarningEvent
from engine.core.i18n import Language, current_language, set_language
from engine.core.messages import t
from engine.core.shutdown import exit_when_parent_dies, hooks

UNEXPECTED_ITEM_ERROR = t("batch.unexpected_item_error")
INLINE_BATCH_SIZE = 1
BATCH_LOG_COMMAND = "batch"

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
    settings_file: Path | None = None,
) -> BatchOutcome[ResultT]:
    """Runs `worker` on every file; a failing file is reported and never stops the others.

    In parallel mode `worker` must be picklable (a module-level function).
    Unexpected failures are kept in the diagnostics log next to `settings_file`.
    """
    if batch_size <= INLINE_BATCH_SIZE or len(paths) <= 1:
        completed = _run_inline(paths, worker)
    else:
        completed = _run_in_pool(paths, worker, batch_size)
    return _collect(paths, completed, emit, label, settings_file)


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
    with (
        ProcessPoolExecutor(
            max_workers=batch_size, initializer=prepare_worker, initargs=(current_language(),)
        ) as pool,
        hooks.registered(partial(_stop_pool, pool)),
    ):
        futures: dict[Future[ResultT], Path] = {pool.submit(worker, path): path for path in paths}
        for future in as_completed(futures):
            error = future.exception()
            if isinstance(error, Exception):
                yield futures[future], error
            else:
                yield futures[future], future.result()


def prepare_worker(language: Language) -> None:
    """Spawned workers import everything afresh: they inherit the run's language and its end."""
    set_language(language)
    exit_when_parent_dies()


def _stop_pool(pool: ProcessPoolExecutor) -> None:
    # The executor forgets its processes on shutdown: take them first, kill them after.
    processes = list(pool._processes.values())
    pool.shutdown(wait=False, cancel_futures=True)
    for process in processes:
        process.kill()


def _collect[ResultT](
    paths: Sequence[Path],
    completed: Completed[ResultT],
    emit: Emit,
    label: str,
    settings_file: Path | None,
) -> BatchOutcome[ResultT]:
    total = max(len(paths), 1)
    by_path: dict[Path, ResultT] = {}
    failures: list[BatchFailure] = []
    for done, (path, value) in enumerate(completed, start=1):
        if isinstance(value, Exception):
            failures.append(_report_failure(path, value, emit, settings_file))
        else:
            by_path[path] = value
        message = t("batch.progress", label=label, name=path.name)
        emit(ProgressEvent(current=done, total=total, message=message))
    results = [(path, by_path[path]) for path in paths if path in by_path]
    return BatchOutcome(results=results, failures=failures)


def _report_failure(
    path: Path, error: Exception, emit: Emit, settings_file: Path | None
) -> BatchFailure:
    if isinstance(error, EngineError):
        message, hint = error.message, error.hint
    else:
        traceback.print_exception(error, file=sys.stderr)
        record_failure(settings_file, [_log_command(path)], error)
        message, hint = UNEXPECTED_ITEM_ERROR, t("batch.unexpected_item_hint")
    emit(WarningEvent(message=message, file=str(path), hint=hint))
    return BatchFailure(path=path, message=message)


def _log_command(path: Path) -> str:
    return f"{BATCH_LOG_COMMAND} {path}"
