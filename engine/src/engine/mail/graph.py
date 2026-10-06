"""Microsoft Graph, read-only: device-code sign-in and message download. No SDK, plain HTTP."""

import time
from collections.abc import Callable
from typing import Any

import httpx
from pydantic import BaseModel, ConfigDict

from engine.core.errors import EngineError

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
        response = http.post(
            f"{LOGIN_ROOT}/{tenant}/oauth2/v2.0/devicecode",
            data={"client_id": client_id, "scope": SCOPES},
        )
    payload = _json_or_error(response, "Microsoft n'a pas fourni de code de connexion.")
    if not response.is_success:
        raise MailError(
            "Connexion à Microsoft refusée : " + _error_text(payload),
            hint="Vérifiez l'identifiant d'application et le tenant dans Paramètres → Courriel.",
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
            response = http.post(
                _token_url(tenant),
                data={
                    "client_id": client_id,
                    "grant_type": "urn:ietf:params:oauth:grant-type:device_code",
                    "device_code": login.device_code,
                },
            )
            payload = _json_or_error(response, "Réponse de connexion illisible.")
            if response.is_success:
                return Tokens.model_validate(payload)
            error = str(payload.get("error", ""))
            if error not in DEVICE_CODE_PENDING:
                raise MailError("Connexion à Microsoft échouée : " + _error_text(payload))
            if error == "slow_down":
                interval += SLOW_DOWN_EXTRA_SECONDS
            sleep(interval)
    raise MailError(
        "Le code de connexion a expiré.", hint="Relancez la connexion et saisissez le nouveau code."
    )


def refresh_tokens(
    client_id: str, tenant: str, refresh_token: str, transport: httpx.BaseTransport | None = None
) -> Tokens:
    with httpx.Client(timeout=LOGIN_TIMEOUT, transport=transport) as http:
        response = http.post(
            _token_url(tenant),
            data={
                "client_id": client_id,
                "grant_type": "refresh_token",
                "refresh_token": refresh_token,
                "scope": SCOPES,
            },
        )
    payload = _json_or_error(response, "Réponse de connexion illisible.")
    if not response.is_success:
        raise MailError(
            "La session Microsoft n'est plus valable.",
            hint="Reconnectez la boîte mail dans l'onglet Courriels.",
        )
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
        response = self._http.get(f"/me/messages/{message_id}/attachments/{attachment_id}/$value")
        if not response.is_success:
            raise MailError("Téléchargement d'une pièce jointe refusé par Microsoft.")
        return response.content

    def _get(self, url: str, params: dict[str, str] | None) -> dict[str, Any]:
        try:
            response = self._http.get(url, params=params)
        except httpx.TransportError as error:
            raise MailError(
                "Microsoft 365 est injoignable.", hint="Vérifiez la connexion Internet."
            ) from error
        payload = _json_or_error(response, "Réponse de Microsoft 365 illisible.")
        if not response.is_success:
            raise MailError("Microsoft 365 a refusé la lecture : " + _error_text(payload))
        return payload


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
        return str(error.get("message") or error.get("code") or "erreur inconnue")
    description = payload.get("error_description")
    return str(description or error or "erreur inconnue").splitlines()[0]
