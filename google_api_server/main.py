"""
Local FastAPI server for Google Calendar API and Gmail API access.
Run: uvicorn main:app --reload --port 8000
Then open http://localhost:8000/auth to start OAuth (first time only).
"""

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

from fastapi import FastAPI, HTTPException
from fastapi.responses import RedirectResponse
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import Flow
from google.auth.transport.requests import Request
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

# ---------------------------------------------------------------------------
# Config: paths relative to this file
# ---------------------------------------------------------------------------
BASE_DIR = Path(__file__).resolve().parent
CREDENTIALS_FILE = BASE_DIR / "credentials.json"
TOKEN_FILE = BASE_DIR / "token.json"

# Scopes for Calendar (read) and Gmail (read)
SCOPES = [
    "https://www.googleapis.com/auth/calendar.readonly",
    "https://www.googleapis.com/auth/gmail.readonly",
]

# OAuth redirect (must match Google Cloud Console "Authorized redirect URIs")
REDIRECT_URI = "http://localhost:8000/callback"

app = FastAPI(
    title="Google Calendar & Gmail API Server",
    description="Local server to access Google Calendar and Gmail via OAuth.",
)


def get_credentials() -> Optional[Credentials]:
    """Load credentials from token.json; return None if not yet authorized."""
    if not TOKEN_FILE.exists():
        return None
    try:
        creds = Credentials.from_authorized_user_file(str(TOKEN_FILE), SCOPES)
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
            with open(TOKEN_FILE, "w") as f:
                f.write(creds.to_json())
        return creds
    except Exception:
        return None


def require_credentials():
    """Raise 401 if user has not completed OAuth."""
    creds = get_credentials()
    if not creds:
        raise HTTPException(
            status_code=401,
            detail="Not authorized. Open http://localhost:8000/auth in your browser first.",
        )
    return creds


# ---------------------------------------------------------------------------
# OAuth routes
# ---------------------------------------------------------------------------


@app.get("/")
def root():
    """Health and usage info."""
    has_token = TOKEN_FILE.exists()
    return {
        "service": "Google Calendar & Gmail API Server",
        "status": "running",
        "authorized": has_token,
        "next": "Open /auth to authorize" if not has_token else "Use /calendar/events and /gmail/messages",
        "endpoints": {
            "auth": "/auth",
            "callback": "/callback (used by Google after login)",
            "calendar_events": "/calendar/events",
            "gmail_messages": "/gmail/messages",
        },
    }


@app.get("/auth")
def auth():
    """Redirect user to Google OAuth consent screen."""
    if not CREDENTIALS_FILE.exists():
        raise HTTPException(
            status_code=500,
            detail=(
                "credentials.json not found. "
                "Download it from Google Cloud Console and put it in the same folder as main.py. "
                "See GOOGLE_CALENDAR_GMAIL_SETUP.md for steps."
            ),
        )
    flow = Flow.from_client_secrets_file(
        str(CREDENTIALS_FILE),
        scopes=SCOPES,
        redirect_uri=REDIRECT_URI,
    )
    authorization_url, _ = flow.authorization_url(
        access_type="offline",
        include_granted_scopes="true",
        prompt="consent",
    )
    return RedirectResponse(url=authorization_url)


@app.get("/callback")
def callback(code: Optional[str] = None, error: Optional[str] = None):
    """Handle OAuth callback from Google; save token and redirect."""
    if error:
        raise HTTPException(status_code=400, detail=f"OAuth error: {error}")
    if not code:
        raise HTTPException(status_code=400, detail="Missing 'code' in callback.")
    flow = Flow.from_client_secrets_file(
        str(CREDENTIALS_FILE),
        scopes=SCOPES,
        redirect_uri=REDIRECT_URI,
    )
    flow.fetch_token(code=code)
    creds = flow.credentials
    token_data = {
        "token": creds.token,
        "refresh_token": creds.refresh_token,
        "token_uri": creds.token_uri,
        "client_id": creds.client_id,
        "client_secret": creds.client_secret,
        "scopes": creds.scopes,
    }
    with open(TOKEN_FILE, "w") as f:
        json.dump(token_data, f, indent=2)
    return RedirectResponse(url="/success")


@app.get("/success")
def success():
    """Simple success page after OAuth."""
    return {
        "message": "Authorization successful. You can close this tab.",
        "try": "GET /calendar/events or GET /gmail/messages",
    }


# ---------------------------------------------------------------------------
# Calendar API
# ---------------------------------------------------------------------------


@app.get("/calendar/events")
def calendar_events(max_results: int = 10):
    """List upcoming events from the primary calendar."""
    creds = require_credentials()
    try:
        service = build("calendar", "v3", credentials=creds)
        now = datetime.now(timezone.utc).isoformat()
        events_result = (
            service.events()
            .list(
                calendarId="primary",
                timeMin=now,
                maxResults=max_results,
                singleEvents=True,
                orderBy="startTime",
            )
            .execute()
        )
        events = events_result.get("items", [])
        return {"calendar": "primary", "events": events, "count": len(events)}
    except HttpError as e:
        raise HTTPException(status_code=e.resp.status, detail=str(e))


# ---------------------------------------------------------------------------
# Gmail API
# ---------------------------------------------------------------------------


@app.get("/gmail/messages")
def gmail_messages(max_results: int = 10):
    """List recent messages from the inbox."""
    creds = require_credentials()
    try:
        service = build("gmail", "v1", credentials=creds)
        results = (
            service.users()
            .messages()
            .list(userId="me", maxResults=max_results)
            .execute()
        )
        messages = results.get("messages", [])
        return {"userId": "me", "message_ids": [m["id"] for m in messages], "count": len(messages)}
    except HttpError as e:
        raise HTTPException(status_code=e.resp.status, detail=str(e))


@app.get("/gmail/messages/{message_id}")
def gmail_message(message_id: str):
    """Get one message by ID (subject, snippet, etc.)."""
    creds = require_credentials()
    try:
        service = build("gmail", "v1", credentials=creds)
        msg = service.users().messages().get(userId="me", id=message_id).execute()
        payload = msg.get("payload", {})
        headers = {h["name"]: h["value"] for h in payload.get("headers", [])}
        return {
            "id": msg["id"],
            "threadId": msg.get("threadId"),
            "snippet": msg.get("snippet"),
            "subject": headers.get("Subject"),
            "from": headers.get("From"),
            "date": headers.get("Date"),
        }
    except HttpError as e:
        raise HTTPException(status_code=e.resp.status, detail=str(e))
