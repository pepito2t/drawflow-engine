import json
import sys
from collections.abc import Sequence
from pathlib import Path

import anyio
import httpx
import pytest
from httpx import MockTransport

from engine.assistant.errors import AssistantError
from engine.core.errors import EngineError, InvalidInputError
from engine.core.events import Event
from engine.core.settings import load_general_settings
from engine.setup.actions import SetupContext, SetupError, run_action
from engine.setup.commands import CommandOutcome, run_command, start_detached
from engine.setup.installer_download import InstallerDownloadError
from engine.setup.ollama import delete_model, installed_sizes, pull_model
from engine.testing.fake_machine import LOCALAPPDATA, PROGRAM_FILES, FakeMachine

ODA = PROGRAM_FILES / "ODA" / "ODAFileConverter 26.4.0" / "ODAFileConverter.exe"
OLLAMA_APP = LOCALAPPDATA / "Programs" / "Ollama" / "ollama app.exe"
NO_WAIT = 0.05


SIGNED_BY_ODA = "Valid\nCN=Open Design Alliance, O=Open Design Alliance"
SIGNED_BY_OLLAMA = "Valid\nCN=Ollama Inc, O=Ollama Inc"


class Recorder:
    def __init__(
        self,
        machine: FakeMachine,
        code: int = 0,
        installs: Path | None = None,
        signature: str = SIGNED_BY_ODA,
    ) -> None:
        self.machine = machine
        self.code = code
        self.installs = installs
        self.signature = signature
        self.commands: list[list[str]] = []

    def run(self, arguments: Sequence[str]) -> CommandOutcome:
        self.commands.append(list(arguments))
        if arguments[0] == "powershell":
            return CommandOutcome(0, self.signature)
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


def _oda_site(status: int = 200) -> httpx.MockTransport:
    return httpx.MockTransport(lambda _: httpx.Response(status, content=b"msi"))


def test_oda_install_downloads_the_official_msi_then_configures_it(tmp_path: Path) -> None:
    recorder = Recorder(FakeMachine(), installs=ODA)
    events: list[Event] = []

    run_action("oda.install", context(tmp_path, recorder, events, _oda_site()))

    assert recorder.commands[0][0] == "powershell"
    assert recorder.commands[1][:2] == ["msiexec", "/i"]
    assert recorder.commands[1][2].endswith(".msi")
    assert load_general_settings(tmp_path / "settings.json").oda_converter_path == ODA
    assert events[-1].type == "result"


def test_oda_install_does_not_depend_on_winget(tmp_path: Path) -> None:
    recorder = Recorder(FakeMachine(programs=set()), installs=ODA)

    run_action("oda.install", context(tmp_path, recorder, [], _oda_site()))

    assert all(command[0] != "winget" for command in recorder.commands)


def test_oda_removed_from_the_site_points_to_the_download_page(tmp_path: Path) -> None:
    recorder = Recorder(FakeMachine())

    with pytest.raises(InstallerDownloadError, match="HTTP 404") as caught:
        run_action("oda.install", context(tmp_path, recorder, [], _oda_site(404)))
    assert caught.value.hint is not None
    assert "Page de téléchargement" in caught.value.hint
    assert recorder.commands == []


def test_oda_install_is_windows_only(tmp_path: Path) -> None:
    with pytest.raises(SetupError, match="Windows"):
        run_action("oda.install", context(tmp_path, Recorder(FakeMachine(os="macos")), []))


def _ollama_site(request: httpx.Request) -> httpx.Response:
    if request.url.path.endswith("OllamaSetup.exe"):
        return httpx.Response(200, content=b"setup")
    return httpx.Response(200, json={"version": "0.12.0"})


