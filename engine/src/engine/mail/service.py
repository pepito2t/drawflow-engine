"""Entry points of `engine mail …`: sign in, fetch, list, export, remove. Mailbox is read-only."""

from datetime import UTC, datetime, timedelta
from pathlib import Path
from typing import Any

import httpx

from engine.core.errors import InvalidInputError
from engine.core.settings import load_mail_settings
from engine.core.settings_models import MailSettings
from engine.mail.graph import (
    MAX_ATTACHMENT_BYTES,
    DeviceLogin,
    GraphClient,
    MailError,
    finish_device_login,
    refresh_tokens,
    start_device_login,
)
from engine.mail.messages import t
from engine.mail.store import Attachment, ConversationStore, as_message
from engine.mail.tokens import MailSession, SessionStore

LOCAL_FOLDER_NAME = "mail"
SKIPPED_CONTENT_TYPES = ("image/",)


def status(settings_file: Path) -> dict[str, Any]:
    mail = load_mail_settings(settings_file)
    session = SessionStore(settings_file).read()
    return {
        "configured": bool(mail.client_id),
        "account": session.account if session else None,
        "last_fetch_at": session.last_fetch_at if session else None,
        "conversations": len(_store(settings_file, mail).conversations()),
        "folder": str(_folder(settings_file, mail)),
    }


def connect_start(
    settings_file: Path, transport: httpx.BaseTransport | None = None
) -> dict[str, Any]:
    mail = _configured(settings_file)
    login = start_device_login(mail.client_id, mail.tenant, transport)
    return login.model_dump(mode="json")


def connect_finish(
    settings_file: Path, raw_login: dict[str, Any], transport: httpx.BaseTransport | None = None
) -> dict[str, Any]:
    mail = _configured(settings_file)
    try:
        login = DeviceLogin.model_validate(raw_login)
    except ValueError as error:
        raise InvalidInputError(t("service.missing_code")) from error
    tokens = finish_device_login(mail.client_id, mail.tenant, login, transport)
    client = GraphClient(tokens.access_token, transport)
    try:
        account = client.account()
    finally:
        client.close()
    address = str(account.get("mail") or account.get("userPrincipalName") or "")
    SessionStore(settings_file).write(
        MailSession(account=address, refresh_token=tokens.refresh_token)
    )
    return {"account": address}


def disconnect(settings_file: Path) -> dict[str, Any]:
    SessionStore(settings_file).clear()
    return {"disconnected": True}


def fetch(settings_file: Path, transport: httpx.BaseTransport | None = None) -> dict[str, Any]:
    """Downloads the messages received since the last fetch and files them by conversation."""
    mail = _configured(settings_file)
    sessions = SessionStore(settings_file)
    session = sessions.read()
    if session is None:
        raise MailError(t("service.not_connected"), hint=t("service.not_connected_hint"))
    tokens = refresh_tokens(mail.client_id, mail.tenant, session.refresh_token, transport)
    store = _store(settings_file, mail)
    client = GraphClient(tokens.access_token, transport)
    try:
        received = client.messages_since(_since(session, mail))
        added = _file_messages(client, store, received)
    finally:
        client.close()
    conversations = store.rebuild_index()
    pruned = store.prune(mail.max_conversations)
    sessions.write(
        MailSession(
            account=session.account,
            refresh_token=tokens.refresh_token,
            last_fetch_at=datetime.now(UTC).isoformat(timespec="seconds"),
        )
    )
    return {
        "fetched": len(received),
        "added": added,
        "conversations": len(conversations) - pruned,
        "pruned": pruned,
    }


def list_conversations(settings_file: Path) -> dict[str, Any]:
    store = _store(settings_file, load_mail_settings(settings_file))
    return {"conversations": [item.model_dump(mode="json") for item in store.conversations()]}


def read_conversation(settings_file: Path, conversation_id: str) -> dict[str, Any]:
    store = _store(settings_file, load_mail_settings(settings_file))
    conversation = store.conversation(conversation_id)
    return {
        "conversation": conversation.model_dump(mode="json"),
        "messages": [
            message.model_dump(mode="json") for message in store.messages(conversation_id)
        ],
    }


def export_conversation(settings_file: Path, conversation_id: str, target: Path) -> dict[str, Any]:
    store = _store(settings_file, load_mail_settings(settings_file))
    return {"exported": str(store.export(conversation_id, target))}


def remove_conversation(settings_file: Path, conversation_id: str) -> dict[str, Any]:
    store = _store(settings_file, load_mail_settings(settings_file))
    store.remove(conversation_id)
    return {"removed": conversation_id}


def _configured(settings_file: Path) -> MailSettings:
    mail = load_mail_settings(settings_file)
    if not mail.client_id:
        raise MailError(t("service.not_configured"), hint=t("service.not_configured_hint"))
    return mail


def _folder(settings_file: Path, mail: MailSettings) -> Path:
    return mail.local_folder or settings_file.parent / LOCAL_FOLDER_NAME


def _store(settings_file: Path, mail: MailSettings) -> ConversationStore:
    return ConversationStore(_folder(settings_file, mail))


def _since(session: MailSession, mail: MailSettings) -> str:
    if session.last_fetch_at:
        return session.last_fetch_at
    start = datetime.now(UTC) - timedelta(days=mail.lookback_days)
    return start.isoformat(timespec="seconds").replace("+00:00", "Z")


def _file_messages(
    client: GraphClient, store: ConversationStore, received: list[dict[str, Any]]
) -> int:
    added = 0
    for raw in received:
        conversation_id = str(raw.get("conversationId") or raw.get("id") or "")
        if not conversation_id:
            continue
        message = as_message(raw)
        store.register(conversation_id)
        if raw.get("hasAttachments"):
            message = message.model_copy(
                update={
                    "attachments": _download_attachments(client, store, conversation_id, message.id)
                }
            )
        if store.add_message(conversation_id, message):
            added += 1
    return added


def _download_attachments(
    client: GraphClient, store: ConversationStore, conversation_id: str, message_id: str
) -> list[Attachment]:
    attachments = []
    for raw in client.attachments(message_id):
        name = str(raw.get("name") or t("service.attachment_default_name"))
        size = int(raw.get("size") or 0)
        content_type = str(raw.get("contentType") or "")
        attachment = Attachment(name=name, size=size, content_type=content_type)
        skip = raw.get("isInline") or size > MAX_ATTACHMENT_BYTES
        skip = skip or content_type.startswith(SKIPPED_CONTENT_TYPES)
        if not skip and isinstance(raw.get("id"), str):
            path = store.attachment_path(conversation_id, message_id, name)
            store.write_attachment(path, client.attachment_content(message_id, raw["id"]))
            attachment = attachment.model_copy(update={"file": str(path)})
        attachments.append(attachment)
    return attachments
