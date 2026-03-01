# Google Calendar & Gmail — Setup Guide

Get `credentials.json` from a teammate, or create it following the steps below. Put it in `google_api_server/`. Then start the server and open **http://localhost:8000/auth** to sign in with your Google account.

---

## When to Use This Guide

Use this guide when:

- `credentials.json` is not available from a teammate
- You need to create a new OAuth client (e.g. in a new Google Cloud project)

---

## Steps to Recreate Credentials

### 1. Google Cloud project

[Console](https://console.cloud.google.com/) → create project (e.g. **Resume Agent API**).

### 2. Enable APIs

**APIs & Services** → **Library** → enable **Google Calendar API** and **Gmail API**.

### 3. OAuth client

**APIs & Services** → **Credentials** → **Create credentials** → **OAuth client ID**.

- **Application type**: Web application
- **Authorized redirect URIs**: `http://localhost:8000/callback`
- **Name**: e.g. *Resume Agent Local*

If prompted for a consent screen: **External**, fill App name + support email, add yourself as test user. Skip adding scopes in the Console; the app requests them at runtime.

Download the JSON and save it as `google_api_server/credentials.json`.

### 4. Run and authorize

```bash
cd google_api_server
pip install -r requirements.txt
uvicorn main:app --reload --port 8000
```

Open **http://localhost:8000/auth** and sign in.

---

## Endpoints

| Endpoint | Description |
|----------|-------------|
| `GET /` | Service info |
| `GET /auth` | Start OAuth flow |
| `GET /calendar/events` | Upcoming events (JSON) |
| `GET /gmail/messages` | Recent message IDs |
| `GET /gmail/messages/{id}` | Single message details |

---

## Troubleshooting

| Issue | Fix |
|-------|-----|
| `credentials.json` not found | Follow steps above to create OAuth client and download JSON. |
| Redirect URI mismatch | Set **Authorized redirect URIs** to exactly `http://localhost:8000/callback`. |
| 401 on `/calendar/events` or `/gmail/messages` | Open **http://localhost:8000/auth** and complete sign-in. |
| Token invalid / `deleted_client` | Delete `token.json`, open `/auth` again. |
| Switch to another Google account | Delete `token.json`, open `/auth`, sign in with the new account. |
