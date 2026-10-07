import json
from datetime import UTC, datetime
from pathlib import Path
from typing import Any
from urllib.parse import parse_qs

import httpx
import pytest

from engine.core.errors import OutputWriteError
from engine.core.registry import discover_modules
from engine.core.settings import save_settings
from engine.mail import service
from engine.mail.graph import DeviceLogin, MailError, finish_device_login, start_device_login
from engine.mail.store import (
    ConversationStore,
    MailStoreError,
    Message,
    Participant,
    as_message,
    clean_subject,
    folder_id_of,
)
from engine.mail.tokens import MailSession, SessionStore

CLIENT_ID = "11111111-2222-3333-4444-555555555555"
MODULES = discover_modules()


def _message(
    identifier: str, conversation: str, received: str, subject: str, attachments: bool = False
) -> dict[str, Any]:
    return {
        "id": identifier,
        "conversationId": conversation,
        "subject": subject,
        "from": {"emailAddress": {"name": "Marc", "address": "marc@chantier.ch"}},
        "toRecipients": [{"emailAddress": {"name": "Léa", "address": "lea@facades.ch"}}],
        "receivedDateTime": received,
        "bodyPreview": "Bonjour",
        "hasAttachments": attachments,
        "body": {"contentType": "text", "content": "Bonjour,\nvoici le plan."},
        "webLink": "https://outlook.office.com/mail/x",
    }


class FakeMicrosoft:
    """Login endpoints and a tiny mailbox, served through a MockTransport."""

    def __init__(self) -> None:
        self.polls = 0
        self.downloads = 0
        self.mailbox_down = False
        self.served_at: list[datetime] = []
        self.messages = [
            _message("m1", "c1", "2026-10-01T08:00:00Z", "Façade nord"),
            _message("m2", "c1", "2026-10-02T09:00:00Z", "RE: Façade nord", attachments=True),
            _message("m3", "c2", "2026-10-03T10:00:00Z", "Soumission lot 4"),
        ]

    def transport(self) -> httpx.MockTransport:
        return httpx.MockTransport(self.handle)

    def handle(self, request: httpx.Request) -> httpx.Response:
        path = request.url.path
        if path.endswith("/devicecode"):
            return httpx.Response(
                200,
                json={
                    "device_code": "dev",
                    "user_code": "ABCD-EFGH",
                    "verification_uri": "https://microsoft.com/devicelogin",
                    "interval": 1,
                    "expires_in": 60,
                },
            )
        if path.endswith("/token"):
            form = parse_qs(request.content.decode())
            if form.get("grant_type") == ["refresh_token"]:
                return httpx.Response(
                    200, json={"access_token": "at2", "refresh_token": "rt2", "expires_in": 3600}
                )
            self.polls += 1
            if self.polls < 2:
                return httpx.Response(400, json={"error": "authorization_pending"})
            return httpx.Response(
                200, json={"access_token": "at", "refresh_token": "rt", "expires_in": 3600}
            )
        if path == "/v1.0/me":
            return httpx.Response(200, json={"mail": "lea@facades.ch"})
        if path == "/v1.0/me/messages":
            if self.mailbox_down:
                raise httpx.ConnectError("offline", request=request)
            self.served_at.append(datetime.now(UTC))
            return httpx.Response(200, json={"value": self.messages})
        if path.endswith("/attachments"):
            return httpx.Response(
                200,
                json={
                    "value": [
                        {
                            "id": "a1",
                            "name": "plan.dwg",
                            "size": 12,
                            "contentType": "application/x",
                        },
                        {"id": "a2", "name": "logo.png", "size": 5, "contentType": "image/png"},
                    ]
                },
            )
        if path.endswith("/$value"):
            self.downloads += 1
            return httpx.Response(200, content=b"DWG-CONTENT")
        return httpx.Response(404, json={"error": {"message": "inconnu"}})


@pytest.fixture
def settings(tmp_path: Path) -> Path:
    settings_file = tmp_path / "config" / "settings.json"
    save_settings(settings_file, {"mail": {"client_id": CLIENT_ID}}, MODULES)
    return settings_file


