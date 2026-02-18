# Google Calendar & Gmail API — Local Server

FastAPI server that accesses **Google Calendar** and **Gmail** via OAuth 2.0. After setup, **http://localhost:8000/calendar/events** and **http://localhost:8000/gmail/messages** return JSON for the signed-in account.

**Full setup (one-time):** [GOOGLE_CALENDAR_GMAIL_SETUP.md](../GOOGLE_CALENDAR_GMAIL_SETUP.md) in the repo root.

---

## Quick summary

1. In Google Cloud Console: create project → enable **Calendar API** and **Gmail API** → **Create OAuth client** (Web app), redirect URI `http://localhost:8000/callback` → download JSON as **`credentials.json`** and put it in this folder. No need to add scopes in the Console; the app requests them when you authorize.
2. Run: `pip install -r requirements.txt` then `uvicorn main:app --reload --port 8000`.
3. In the browser open **http://localhost:8000/auth**, sign in with the Google account you want to use, and grant access.
4. Use **http://localhost:8000/calendar/events** and **http://localhost:8000/gmail/messages** to get JSON.

---

## Quick run (after you have `credentials.json`)

```bash
cd google_api_server
pip install -r requirements.txt
uvicorn main:app --reload --port 8000
```

- First time: open **http://localhost:8000/auth** to authorize.
- Then: **http://localhost:8000/calendar/events** and **http://localhost:8000/gmail/messages** return JSON.