def test_windows_installs_ollama_from_its_own_setup_then_starts_it(tmp_path: Path) -> None:
    recorder = Recorder(FakeMachine(programs={"ollama"}), signature=SIGNED_BY_OLLAMA)
    events: list[Event] = []

    run_action("ollama.install", context(tmp_path, recorder, events, MockTransport(_ollama_site)))

    assert recorder.commands[0][0] == "powershell"
    setup, *flags = recorder.commands[1]
    assert setup.endswith("OllamaSetup.exe")
    assert "/VERYSILENT" in flags
    assert recorder.commands[2] == ["ollama", "serve"]
    assert any(event.type == "progress" for event in events)
    assert events[-1].type == "result"


def test_failed_install_explains_with_the_end_of_the_installer_output(tmp_path: Path) -> None:
    recorder = Recorder(FakeMachine(), code=1, signature=SIGNED_BY_OLLAMA)

    with pytest.raises(EngineError, match="a échoué") as caught:
        run_action("ollama.install", context(tmp_path, recorder, [], MockTransport(_ollama_site)))
    assert caught.value.hint is not None
    assert "0x80070005" in caught.value.hint


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


def test_model_pull_downloads_and_remembers_the_recommended_model(tmp_path: Path) -> None:
    pulled: list[str] = []

    def handle(request: httpx.Request) -> httpx.Response:
        if request.url.path.endswith("/pull"):
            pulled.append(str(json.loads(request.content)["model"]))
        return httpx.Response(200, content=json.dumps({"status": "success"}).encode())

    recorder = Recorder(FakeMachine(memory=8_000_000_000))
    setup = context(tmp_path, recorder, [], httpx.MockTransport(handle))

    run_action("model.pull", setup)

    assert pulled == ["qwen3.5:4b"]
    stored = json.loads(setup.settings.read_text(encoding="utf-8"))["assistant"]["model"]
    assert stored == "qwen3.5:4b"


def test_model_pull_error_is_readable(tmp_path: Path) -> None:
    server = _pull_server({"error": "pull model manifest: file does not exist"})

    with pytest.raises(AssistantError, match="file does not exist"):
        run_action("model.pull", context(tmp_path, Recorder(FakeMachine()), [], server))


def test_unknown_action_is_refused(tmp_path: Path) -> None:
    with pytest.raises(InvalidInputError):
        run_action("rm -rf", context(tmp_path, Recorder(FakeMachine()), []))


def test_unreadable_pull_progress_is_a_readable_error() -> None:
    garbage = httpx.MockTransport(lambda _: httpx.Response(200, content=b"not json\n"))

    with pytest.raises(AssistantError, match="illisible"):
        anyio.run(pull_model, "http://127.0.0.1:11434/v1", "qwen3:4b", lambda *_: None, garbage)


def test_deleting_a_model_while_ollama_is_down_is_a_readable_error() -> None:
    def refuse(_: httpx.Request) -> httpx.Response:
        raise httpx.ConnectError("refused")

    with pytest.raises(AssistantError, match="ne répond pas"):
        anyio.run(
            delete_model, "http://127.0.0.1:11434/v1", "qwen3:4b", httpx.MockTransport(refuse)
        )


def test_listing_models_while_ollama_goes_down_is_a_readable_error() -> None:
    def refuse(_: httpx.Request) -> httpx.Response:
        raise httpx.ConnectError("refused")

    with pytest.raises(AssistantError, match="ne répond plus") as caught:
        anyio.run(installed_sizes, "http://127.0.0.1:11434/v1", httpx.MockTransport(refuse))
    assert caught.value.hint is not None


def test_missing_program_and_timeout_are_readable_setup_errors(tmp_path: Path) -> None:
    with pytest.raises(SetupError, match="Impossible de lancer"):
        run_command([str(tmp_path / "absent-installer.exe")])
    with pytest.raises(SetupError, match="absent-installer"):
        start_detached([str(tmp_path / "absent-installer.exe")])
    with pytest.raises(SetupError, match="ne s'est pas terminé"):
        run_command([sys.executable, "-c", "import time; time.sleep(30)"], timeout_seconds=0.2)
