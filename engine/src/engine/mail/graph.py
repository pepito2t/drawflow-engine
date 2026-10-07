"""Microsoft Graph, read-only: device-code sign-in and message download. No SDK, plain HTTP."""

import time
from collections.abc import Callable
from typing import Any

import httpx
from pydantic import BaseModel, ConfigDict

from engine.core.errors import EngineError
from engine.mail.messages import t

LOGIN_ROOT = "https://login.microsoftonline.com"
GRAPH_ROOT = "https://graph.microsoft.com/v1.0"
SCOPES = "offline_access User.Read Mail.Read"
PAGE_SIZE = 50
MAX_PAGES = 40
MAX_ATTACHMENT_BYTES = 25_000_000
LOGIN_TIMEOUT = httpx.Timeout(15.0)
GRAPH_TIMEOUT = httpx.Timeout(connect=10.0, read=120.0, write=30.0, pool=10.0)
DEVICE_CODE_PENDING = {"authorization_pending", "slow_down"}
SLOW_DOWN_EXTRA_SECONDS = 5
MESSAGE_FIELDS = (
    "id,conversationId,subject,from,toRecipients,ccRecipients,receivedDateTime,"
    "bodyPreview,hasAttachments,body,webLink"
)
ATTACHMENT_FIELDS = "id,name,size,contentType,isInline"


class MailError(EngineError):
    pass


class DeviceLogin(BaseModel):
    model_config = ConfigDict(frozen=True, extra="ignore")

    device_code: str
    user_code: str
    verification_uri: str
    interval: int = 5
    expires_in: int = 900


class Tokens(BaseModel):
    model_config = ConfigDict(frozen=True, extra="ignore")

    access_token: str
    refresh_token: str
    expires_in: int = 3600


Sleep = Callable[[float], None]


def _token_url(tenant: str) -> str:
    return f"{LOGIN_ROOT}/{tenant}/oauth2/v2.0/token"


def start_device_login(
    client_id: str, tenant: str, transport: httpx.BaseTransport | None = None
) -> DeviceLogin:
    with httpx.Client(timeout=LOGIN_TIMEOUT, transport=transport) as http:
        response = _post(
            http,
            f"{LOGIN_ROOT}/{tenant}/oauth2/v2.0/devicecode",
            {"client_id": client_id, "scope": SCOPES},
        )
    payload = _json_or_error(response, t("graph.no_device_code"))
    if not response.is_success:
        raise MailError(
            t("graph.login_refused", error=_error_text(payload)),
            hint=t("graph.login_refused.hint"),
        )
    return DeviceLogin.model_validate(payload)


def finish_device_login(
    client_id: str,
    tenant: str,
    login: DeviceLogin,
    transport: httpx.BaseTransport | None = None,
    sleep: Sleep = time.sleep,
    clock: Callable[[], float] = time.monotonic,
) -> Tokens:
    """Polls until the user has signed in on the Microsoft page, or the code expires."""
    deadline = clock() + login.expires_in
    interval = float(login.interval)
    with httpx.Client(timeout=LOGIN_TIMEOUT, transport=transport) as http:
        while clock() < deadline:
            response = _post(
                http,
                _token_url(tenant),
                {
                    "client_id": client_id,
                    "grant_type": "urn:ietf:params:oauth:grant-type:device_code",
                    "device_code": login.device_code,
                },
            )
            payload = _json_or_error(response, t("graph.unreadable_login_reply"))
            if response.is_success:
                return Tokens.model_validate(payload)
            error = str(payload.get("error", ""))
            if error not in DEVICE_CODE_PENDING:
                raise MailError(t("graph.login_failed", error=_error_text(payload)))
            if error == "slow_down":
                interval += SLOW_DOWN_EXTRA_SECONDS
            sleep(interval)
    raise MailError(t("graph.code_expired"), hint=t("graph.code_expired.hint"))


