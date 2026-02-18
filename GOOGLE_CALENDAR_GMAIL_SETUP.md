# Google Calendar & Gmail API — Setup Guide

Local FastAPI server to read **Google Calendar** and **Gmail**. Result: `http://localhost:8000/calendar/events` and `http://localhost:8000/gmail/messages` return JSON. No scopes need to be added in the Console; the app requests them at runtime.

---

## Steps

**1. Google Cloud project**  
[Console](https://console.cloud.google.com/) → create project (e.g. **Resume Agent API**).

**2. Enable APIs**  
**APIs & Services** → **Library** → enable **Google Calendar API** and **Gmail API**.

**3. OAuth client**  
**APIs & Services** → **Credentials** (or **Google Auth Platform** → **Create OAuth client**).  
→ **Web application**, **Authorized redirect URIs**: `http://localhost:8000/callback`, **Name** (e.g. *Local Calendar Gmail Server*).  
→ Create → **Download** JSON → rename to **`credentials.json`** → put in **`google_api_server/`** (same folder as `main.py`).  
If asked for consent screen: **External**, fill App name + support email, add yourself as test user. Skip adding scopes.

**4. Run server**  
```bash
cd google_api_server
pip install -r requirements.txt
uvicorn main:app --reload --port 8000
```

**5. Authorize once**  
Browser: **http://localhost:8000/auth** → sign in with the Google account you want (e.g. KWF or `apps@kashmirworldfoundation.com`) → grant access.

**6. Use**  
- **http://localhost:8000/calendar/events** — calendar events (JSON)  
- **http://localhost:8000/gmail/messages** — recent message IDs (JSON)  
- **http://localhost:8000/gmail/messages/{id}** — one message

---

## Checklist

- [ ] Project created, Calendar API + Gmail API enabled  
- [ ] OAuth client (Web app), redirect `http://localhost:8000/callback`  
- [ ] `credentials.json` in `google_api_server/`  
- [ ] `uvicorn main:app --reload --port 8000`  
- [ ] **http://localhost:8000/auth** → sign in → test the two URLs above  

---

## Troubleshooting

| Issue | Fix |
|-------|-----|
| credentials.json not found | Download OAuth client JSON, rename to `credentials.json`, put in `google_api_server/`. |
| Redirect URI mismatch | Set **Authorized redirect URIs** to exactly `http://localhost:8000/callback`. |
| 401 on /calendar/events or /gmail/messages | Open **http://localhost:8000/auth** and complete sign-in. |
| 403 | Ensure both APIs are enabled; use an account that has access to that calendar/inbox. |
| Token invalid | Delete `token.json`, go to `/auth` again. |

---

To use another account (e.g. `apps@kashmirworldfoundation.com`): delete `token.json`, open `/auth` again, sign in with that account.
