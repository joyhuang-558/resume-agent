"""
Local FastAPI server for Google Calendar API and Gmail API access.
Run: uvicorn main:app --reload --port 8000
Then open http://localhost:8000/auth to start OAuth (first time only).
"""

import json
import logging
import os
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

from fastapi import FastAPI, HTTPException
from fastapi.responses import HTMLResponse, RedirectResponse
from pydantic import BaseModel
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import Flow
from google.auth.transport.requests import Request
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

# ---------------------------------------------------------------------------
# Config: paths relative to this file
# ---------------------------------------------------------------------------
BASE_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = BASE_DIR.parent
CREDENTIALS_FILE = BASE_DIR / "credentials.json"
TOKEN_FILE = BASE_DIR / "token.json"
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

try:
    from dotenv import load_dotenv

    load_dotenv(PROJECT_ROOT / ".env")
except Exception:
    pass

from agent.knowledge_agent import create_knowledge_agent
from knowledge.config import KnowledgeConfig
from knowledge.setup import create_knowledge_base
from tools.knowledge_tool import InsertKnowledgeTool

logger = logging.getLogger(__name__)

# Scopes for Calendar (read) and Gmail (read)
SCOPES = [
    "https://www.googleapis.com/auth/calendar.readonly",
    "https://www.googleapis.com/auth/gmail.readonly",
]

# OAuth redirect (must match Google Cloud Console "Authorized redirect URIs")
REDIRECT_URI = "http://localhost:8000/callback"

app = FastAPI(
    title="Google Calendar & Gmail API Server",
    description="Local server to access Google Calendar, Gmail, and Resume Agent chat via OAuth.",
)

_CHAT_AGENT = None


class ChatRequest(BaseModel):
    message: str


class ChatResponse(BaseModel):
    answer: str


def _env_bool(name: str, default: bool = False) -> bool:
    value = os.getenv(name)
    if value is None:
        return default
    return value.strip().lower() in {"1", "true", "yes", "on"}


def _resolve_project_path(value: str) -> str:
    path = Path(value)
    if path.is_absolute():
        return str(path)
    return str((PROJECT_ROOT / path).resolve())


def _chat_ui_html() -> str:
    return """<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1" />
  <title>Resume Agent Chat</title>
  <style>
    :root {
      --bg: #0b1020;
      --panel: #131a2e;
      --panel-2: #1b2440;
      --text: #edf2ff;
      --muted: #9fb0d0;
      --accent: #7aa2ff;
      --user: #244a9a;
      --agent: #223055;
      --error: #9f2f2f;
      --border: #2f3f69;
    }
    * { box-sizing: border-box; }
    body {
      margin: 0;
      font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
      background: radial-gradient(1200px 500px at 20% -20%, #1f2b4d 0%, var(--bg) 50%);
      color: var(--text);
    }
    .wrap {
      max-width: 920px;
      margin: 0 auto;
      padding: 24px 16px 32px;
    }
    .header {
      margin-bottom: 14px;
    }
    .title {
      margin: 0;
      font-size: 24px;
      font-weight: 700;
    }
    .subtitle {
      margin: 6px 0 0;
      color: var(--muted);
      font-size: 14px;
    }
    .panel {
      border: 1px solid var(--border);
      background: linear-gradient(180deg, var(--panel), var(--panel-2));
      border-radius: 14px;
      overflow: hidden;
      box-shadow: 0 18px 40px rgba(0, 0, 0, 0.3);
    }
    #messages {
      height: 62vh;
      overflow-y: auto;
      padding: 16px;
      display: flex;
      flex-direction: column;
      gap: 10px;
    }
    .msg {
      padding: 10px 12px;
      border-radius: 10px;
      white-space: pre-wrap;
      line-height: 1.45;
      border: 1px solid rgba(255, 255, 255, 0.08);
    }
    .msg.user {
      align-self: flex-end;
      background: var(--user);
      max-width: 80%;
    }
    .msg.agent {
      align-self: flex-start;
      background: var(--agent);
      max-width: 90%;
    }
    .msg.error {
      align-self: flex-start;
      background: var(--error);
      max-width: 90%;
    }
    .composer {
      border-top: 1px solid var(--border);
      padding: 12px;
      display: grid;
      grid-template-columns: 1fr auto;
      gap: 10px;
      background: rgba(4, 9, 20, 0.35);
    }
    textarea {
      width: 100%;
      min-height: 68px;
      max-height: 180px;
      resize: vertical;
      border-radius: 10px;
      border: 1px solid var(--border);
      background: #0f1730;
      color: var(--text);
      padding: 10px;
      font: inherit;
    }
    button {
      border: 1px solid #5d84de;
      background: var(--accent);
      color: #0b1430;
      border-radius: 10px;
      padding: 0 18px;
      font-weight: 600;
      cursor: pointer;
      min-width: 94px;
    }
    button:disabled { opacity: 0.5; cursor: not-allowed; }
    .quick {
      display: flex;
      gap: 8px;
      flex-wrap: wrap;
      margin-top: 10px;
    }
    .quick button {
      background: transparent;
      color: var(--muted);
      border-color: var(--border);
      padding: 6px 10px;
      min-width: 0;
    }
  </style>
</head>
<body>
  <div class="wrap">
    <div class="header">
      <h1 class="title">Resume Agent Chat</h1>
      <p class="subtitle">Web shell for <code>POST /chat</code>. Ask about Gmail + resume knowledge in one place.</p>
      <div class="quick">
        <button data-prompt="Show latest 5 unread emails">Show latest unread emails</button>
        <button data-prompt="Search emails about Application">Search application emails</button>
        <button data-prompt="Who are the strongest candidates from recent application emails?">Top candidates</button>
      </div>
    </div>
    <div class="panel">
      <div id="messages"></div>
      <form id="chat-form" class="composer">
        <textarea id="prompt" placeholder="Ask something..."></textarea>
        <button id="send-btn" type="submit">Send</button>
      </form>
    </div>
  </div>
  <script>
    const messages = document.getElementById("messages");
    const form = document.getElementById("chat-form");
    const input = document.getElementById("prompt");
    const sendBtn = document.getElementById("send-btn");
    const quickButtons = document.querySelectorAll(".quick button");

    function pushMessage(kind, text) {
      const div = document.createElement("div");
      div.className = "msg " + kind;
      div.textContent = text;
      messages.appendChild(div);
      messages.scrollTop = messages.scrollHeight;
    }

    async function sendPrompt(prompt) {
      const clean = prompt.trim();
      if (!clean) return;
      pushMessage("user", clean);
      sendBtn.disabled = true;
      try {
        const res = await fetch("/chat", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ message: clean })
        });
        const body = await res.json();
        if (!res.ok) {
          throw new Error(body.detail || "Request failed");
        }
        pushMessage("agent", body.answer || "(empty response)");
      } catch (err) {
        pushMessage("error", "Error: " + err.message);
      } finally {
        sendBtn.disabled = false;
      }
    }

    form.addEventListener("submit", async (e) => {
      e.preventDefault();
      const value = input.value;
      input.value = "";
      await sendPrompt(value);
      input.focus();
    });

    quickButtons.forEach((btn) => {
      btn.addEventListener("click", async () => {
        await sendPrompt(btn.dataset.prompt || "");
      });
    });

    pushMessage("agent", "Ready. Try one of the quick prompts above.");
  </script>
</body>
</html>
"""