def test_device_login_polls_until_the_user_signed_in() -> None:
    fake = FakeMicrosoft()
    waited: list[float] = []

    login = start_device_login(CLIENT_ID, "common", fake.transport())
    tokens = finish_device_login(CLIENT_ID, "common", login, fake.transport(), sleep=waited.append)

    assert login.user_code == "ABCD-EFGH"
    assert tokens.refresh_token == "rt" and waited == [1.0]


def test_expired_device_code_is_explained() -> None:
    fake = FakeMicrosoft()
    fake.polls = -100
    login = DeviceLogin(device_code="dev", user_code="X", verification_uri="u", expires_in=0)

    with pytest.raises(MailError, match="expiré"):
        finish_device_login(CLIENT_ID, "common", login, fake.transport(), sleep=lambda _: None)


def test_connect_then_fetch_files_messages_by_conversation(settings: Path) -> None:
    fake = FakeMicrosoft()
    before = service.status(settings)
    assert before["configured"] and before["account"] is None

    login = service.connect_start(settings, fake.transport())
    service.connect_finish(settings, login, fake.transport())
    first = service.fetch(settings, fake.transport())
    second = service.fetch(settings, fake.transport())

    assert service.status(settings)["account"] == "lea@facades.ch"
    assert first == {"fetched": 3, "added": 3, "conversations": 2, "pruned": 0}
    assert second["added"] == 0
    listed = service.list_conversations(settings)["conversations"]
    assert [item["subject"] for item in listed] == ["Soumission lot 4", "Façade nord"]
    assert listed[1]["message_count"] == 2 and listed[1]["attachment_count"] == 2
    detail = service.read_conversation(settings, "c1")
    files = [attachment["file"] for attachment in detail["messages"][1]["attachments"]]
    assert files[0] is not None and Path(files[0]).read_bytes() == b"DWG-CONTENT"
    assert files[1] is None
    assert SessionStore(settings).read() is not None
    assert SessionStore(settings).read().refresh_token == "rt2"  # type: ignore[union-attr]


def test_export_and_remove_only_touch_the_local_folder(settings: Path, tmp_path: Path) -> None:
    fake = FakeMicrosoft()
    service.connect_finish(
        settings, service.connect_start(settings, fake.transport()), fake.transport()
    )
    service.fetch(settings, fake.transport())

    exported = Path(service.export_conversation(settings, "c1", tmp_path / "Chantier")["exported"])
    service.remove_conversation(settings, "c1")

    assert exported.name == "Façade nord"
    assert sorted(path.name for path in exported.iterdir()) == [
        "001 2026-10-01.md",
        "002 2026-10-02 plan.dwg",
        "002 2026-10-02.md",
    ]
    first_message = (exported / "001 2026-10-01.md").read_text(encoding="utf-8")
    assert "Marc <marc@chantier.ch>" in first_message
    remaining = service.list_conversations(settings)["conversations"]
    assert [item["id"] for item in remaining] == ["c2"]
    with pytest.raises(MailStoreError):
        service.read_conversation(settings, "c1")


def test_unconfigured_mailbox_is_refused(tmp_path: Path) -> None:
    with pytest.raises(MailError, match="pas configurée"):
        service.connect_start(tmp_path / "settings.json")
    with pytest.raises(MailError, match="Aucune boîte"):
        settings_file = tmp_path / "s" / "settings.json"
        save_settings(settings_file, {"mail": {"client_id": CLIENT_ID}}, MODULES)
        service.fetch(settings_file)


def test_unwritable_store_folder_is_a_readable_error_naming_the_file(tmp_path: Path) -> None:
    store = ConversationStore(tmp_path / "mail")
    store.register("c1")
    (store.folder / "conversations.json").mkdir()

    with pytest.raises(OutputWriteError, match="index") as index_error:
        store.rebuild_index()
    assert index_error.value.file == store.folder / "conversations.json"

    blocked = ConversationStore(tmp_path / "fichier")
    (tmp_path / "fichier").write_text("", encoding="utf-8")
    with pytest.raises(OutputWriteError, match="dossier") as register_error:
        blocked.register("c2")
    assert register_error.value.file is not None and register_error.value.hint is not None


