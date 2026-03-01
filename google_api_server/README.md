# Google Calendar & Gmail API Server

Standalone FastAPI server for read-only access to Google Calendar and Gmail.

- **Setup**: See [GOOGLE_CALENDAR_GMAIL_SETUP.md](../GOOGLE_CALENDAR_GMAIL_SETUP.md)
- **Architecture**: See [ARCHITECTURE.md](../ARCHITECTURE.md)

## Quick run

```bash
pip install -r requirements.txt
uvicorn main:app --reload --port 8000
```

First time: open **http://localhost:8000/auth** to authorize. Then use `/calendar/events` and `/gmail/messages`.