def refresh_tokens(
    client_id: str, tenant: str, refresh_token: str, transport: httpx.BaseTransport | None = None
) -> Tokens:
    with httpx.Client(timeout=LOGIN_TIMEOUT, transport=transport) as http:
        response = _post(
            http,
            _token_url(tenant),
            {
                "client_id": client_id,
                "grant_type": "refresh_token",
                "refresh_token": refresh_token,
                "scope": SCOPES,
            },
        )
    payload = _json_or_error(response, t("graph.unreadable_login_reply"))
    if not response.is_success:
        raise MailError(t("graph.session_expired"), hint=t("graph.session_expired.hint"))
    return Tokens.model_validate(payload)


class GraphClient:
    def __init__(self, access_token: str, transport: httpx.BaseTransport | None = None) -> None:
        self._http = httpx.Client(
            base_url=GRAPH_ROOT,
            timeout=GRAPH_TIMEOUT,
            transport=transport,
            headers={
                "Authorization": f"Bearer {access_token}",
                "Prefer": 'outlook.body-content-type="text"',
            },
        )

    def close(self) -> None:
        self._http.close()

    def account(self) -> dict[str, Any]:
        return self._get("/me", {"$select": "displayName,mail,userPrincipalName"})

    def messages_since(self, received_after: str) -> list[dict[str, Any]]:
        """Newest first, several pages; `received_after` is an ISO 8601 instant."""
        collected: list[dict[str, Any]] = []
        url: str | None = "/me/messages"
        params: dict[str, str] | None = {
            "$select": MESSAGE_FIELDS,
            "$filter": f"receivedDateTime ge {received_after}",
            "$orderby": "receivedDateTime desc",
            "$top": str(PAGE_SIZE),
        }
        for _ in range(MAX_PAGES):
            if url is None:
                break
            page = self._get(url, params)
            params = None
            collected.extend(item for item in page.get("value", []) if isinstance(item, dict))
            url = page.get("@odata.nextLink")
        return collected

    def attachments(self, message_id: str) -> list[dict[str, Any]]:
        page = self._get(f"/me/messages/{message_id}/attachments", {"$select": ATTACHMENT_FIELDS})
        return [item for item in page.get("value", []) if isinstance(item, dict)]

    def attachment_content(self, message_id: str, attachment_id: str) -> bytes:
        response = self._fetch(
            f"/me/messages/{message_id}/attachments/{attachment_id}/$value", None
        )
        if not response.is_success:
            raise MailError(t("graph.attachment_refused"))
        return response.content

    def _get(self, url: str, params: dict[str, str] | None) -> dict[str, Any]:
        response = self._fetch(url, params)
        payload = _json_or_error(response, t("graph.unreadable_reply"))
        if not response.is_success:
            raise MailError(t("graph.read_refused", error=_error_text(payload)))
        return payload

    def _fetch(self, url: str, params: dict[str, str] | None) -> httpx.Response:
        try:
            return self._http.get(url, params=params)
        except httpx.TransportError as error:
            raise _unreachable() from error


def _post(http: httpx.Client, url: str, data: dict[str, str]) -> httpx.Response:
    try:
        return http.post(url, data=data)
    except httpx.TransportError as error:
        raise _unreachable() from error


def _unreachable() -> MailError:
    return MailError(t("graph.unreachable"), hint=t("graph.unreachable.hint"))


def _json_or_error(response: httpx.Response, message: str) -> dict[str, Any]:
    try:
        payload = response.json()
    except ValueError as error:
        raise MailError(message) from error
    if not isinstance(payload, dict):
        raise MailError(message)
    return payload


def _error_text(payload: dict[str, Any]) -> str:
    error = payload.get("error")
    if isinstance(error, dict):
        return str(error.get("message") or error.get("code") or t("graph.unknown_error"))
    description = payload.get("error_description")
    return str(description or error or t("graph.unknown_error")).splitlines()[0]
