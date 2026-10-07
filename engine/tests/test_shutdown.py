import io
import os
import subprocess
import sys
import threading
import time
from collections.abc import Callable
from pathlib import Path

import pytest

from engine.core.batch import process_batch
from engine.core.shutdown import (
    EXIT_CANCELLED,
    ShutdownHooks,
    exit_when_stdin_closes,
    hooks,
    pipe_is_held_open,
    watch_parent,
    watch_stdin,
)
from engine.testing.processes import is_running, sleep_long

WAIT_SECONDS = 15.0
POLL_SECONDS = 0.1
WORKER_START_SECONDS = 0.5

ORPHANED_WORKER = f"""
import os, time
from concurrent.futures import ProcessPoolExecutor
from engine.core.batch import prepare_worker

pool = ProcessPoolExecutor(max_workers=1, initializer=prepare_worker, initargs=("fr",))
pid = pool.submit(os.getpid).result()
pool.submit(time.sleep, {WAIT_SECONDS * 4})
time.sleep({WORKER_START_SECONDS})
print(pid, flush=True)
os._exit(0)
"""

GUARDED_SLEEP = f"""
import time
from engine.core.shutdown import exit_when_stdin_closes

exit_when_stdin_closes()
time.sleep({WAIT_SECONDS * 4})
"""


HOOKED_SLEEP = f"""
import sys, time
from engine.core.shutdown import exit_when_stdin_closes, hooks

with hooks.registered(lambda: print("hook", flush=True)):
    exit_when_stdin_closes()
    print("ready", flush=True)
    time.sleep({WAIT_SECONDS * 4})
"""
CANCEL_REQUEST = b"cancel\n"


def _wait_until(condition: Callable[[], bool], seconds: float = WAIT_SECONDS) -> bool:
    deadline = time.monotonic() + seconds
    while time.monotonic() < deadline:
        if condition():
            return True
        time.sleep(POLL_SECONDS)
    return condition()


def test_hooks_run_innermost_first_and_only_while_registered() -> None:
    registry = ShutdownHooks()
    calls: list[str] = []

    with registry.registered(lambda: calls.append("pool")):
        with registry.registered(lambda: calls.append("oda")):
            registry.trigger()
        registry.trigger()
    registry.trigger()

    assert calls == ["oda", "pool", "pool"]


def test_a_failing_hook_does_not_stop_the_others(capsys: pytest.CaptureFixture[str]) -> None:
    registry = ShutdownHooks()
    calls: list[str] = []

    def failing() -> None:
        raise RuntimeError("déjà fermé")

    with registry.registered(lambda: calls.append("outer")), registry.registered(failing):
        registry.trigger()

    assert calls == ["outer"]
    assert "déjà fermé" in capsys.readouterr().err


def test_stdin_guard_fires_once_the_writer_closes_the_pipe() -> None:
    read_end, write_end = os.pipe()
    closed = threading.Event()

    with os.fdopen(read_end, "rb") as stream:
        watch_stdin(stream, closed.set)
        assert not closed.wait(POLL_SECONDS)
        os.close(write_end)
        assert closed.wait(WAIT_SECONDS)


def test_stdin_guard_fires_when_the_app_writes_a_cancel() -> None:
    read_end, write_end = os.pipe()
    stopped = threading.Event()

    try:
        with os.fdopen(read_end, "rb") as stream:
            watch_stdin(stream, stopped.set)
            assert not stopped.wait(POLL_SECONDS)
            os.write(write_end, CANCEL_REQUEST)
            assert stopped.wait(WAIT_SECONDS)
    finally:
        os.close(write_end)


def test_stdin_guard_ignores_a_stream_that_cannot_be_read() -> None:
    closed = threading.Event()

    class Unreadable(io.BytesIO):
        def read(self, size: int | None = -1) -> bytes:
            raise OSError("reading from stdin while output is captured")

    thread = watch_stdin(Unreadable(), closed.set)
    thread.join(WAIT_SECONDS)

    assert not thread.is_alive() and not closed.is_set()


def test_pipe_is_held_open_only_while_the_writer_lives() -> None:
    read_end, write_end = os.pipe()
    try:
        assert pipe_is_held_open(read_end)
        os.close(write_end)
        assert not pipe_is_held_open(read_end)
    finally:
        os.close(read_end)


def test_a_cancel_written_before_the_guard_still_counts_as_held_open() -> None:
    read_end, write_end = os.pipe()
    try:
        os.write(write_end, CANCEL_REQUEST)
        assert pipe_is_held_open(read_end)
    finally:
        os.close(read_end)
        os.close(write_end)


def test_guard_watches_only_a_pipe_held_open() -> None:
    read_end, write_end = os.pipe()
    closed = threading.Event()
    with os.fdopen(read_end, "r") as stream:
        thread = exit_when_stdin_closes(stream, closed.set)
        assert thread is not None
        os.close(write_end)
        assert closed.wait(WAIT_SECONDS)

    assert exit_when_stdin_closes(io.StringIO(), closed.set) is None


def test_parent_guard_fires_when_the_parent_is_gone() -> None:
    gone = threading.Event()
    dead = threading.Event()

    class FakeParent:
        def join(self, timeout: float | None = None) -> None:
            gone.wait(WAIT_SECONDS)

    watch_parent(FakeParent(), dead.set)
    assert not dead.wait(POLL_SECONDS)
    gone.set()

    assert dead.wait(WAIT_SECONDS)


def test_engine_run_exits_when_the_app_closes_its_stdin() -> None:
    process = subprocess.Popen(
        [sys.executable, "-c", GUARDED_SLEEP],
        stdin=subprocess.PIPE,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.PIPE,
    )
    assert process.stdin is not None
    time.sleep(WORKER_START_SECONDS)
    process.stdin.close()

    assert process.wait(WAIT_SECONDS) == EXIT_CANCELLED, process.stderr


def test_engine_run_runs_its_hooks_and_exits_when_the_app_writes_a_cancel() -> None:
    process = subprocess.Popen(
        [sys.executable, "-c", HOOKED_SLEEP],
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    assert process.stdin is not None and process.stdout is not None
    try:
        assert process.stdout.readline() == b"ready\n"
        process.stdin.write(CANCEL_REQUEST)
        process.stdin.flush()

        assert process.wait(WAIT_SECONDS) == EXIT_CANCELLED, process.stderr
        assert process.stdout.read() == b"hook\n"
    finally:
        process.stdin.close()
        process.kill()


def test_pool_workers_die_with_their_parent() -> None:
    completed = subprocess.run(
        [sys.executable, "-c", ORPHANED_WORKER],
        capture_output=True,
        text=True,
        check=True,
        timeout=WAIT_SECONDS * 2,
    )
    worker_pid = int(completed.stdout.strip())

    assert _wait_until(lambda: not is_running(worker_pid)), "worker survived its parent"


def test_triggering_the_hooks_kills_the_running_pool(tmp_path: Path) -> None:
    paths = [tmp_path / "a.txt", tmp_path / "b.txt"]
    outcome: list[object] = []

    def run_batch() -> None:
        try:
            outcome.append(
                process_batch(paths, sleep_long, batch_size=2, emit=lambda _: None, label="x")
            )
        except BaseException as error:
            # Whatever the pool raises once killed is the expected outcome here.
            outcome.append(error)

    thread = threading.Thread(target=run_batch, daemon=True)
    started = time.monotonic()
    thread.start()
    time.sleep(WORKER_START_SECONDS * 4)
    hooks.trigger()
    thread.join(WAIT_SECONDS)

    assert not thread.is_alive()
    assert time.monotonic() - started < WAIT_SECONDS
