import os
import secrets
from pathlib import Path

from fastapi import Query
from fastapi import APIRouter, HTTPException
from fastapi.responses import RedirectResponse
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import Flow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

import base64
import re
import httpx
from html.parser import HTMLParser

router = APIRouter(prefix="/gmail", tags=["Gmail Read-only"])

SCOPES = ["https://www.googleapis.com/auth/gmail.readonly"]
CLIENT_FILE = Path(os.environ["GOOGLE_OAUTH_CLIENT_SECRETS_FILE"])
TOKEN_FILE = Path(os.environ["GOOGLE_TOKEN_FILE"])
REDIRECT_URI = os.environ["GMAIL_REDIRECT_URI"]

# Local-development state only; use a server-side session store for production.
_pending_state = None


def create_flow(
    state=None,
    code_verifier=None,
    autogenerate_code_verifier=False,
):
    if not CLIENT_FILE.is_file():
        raise HTTPException(
            status_code=500,
            detail="OAuth client file is missing.",
        )

    flow = Flow.from_client_secrets_file(
        str(CLIENT_FILE),
        scopes=SCOPES,
        state=state,
        code_verifier=code_verifier,
        autogenerate_code_verifier=autogenerate_code_verifier,
    )
    flow.redirect_uri = REDIRECT_URI
    return flow


def load_credentials():
    if not TOKEN_FILE.is_file():
        return None
    try:
        credentials = Credentials.from_authorized_user_file(
            str(TOKEN_FILE), SCOPES
        )
        if credentials.expired and credentials.refresh_token:
            credentials.refresh(Request())
            TOKEN_FILE.parent.mkdir(parents=True, exist_ok=True)
            TOKEN_FILE.write_text(credentials.to_json(), encoding="utf-8")
        return credentials if credentials.valid else None
    except Exception:
        return None


@router.get("/oauth/start")
def oauth_start():
    global _pending_state, _pending_code_verifier

    _pending_state = secrets.token_urlsafe(32)

    flow = create_flow(
        state=_pending_state,
        autogenerate_code_verifier=True,
    )

    url, _ = flow.authorization_url(
        access_type="offline",
        prompt="consent",
    )

    _pending_code_verifier = flow.code_verifier
    return RedirectResponse(url, status_code=302)


@router.get("/oauth/callback")
def oauth_callback(code: str | None = None, state: str | None = None,
                   error: str | None = None):
    global _pending_state, _pending_code_verifier

    if error:
        _pending_state = None
        _pending_code_verifier = None
        raise HTTPException(status_code=400, detail="Google authorization was not completed.")
    if not code or not state or not _pending_state:
        raise HTTPException(status_code=400, detail="Missing or expired OAuth state.")
    if not secrets.compare_digest(state, _pending_state):
        raise HTTPException(status_code=400, detail="OAuth state validation failed.")

    expected_state = _pending_state
    expected_verifier = _pending_code_verifier

    _pending_state = None
    _pending_code_verifier = None

    if not expected_verifier:
        raise HTTPException(
            status_code=400,
            detail="Missing OAuth code verifier. Restart Gmail OAuth.",
        )

    flow = create_flow(
        state=expected_state,
        code_verifier=expected_verifier,
    )

    
    try:
        flow.fetch_token(code=code)
    except Exception as exc:
        error_code = getattr(exc, "error", None) or type(exc).__name__
        error_description = (
            getattr(exc, "description", None)
            or "No additional details returned."
        )
        print(
            f"OAuth token exchange failed: {error_code}; "
            f"description={error_description}"
        )
        raise HTTPException(
            status_code=400,
            detail=f"OAuth token exchange failed: {error_code}",
        ) from exc


    credentials = flow.credentials
    if not set(SCOPES).issubset(set(credentials.scopes or [])):
        raise HTTPException(status_code=403, detail="Gmail read-only scope was not granted.")

    TOKEN_FILE.parent.mkdir(parents=True, exist_ok=True)
    TOKEN_FILE.write_text(credentials.to_json(), encoding="utf-8")
    return {
        "status": "connected",
        "scope": SCOPES[0],
        "write_access_enabled": False,
        "message": "Gmail read-only OAuth completed."
    }


