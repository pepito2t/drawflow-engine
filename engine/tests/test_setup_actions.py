import json
from collections.abc import Sequence
from pathlib import Path

import httpx
import pytest

from engine.assistant.errors import AssistantError
from engine.core.errors import InvalidInputError
from engine.core.events import Event
from engine.core.settings import load_general_settings
from engine.setup.actions import SetupContext, SetupError, run_action
from engine.setup.commands import CommandOutcome
from engine.testing.fake_machine import LOCALAPPDATA, PROGRAM_FILES, FakeMachine

ODA = PROGRAM_FILES / "ODA" / "ODAFileConverter 26.4.0" / "ODAFileConverter.exe"
OLLAMA_APP = LOCALAPPDATA / "Programs" / "Ollama" / "ollama app.exe"
WINGET_ALREADY_INSTALLED = 0x8A150061
NO_WAIT = 0.05


class Recorder:
    def __init__(self, machine: FakeMachine, code: int = 0, installs: Path | None = None) -> None:
        self.machine = machine
        self.code = code
        self.installs = installs
        self.commands: list[list[str]] = []

    def run(self, arguments: Sequence[str]) -> CommandOutcome:
        self.commands.append(list(arguments))
        if self.installs is not None:
            self.machine.files.add(self.installs)
        return CommandOutcome(self.code, "Téléchargement…\nÉchec de l'installation : 0x80070005")

    def start(self, arguments: Sequence[str]) -> None:
        self.commands.append(list(arguments))


def context(
    tmp_path: Path,
    recorder: Recorder,
    events: list[Event],
    transport: httpx.AsyncBaseTransport | None = None,
) -> SetupContext:
    return SetupContext(
        settings=tmp_path / "settings.json",
        emit=events.append,
        machine=recorder.machine,
        run=recorder.run,
        start=recorder.start,
        transport=transport,
        start_wait_seconds=NO_WAIT,
    )


def test_oda_install_uses_winget_then_configures_the_detected_path(tmp_path: Path) -> None:
    recorder = Recorder(FakeMachine(programs={"winget"}), installs=ODA)
    events: list[Event] = []

    run_action("oda.install", context(tmp_path, recorder, events))

    assert recorder.commands[0][:4] == ["winget", "install", "--id", "ODA.ODAFileConverter"]
    assert "--accept-package-agreements" in recorder.commands[0]
    assert load_general_settings(tmp_path / "settings.json").oda_converter_path == ODA
    assert events[-1].type == "result"


def test_already_installed_package_is_not_a_failure(tmp_path: Path) -> None:
    machine = FakeMachine(programs={"winget"}, files={ODA})
    recorder = Recorder(machine, code=WINGET_ALREADY_INSTALLED)

    run_action("oda.install", context(tmp_path, recorder, []))

    assert load_general_settings(tmp_path / "settings.json").oda_converter_path == ODA


def test_failed_install_explains_with_the_end_of_the_installer_output(tmp_path: Path) -> None:
    recorder = Recorder(FakeMachine(programs={"winget"}), code=1)

    with pytest.raises(SetupError, match="a échoué") as caught:
        run_action("ollama.install", context(tmp_path, recorder, []))
    assert caught.value.hint is not None
    assert "0x80070005" in caught.value.hint


def test_install_without_winget_points_to_the_download_page(tmp_path: Path) -> None:
    with pytest.raises(SetupError, match="winget"):
        run_action("oda.install", context(tmp_path, Recorder(FakeMachine()), []))


def test_macos_installs_ollama_with_homebrew(tmp_path: Path) -> None:
    machine = FakeMachine(os="macos", programs={"brew", "ollama"})
    recorder = Recorder(machine)
    ollama_up = httpx.MockTransport(lambda _: httpx.Response(200, json={"version": "0.12.0"}))

    run_action("ollama.install", context(tmp_path, recorder, [], ollama_up))

    assert recorder.commands == [["brew", "install", "--cask", "ollama"], ["ollama", "serve"]]


def test_start_launches_the_ollama_app_and_waits_for_it(tmp_path: Path) -> None:
    recorder = Recorder(FakeMachine(files={OLLAMA_APP}))
    events: list[Event] = []
    ollama_up = httpx.MockTransport(lambda _: httpx.Response(200, json={"version": "0.12.0"}))

    run_action("ollama.start", context(tmp_path, recorder, events, ollama_up))

    assert recorder.commands == [[str(OLLAMA_APP)]]
    assert events[-1].type == "result"


def test_start_reports_a_server_that_never_comes_up(tmp_path: Path) -> None:
    recorder = Recorder(FakeMachine(files={OLLAMA_APP}))

    def refuse(request: httpx.Request) -> httpx.Response:
        raise httpx.ConnectError("refused", request=request)

    down = httpx.MockTransport(refuse)

    with pytest.raises(SetupError, match="ne répond pas"):
        run_action("ollama.start", context(tmp_path, recorder, [], down))


def _pull_server(*updates: dict[str, object]) -> httpx.MockTransport:
    body = "\n".join(json.dumps(update) for update in updates).encode()
    return httpx.MockTransport(lambda _: httpx.Response(200, content=body))


def test_model_pull_reports_download_progress(tmp_path: Path) -> None:
    events: list[Event] = []
    server = _pull_server(
        {"status": "pulling manifest"},
        {"status": "downloading", "total": 4000, "completed": 1000},
        {"status": "downloading", "total": 4000, "completed": 4000},
        {"status": "success"},
    )

    run_action("model.pull", context(tmp_path, Recorder(FakeMachine()), events, server))

    progress = [(event.current, event.total) for event in events if event.type == "progress"]
    assert progress == [(25, 100), (100, 100)]
    assert events[-1].type == "result"


def test_model_pull_error_is_readable(tmp_path: Path) -> None:
    server = _pull_server({"error": "pull model manifest: file does not exist"})

    with pytest.raises(AssistantError, match="file does not exist"):
        run_action("model.pull", context(tmp_path, Recorder(FakeMachine()), [], server))


def test_unknown_action_is_refused(tmp_path: Path) -> None:
    with pytest.raises(InvalidInputError):
        run_action("rm -rf", context(tmp_path, Recorder(FakeMachine()), []))
