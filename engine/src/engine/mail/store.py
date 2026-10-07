"""Conversations kept on this computer: one folder each, with messages and attachments."""

import hashlib
import json
import re
import shutil
from pathlib import Path
from typing import Any

from pydantic import BaseModel, ConfigDict, Field, ValidationError

from engine.core.errors import EngineError, OutputWriteError
from engine.core.json_files import write_json_atomically
from engine.mail.messages import t

INDEX_FILE = "conversations.json"
CONVERSATION_FILE = "conversation.json"
MESSAGES_FOLDER = "messages"
ATTACHMENTS_FOLDER = "attachments"
FOLDER_ID_LENGTH = 16
MAX_NAME_LENGTH = 60
UNSAFE_NAME_CHARACTERS = re.compile(r'[<>:"/\\|?*\x00-\x1f]+')
SUBJECT_PREFIXES = re.compile(r"^\s*((re|tr|fw|fwd|aw|wg)\s*:\s*)+", re.IGNORECASE)


class MailStoreError(EngineError):
    pass


class Participant(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    name: str = ""
    address: str = ""


class Attachment(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    name: str
    size: int = 0
    content_type: str = ""
    file: str | None = None


class Message(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    id: str
    received_at: str
    sender: Participant
    recipients: list[Participant] = Field(default_factory=list)
    subject: str = ""
    preview: str = ""
    body: str = ""
    attachments: list[Attachment] = Field(default_factory=list)
    web_link: str | None = None


class Conversation(BaseModel):
    model_config = ConfigDict(extra="forbid")

    id: str
    subject: str
    participants: list[Participant] = Field(default_factory=list)
    first_received_at: str
    last_received_at: str
    message_count: int = 0
    attachment_count: int = 0
    project: str | None = None
    category: str | None = None


def folder_id_of(conversation_id: str) -> str:
    return hashlib.sha256(conversation_id.encode("utf-8")).hexdigest()[:FOLDER_ID_LENGTH]


def clean_subject(subject: str) -> str:
    return SUBJECT_PREFIXES.sub("", subject).strip() or t("store.no_subject")


def safe_name(text: str) -> str:
    cleaned = UNSAFE_NAME_CHARACTERS.sub(" ", text).strip(" .")
    return (cleaned or t("store.no_name"))[:MAX_NAME_LENGTH].rstrip(" .")


class ConversationStore:
    def __init__(self, folder: Path) -> None:
        self.folder = folder

    def conversations(self) -> list[Conversation]:
        path = self.folder / INDEX_FILE
        if not path.is_file():
            return []
        try:
            raw = json.loads(path.read_text(encoding="utf-8"))
            listed = [Conversation.model_validate(item) for item in raw]
        except (OSError, json.JSONDecodeError, TypeError, ValidationError) as error:
            raise MailStoreError(
                t("store.index_unreadable"), file=path, hint=t("store.index_unreadable.hint")
            ) from error
        return sorted(listed, key=lambda item: item.last_received_at, reverse=True)

    def conversation(self, conversation_id: str) -> Conversation:
        for conversation in self.conversations():
            if conversation.id == conversation_id:
                return conversation
        raise MailStoreError(t("store.conversation_gone"))

    def messages(self, conversation_id: str) -> list[Message]:
        return self._messages_in(self._folder(conversation_id))

    def has_message(self, conversation_id: str, message_id: str) -> bool:
        return self._message_path(conversation_id, message_id).is_file()

    def add_message(self, conversation_id: str, message: Message) -> bool:
        """Returns False when the message was already stored."""
        path = self._message_path(conversation_id, message.id)
        if path.is_file():
            return False
        try:
            write_json_atomically(path, message.model_dump(mode="json"))
        except OSError as error:
            raise OutputWriteError(t("store.message_save_failed"), file=path) from error
        return True

    def attachment_path(self, conversation_id: str, message_id: str, name: str) -> Path:
        folder = self._folder(conversation_id) / ATTACHMENTS_FOLDER / safe_name(message_id)
        return folder / safe_name(name)

    def write_attachment(self, path: Path, content: bytes) -> None:
        try:
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes(content)
        except OSError as error:
            raise OutputWriteError(t("store.attachment_save_failed"), file=path) from error

    def rebuild_index(
        self, classified: dict[str, Conversation] | None = None
    ) -> list[Conversation]:
        """Summaries derived from the stored messages, keeping any classification already made."""
        previous = {item.id: item for item in self.conversations()}
        if classified:
            previous.update(classified)
        conversations = []
        for folder in self._conversation_folders():
            messages = self._messages_in(folder)
            if not messages:
                continue
            conversation_id = _conversation_id_in(folder)
            if conversation_id is None:
                continue
            known = previous.get(conversation_id)
            conversations.append(_summarize(conversation_id, messages, known))
        write_json_atomically(
            self.folder / INDEX_FILE, [item.model_dump(mode="json") for item in conversations]
        )
        return sorted(conversations, key=lambda item: item.last_received_at, reverse=True)

    def register(self, conversation_id: str) -> None:
        folder = self._folder(conversation_id)
        folder.mkdir(parents=True, exist_ok=True)
        marker = folder / CONVERSATION_FILE
        if not marker.is_file():
            write_json_atomically(marker, {"id": conversation_id})

    def remove(self, conversation_id: str) -> None:
        folder = self._folder(conversation_id)
        if not folder.is_dir():
            raise MailStoreError(t("store.conversation_gone"))
        try:
            shutil.rmtree(folder)
        except OSError as error:
            raise OutputWriteError(t("store.remove_failed"), file=folder) from error
        self.rebuild_index()

    def prune(self, keep: int) -> int:
        conversations = self.conversations()
        removed = 0
        for conversation in conversations[keep:]:
            shutil.rmtree(self._folder(conversation.id), ignore_errors=True)
            removed += 1
        if removed:
            self.rebuild_index()
        return removed

    def export(self, conversation_id: str, target_folder: Path) -> Path:
        """Readable copy: one Markdown file per message and the attachments next to them."""
        conversation = self.conversation(conversation_id)
        messages = self.messages(conversation_id)
        destination = target_folder / safe_name(conversation.subject)
        try:
            destination.mkdir(parents=True, exist_ok=True)
            for index, message in enumerate(messages, start=1):
                stem = f"{index:03d} {safe_name(message.received_at[:10])}"
                (destination / f"{stem}.md").write_text(_as_markdown(message), encoding="utf-8")
                for attachment in message.attachments:
                    if attachment.file and Path(attachment.file).is_file():
                        shutil.copy2(attachment.file, destination / f"{stem} {attachment.name}")
        except OSError as error:
            raise OutputWriteError(t("store.export_failed"), file=destination) from error
        return destination

    def _folder(self, conversation_id: str) -> Path:
        return self.folder / folder_id_of(conversation_id)

    def _conversation_folders(self) -> list[Path]:
        if not self.folder.is_dir():
            return []
        return [path for path in self.folder.iterdir() if (path / CONVERSATION_FILE).is_file()]

    def _message_path(self, conversation_id: str, message_id: str) -> Path:
        return self._folder(conversation_id) / MESSAGES_FOLDER / f"{safe_name(message_id)}.json"

    def _messages_in(self, folder: Path) -> list[Message]:
        """The readable messages: one damaged file must not hide a whole conversation."""
        messages = []
        for path in (folder / MESSAGES_FOLDER).glob("*.json"):
            message = _read_message(path)
            if message is not None:
                messages.append(message)
        return sorted(messages, key=lambda message: message.received_at)


def _read_message(path: Path) -> Message | None:
    try:
        return Message.model_validate_json(path.read_text(encoding="utf-8"))
    except (OSError, ValidationError):
        return None


def _conversation_id_in(folder: Path) -> str | None:
    try:
        marker = json.loads((folder / CONVERSATION_FILE).read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return None
    identifier = marker.get("id") if isinstance(marker, dict) else None
    return identifier if isinstance(identifier, str) else None


def _summarize(
    conversation_id: str, messages: list[Message], known: Conversation | None
) -> Conversation:
    participants: dict[str, Participant] = {}
    for message in messages:
        for person in [message.sender, *message.recipients]:
            key = person.address.casefold() or person.name
            if key and key not in participants:
                participants[key] = person
    return Conversation(
        id=conversation_id,
        subject=clean_subject(messages[0].subject),
        participants=list(participants.values()),
        first_received_at=messages[0].received_at,
        last_received_at=messages[-1].received_at,
        message_count=len(messages),
        attachment_count=sum(len(message.attachments) for message in messages),
        project=known.project if known else None,
        category=known.category if known else None,
    )


def _as_markdown(message: Message) -> str:
    recipients = ", ".join(_label(person) for person in message.recipients)
    lines = [
        f"# {message.subject or t('store.no_subject')}",
        "",
        t("store.export.from", sender=_label(message.sender)),
        t("store.export.to", recipients=recipients),
        t("store.export.received", date=message.received_at),
    ]
    if message.attachments:
        names = ", ".join(attachment.name for attachment in message.attachments)
        lines.append(t("store.export.attachments", names=names))
    lines.extend(["", message.body or message.preview, ""])
    return "\n".join(lines)


def _label(person: Participant) -> str:
    if person.name and person.address:
        return f"{person.name} <{person.address}>"
    return person.name or person.address


def as_message(raw: dict[str, Any]) -> Message:
    """A Graph message resource reduced to what Drawflow keeps."""
    body = raw.get("body")
    content = body.get("content") if isinstance(body, dict) else ""
    return Message(
        id=str(raw.get("id", "")),
        received_at=str(raw.get("receivedDateTime", "")),
        sender=_participant(raw.get("from")),
        recipients=[
            _participant(item)
            for key in ("toRecipients", "ccRecipients")
            for item in raw.get(key, [])
            if isinstance(item, dict)
        ],
        subject=str(raw.get("subject") or ""),
        preview=str(raw.get("bodyPreview") or ""),
        body=str(content or ""),
        web_link=raw.get("webLink") if isinstance(raw.get("webLink"), str) else None,
    )


def _participant(raw: Any) -> Participant:
    address = raw.get("emailAddress") if isinstance(raw, dict) else None
    if not isinstance(address, dict):
        return Participant()
    return Participant(
        name=str(address.get("name") or ""), address=str(address.get("address") or "")
    )
