"""Stops the work in flight when the other side goes away.

The app may die while a run is in progress: the sidecar notices its stdin closing, a worker
notices its parent dying. Whoever notices runs the registered hooks (pool, ODA command, output
being written) from its own thread, then exits the process at once.
"""

import multiprocessing
import os
import select
import stat
import sys
import threading
import traceback
from collections.abc import Callable, Iterator
from contextlib import contextmanager
from functools import partial
from typing import IO, Protocol, TextIO

Hook = Callable[[], None]
EXIT_CANCELLED = 3
ORPHAN_WORKER_EXIT_CODE = 0
READ_CHUNK_BYTES = 4096
STDIN_GUARD_NAME = "stdin-guard"
PARENT_GUARD_NAME = "parent-guard"


class Joinable(Protocol):
    def join(self, timeout: float | None = None) -> None: ...


class ShutdownHooks:
    """What to stop, innermost first; a failing hook does not prevent the next one."""

    def __init__(self) -> None:
        self._hooks: dict[int, Hook] = {}
        self._next_token = 0
        self._lock = threading.Lock()

    @contextmanager
    def registered(self, hook: Hook) -> Iterator[None]:
        with self._lock:
            token = self._next_token
            self._next_token += 1
            self._hooks[token] = hook
        try:
            yield
        finally:
            with self._lock:
                self._hooks.pop(token, None)

    def trigger(self) -> None:
        with self._lock:
            hooks = list(self._hooks.values())
        for hook in reversed(hooks):
            try:
                hook()
            except Exception:
                # Shutting down: nobody is left to report to but stderr.
                traceback.print_exc(file=sys.stderr)


# One registry per process: the pool, the ODA command and the output being written register here
# so that the thread noticing the shutdown can stop them all.
hooks = ShutdownHooks()


def stop_process(exit_code: int) -> None:
    hooks.trigger()
    os._exit(exit_code)


def watch_stdin(stream: IO[bytes], on_close: Hook) -> threading.Thread:
    """The read returns nothing once the other end closed the pipe or died."""

    def wait() -> None:
        try:
            while stream.read(READ_CHUNK_BYTES):
                pass
        except (OSError, ValueError):
            return
        on_close()

    thread = threading.Thread(target=wait, name=STDIN_GUARD_NAME, daemon=True)
    thread.start()
    return thread


def watch_parent(parent: Joinable, on_dead: Hook) -> threading.Thread:
    def wait() -> None:
        parent.join()
        on_dead()

    thread = threading.Thread(target=wait, name=PARENT_GUARD_NAME, daemon=True)
    thread.start()
    return thread


def exit_when_stdin_closes(
    stream: TextIO | None = None, on_close: Hook | None = None
) -> threading.Thread | None:
    """Only a pipe the app still holds open is watched: a terminal, /dev/null or a pipe already
    closed at start (CI, scripts) mean nobody will ever cancel this way."""
    stream = sys.stdin if stream is None else stream
    if stream is None:
        return None
    try:
        descriptor = stream.fileno()
        held_open = stat.S_ISFIFO(os.fstat(descriptor).st_mode) and pipe_is_held_open(descriptor)
    except (OSError, ValueError):
        return None
    if not held_open:
        return None
    return watch_stdin(stream.buffer, on_close or partial(stop_process, EXIT_CANCELLED))


def exit_when_parent_dies() -> threading.Thread | None:
    parent = multiprocessing.parent_process()
    if parent is None:
        return None
    return watch_parent(parent, lambda: stop_process(ORPHAN_WORKER_EXIT_CODE))


def pipe_is_held_open(descriptor: int) -> bool:
    """False once the writer is gone: the pipe then reads as ended straight away."""
    if sys.platform == "win32":
        import _winapi
        import msvcrt

        try:
            _winapi.PeekNamedPipe(msvcrt.get_osfhandle(descriptor))
        except OSError:
            return False
        return True
    readable, _, _ = select.select([descriptor], [], [], 0)
    return not readable