@router.get("/status")
def gmail_status():
    credentials = load_credentials()
    return {
        "connected": credentials is not None,
        "scope_requested": SCOPES[0],
        "write_access_enabled": False,
    }


@router.get("/labels")
def gmail_labels():
    credentials = load_credentials()
    if credentials is None:
        raise HTTPException(status_code=401, detail="Connect Gmail at /gmail/oauth/start first.")

    try:
        service = build("gmail", "v1", credentials=credentials, cache_discovery=False)
        result = service.users().labels().list(userId="me").execute()
        labels = result.get("labels", [])
        return {
            "count": len(labels),
            "labels": [
                {"id": item["id"], "name": item["name"], "type": item.get("type")}
                for item in labels
            ],
            "read_only": True,
        }
    except HttpError as exc:
        raise HTTPException(
            status_code=502,
            detail=f"Gmail labels request failed: HTTP {exc.resp.status}",
        ) from exc


@router.get("/messages")
def gmail_messages(
    max_results: int = Query(default=10, ge=1, le=50),
    label_ids: list[str] | None = Query(default=None),
):
    """List Gmail message metadata only. This endpoint never modifies mail."""
    credentials = load_credentials()
    if credentials is None:
        raise HTTPException(
            status_code=401,
            detail="Connect Gmail at /gmail/oauth/start first.",
        )

    try:
        service = build(
            "gmail",
            "v1",
            credentials=credentials,
            cache_discovery=False,
        )

        request_args = {
            "userId": "me",
            "maxResults": max_results,
        }
        if label_ids:
            request_args["labelIds"] = label_ids

        listing = service.users().messages().list(**request_args).execute()
        message_refs = listing.get("messages", [])

        messages = []
        for ref in message_refs:
            item = service.users().messages().get(
                userId="me",
                id=ref["id"],
                format="metadata",
                metadataHeaders=["From", "To", "Subject", "Date"],
            ).execute()

            headers = {
                header["name"].lower(): header["value"]
                for header in item.get("payload", {}).get("headers", [])
            }

            messages.append({
                "message_id": item["id"],
                "thread_id": item.get("threadId"),
                "sender": headers.get("from", ""),
                "recipient": headers.get("to", ""),
                "subject": headers.get("subject", ""),
                "date": headers.get("date", ""),
                "snippet": item.get("snippet", ""),
                "label_ids": item.get("labelIds", []),
            })

        return {
            "count": len(messages),
            "messages": messages,
            "next_page_token": listing.get("nextPageToken"),
            "read_only": True,
            "message_bodies_fetched": False,
        }

    except HttpError as exc:
        raise HTTPException(
            status_code=502,
            detail=f"Gmail message listing failed: HTTP {exc.resp.status}",
        ) from exc



AGENT_SERVICE_URL = os.getenv(
    "AGENT_SERVICE_URL",
    "http://agent-service:8001",
).rstrip("/")


class _HTMLTextExtractor(HTMLParser):
    """Extract readable text from HTML email bodies."""

    def __init__(self):
        super().__init__()
        self.parts = []
        self.skip_depth = 0

    def handle_starttag(self, tag, attrs):
        if tag in {"script", "style"}:
            self.skip_depth += 1
        elif tag == "br" or tag in {"p", "div", "li"}:
            self.parts.append("\n")

    def handle_endtag(self, tag):
        if tag in {"script", "style"} and self.skip_depth:
            self.skip_depth -= 1
        elif tag in {"p", "div", "li"}:
            self.parts.append("\n")

    def handle_data(self, data):
        if not self.skip_depth:
            self.parts.append(data)

    def get_text(self):
        return re.sub(r"\n{3,}", "\n\n", "".join(self.parts)).strip()