def test_store_prunes_oldest_conversations_and_cleans_subjects(tmp_path: Path) -> None:
    store = ConversationStore(tmp_path / "mail")
    for index in range(3):
        conversation = f"c{index}"
        store.register(conversation)
        store.add_message(
            conversation,
            Message(
                id=f"m{index}",
                received_at=f"2026-10-0{index + 1}T08:00:00Z",
                sender=Participant(name="Marc", address="marc@chantier.ch"),
                subject=f"TR: RE: Sujet {index}",
            ),
        )
    store.rebuild_index()

    assert store.prune(2) == 1
    assert [item.subject for item in store.conversations()] == ["Sujet 2", "Sujet 1"]
    assert clean_subject("Fwd: re: Offre") == "Offre" and clean_subject("") == "(sans objet)"
    assert as_message({"id": "x", "receivedDateTime": "t"}).sender == Participant()
    assert json.loads((tmp_path / "mail" / "conversations.json").read_text(encoding="utf-8"))


def _connected(settings: Path, fake: FakeMicrosoft) -> None:
    service.connect_finish(
        settings, service.connect_start(settings, fake.transport()), fake.transport()
    )


def test_last_fetch_is_dated_before_the_download_not_after(settings: Path) -> None:
    fake = FakeMicrosoft()
    _connected(settings, fake)
    moments = iter([datetime(2026, 10, 7, 8, 0, 0, tzinfo=UTC)])

    service.fetch(settings, fake.transport(), clock=lambda: next(moments))

    session = SessionStore(settings).read()
    assert session is not None and session.last_fetch_at == "2026-10-07T08:00:00Z"
    assert service.status(settings)["last_fetch_at"] == "2026-10-07T08:00:00Z"


def test_rotated_refresh_token_is_kept_even_when_the_mailbox_is_unreachable(
    settings: Path,
) -> None:
    fake = FakeMicrosoft()
    _connected(settings, fake)
    fake.mailbox_down = True

    with pytest.raises(MailError, match="injoignable"):
        service.fetch(settings, fake.transport())

    session = SessionStore(settings).read()
    assert session is not None and session.refresh_token == "rt2"
    assert session.last_fetch_at is None


def test_stored_messages_do_not_download_their_attachments_again(settings: Path) -> None:
    fake = FakeMicrosoft()
    _connected(settings, fake)

    service.fetch(settings, fake.transport())
    service.fetch(settings, fake.transport())

    assert fake.downloads == 1


def test_offline_sign_in_is_a_readable_error() -> None:
    def offline(request: httpx.Request) -> httpx.Response:
        raise httpx.ConnectError("offline", request=request)

    with pytest.raises(MailError, match="injoignable"):
        start_device_login(CLIENT_ID, "common", httpx.MockTransport(offline))


def test_one_damaged_message_file_does_not_hide_the_conversation(tmp_path: Path) -> None:
    store = ConversationStore(tmp_path / "mail")
    store.register("c1")
    store.add_message(
        "c1",
        Message(id="m1", received_at="2026-10-01T08:00:00Z", sender=Participant(), subject="A"),
    )
    damaged = tmp_path / "mail" / folder_id_of("c1") / "messages" / "m2.json"
    damaged.write_text("pas du json", encoding="utf-8")

    assert [message.id for message in store.messages("c1")] == ["m1"]
    [conversation] = store.rebuild_index()
    assert conversation.message_count == 1


def test_windows_session_file_is_restricted_with_icacls(tmp_path: Path) -> None:
    commands: list[list[str]] = []

    def icacls(arguments: Any) -> bool:
        commands.append(list(arguments))
        return True

    store = SessionStore(tmp_path / "settings.json", acl=icacls)
    store.write(MailSession(account="lea@facades.ch", refresh_token="rt"))

    [command] = commands
    assert command[:4] == ["icacls", str(store.path), "/inheritance:r", "/grant:r"]
    assert command[4].endswith(":F")
    session = store.read()
    assert session is not None and session.protected


def test_failed_acl_is_remembered_and_surfaced_in_the_status(settings: Path) -> None:
    store = SessionStore(settings, acl=lambda _: False)

    store.write(MailSession(account="lea@facades.ch", refresh_token="rt"))

    session = store.read()
    assert session is not None and not session.protected
    assert "restreints" in str(service.status(settings)["protection_hint"])