def get_chat_agent():
    """Lazily initialize and reuse the Resume Agent instance."""
    global _CHAT_AGENT
    if _CHAT_AGENT is not None:
        return _CHAT_AGENT

    config = KnowledgeConfig.from_env()
    config.uri = _resolve_project_path(config.uri)
    config.dropbox_path = _resolve_project_path(config.dropbox_path)

    knowledge_base = create_knowledge_base(config)
    knowledge_tool = InsertKnowledgeTool(knowledge_base)

    enable_gmail_tools = _env_bool("ENABLE_GMAIL_TOOLS", default=True)
    gmail_credentials_path = _resolve_project_path(
        os.getenv("GOOGLE_CREDENTIALS_PATH", "./google_api_server/credentials.json")
    )
    gmail_token_path = _resolve_project_path(
        os.getenv("GOOGLE_TOKEN_PATH", "./google_api_server/token.json")
    )

    _CHAT_AGENT = create_knowledge_agent(
        knowledge_base,
        knowledge_tool=knowledge_tool,
        enable_insert_tools=True,
        enable_gmail_tools=enable_gmail_tools,
        gmail_credentials_path=gmail_credentials_path,
        gmail_token_path=gmail_token_path,
    )
    logger.info("Resume chat agent initialized. Gmail tools enabled=%s", enable_gmail_tools)
    return _CHAT_AGENT


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
            "chat": "POST /chat",
            "chat_ui": "/chat-ui",
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


@app.post("/chat", response_model=ChatResponse)
async def chat(payload: ChatRequest):
    """Chat with the same Resume Agent used in terminal interactive mode."""
    prompt = payload.message.strip()
    if not prompt:
        raise HTTPException(status_code=400, detail="Field 'message' cannot be empty.")

    try:
        agent = get_chat_agent()
        response = await agent.arun(prompt)
        answer = getattr(response, "content", str(response))
        return ChatResponse(answer=answer)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Agent chat failed: {e}")


@app.get("/chat-ui", response_class=HTMLResponse)
def chat_ui():
    """Minimal browser UI for chatting with the Resume Agent."""
    return HTMLResponse(content=_chat_ui_html())