def _decode_gmail_body(data: str) -> str:
    """Decode Gmail's Base64URL-encoded body data."""
    try:
        raw = base64.urlsafe_b64decode(data + "=" * (-len(data) % 4))
        return raw.decode("utf-8", errors="replace")
    except (ValueError, TypeError):
        return ""


def _extract_email_body(payload: dict) -> str:
    """Extract text/plain first, falling back to text/html; skip attachments."""
    plain_parts = []
    html_parts = []

    def walk(part):
        mime_type = part.get("mimeType", "").lower()
        filename = part.get("filename", "")
        body = part.get("body", {})

        # Never index attachment contents.
        if filename or body.get("attachmentId"):
            return

        if mime_type == "text/plain" and body.get("data"):
            plain_parts.append(_decode_gmail_body(body["data"]))
        elif mime_type == "text/html" and body.get("data"):
            html_parts.append(_decode_gmail_body(body["data"]))

        for child in part.get("parts", []):
            walk(child)

    walk(payload)

    text = "\n".join(part for part in plain_parts if part.strip())
    if not text:
        parser = _HTMLTextExtractor()
        for part in html_parts:
            parser.feed(part)
        text = parser.get_text()

    return text[:100_000]


@router.post("/rag/index")
def index_gmail_inbox(
    max_results: int = Query(default=3, ge=1, le=3),
):
    """Index a small batch of Inbox email text for local RAG; never modify Gmail."""
    credentials = load_credentials()
    if credentials is None:
        raise HTTPException(
            status_code=401,
            detail="Connect Gmail at /gmail/oauth/start first.",
        )

    try:
        service = build(
            "gmail",
            "v1",
            credentials=credentials,
            cache_discovery=False,
        )

        listing = service.users().messages().list(
            userId="me",
            labelIds=["INBOX"],
            maxResults=max_results,
        ).execute()

        messages = []
        skipped_empty = 0

        for ref in listing.get("messages", []):
            item = service.users().messages().get(
                userId="me",
                id=ref["id"],
                format="full",
            ).execute()

            payload = item.get("payload", {})
            headers = {
                h["name"].lower(): h["value"]
                for h in payload.get("headers", [])
            }
            body = _extract_email_body(payload)

            if not body.strip():
                skipped_empty += 1
                continue

            messages.append({
                "id": item["id"],
                "threadId": item.get("threadId", ""),
                "subject": headers.get("subject", "")[:500],
                "sender": headers.get("from", "")[:500],
                "date": headers.get("date", "")[:100],
                "labels": item.get("labelIds", []),
                "body": body,
            })

        if not messages:
            return {
                "status": "no_indexable_messages",
                "messages_fetched": len(listing.get("messages", [])),
                "messages_indexed": 0,
                "skipped_empty": skipped_empty,
                "gmail_read_only": True,
            }

        with httpx.Client(timeout=180.0) as client:
            response = client.post(
                f"{AGENT_SERVICE_URL}/rag/index",
                json={"messages": messages},
            )
            response.raise_for_status()
            result = response.json()

        # Return counts and status, not email body contents.
        return {
            "status": result.get("status", "completed"),
            "messages_fetched": len(listing.get("messages", [])),
            "messages_sent_for_indexing": len(messages),
            "skipped_empty": skipped_empty,
            "index_result": result,
            "gmail_read_only": True,
            "attachments_indexed": False,
            "message_bodies_returned": False,
        }

    except HttpError as exc:
        raise HTTPException(
            status_code=502,
            detail=f"Gmail body retrieval failed: HTTP {exc.resp.status}",
        ) from exc
    except httpx.HTTPStatusError as exc:
        raise HTTPException(
            status_code=502,
            detail=f"RAG indexer rejected the batch: HTTP {exc.response.status_code}",
        ) from exc
    except httpx.HTTPError as exc:
        raise HTTPException(
            status_code=502,
            detail=f"RAG indexer unavailable: {type(exc).__name__}",
        ) from exc
