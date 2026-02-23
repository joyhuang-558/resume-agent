# Resume Agent

A resume and document knowledge agent built with Agno + LanceDB. It ingests text and files into a searchable vector knowledge base, supports RAG-style candidate Q&A, and can optionally query Gmail via Agno Gmail toolkit.

## Features

- Resume knowledge ingestion from text, PDF, and TXT files.
- Local vector storage with LanceDB for semantic retrieval.
- Interactive agent Q&A over ingested candidate data.
- Dropbox-style folder monitoring for automatic ingestion.
- Optional Gmail integration (read-focused toolkit usage) for inbox-based screening workflows.
- Optional standalone Google API server for OAuth and direct Gmail/Calendar endpoint testing.

## Architecture

- `knowledge/`: Knowledge base setup, embedding config, LanceDB integration.
- `tools/knowledge_tool.py`: Insert text/files into the knowledge base.
- `tools/gmail_tools.py`: Creates Gmail toolkit with read-only filtering where supported.
- `agent/knowledge_agent.py`: Builds the main Agno agent and injects optional tools.
- `main.py`: App entrypoint (`demo`, `interactive`, `monitor`).
- `google_api_server/main.py`: Standalone FastAPI OAuth + Gmail/Calendar read endpoints.

## Project Structure

```text
resume-agent/
├── agent/
├── google_api_server/
├── ingestion/
├── knowledge/
├── tools/
├── batch_upload.py
├── config.example.env
├── main.py
└── requirements.txt
```

## Quick Start

### 1) Install dependencies

```bash
python3 -m pip install -r requirements.txt
```

### 2) Configure environment

```bash
cp config.example.env .env
```

Required in `.env`:

```bash
OPENROUTER_API_KEY=your_openrouter_api_key
LLM_MODEL=openai/gpt-4o-mini
```

Optional Gmail settings:

```bash
ENABLE_GMAIL_TOOLS=true
GOOGLE_CREDENTIALS_PATH=./google_api_server/credentials.json
GOOGLE_TOKEN_PATH=./google_api_server/token.json
```

### 3) Run the app

Interactive mode:

```bash
python3 main.py interactive
```

Other modes:

```bash
python3 main.py demo
python3 main.py monitor
python3 batch_upload.py /path/to/resumes
```

## Interactive Commands

- `insert <text>`: Insert single-line text into knowledge base.
- `insert`: Start multi-line input mode.
- `file <path>`: Insert a PDF/TXT file.
- `<question>`: Query the knowledge base (and enabled tools).
- `exit`: Exit the app.

Example prompts:

```text
Show latest 5 unread emails
Search emails about python resume
Who has machine learning experience?
```

## Gmail Integration Flow

1. Create Google OAuth client (Web application) with redirect URI:
   `http://localhost:8000/callback`
2. Put OAuth client JSON at:
   `google_api_server/credentials.json`
3. Authorize once to generate token:
   - Run: `python3 -m uvicorn main:app --reload --port 8000` in `google_api_server/`
   - Open: `http://127.0.0.1:8000/auth`
4. Ensure `.env` points to `credentials.json` and `token.json`.
5. Run `python3 main.py interactive` and use Gmail prompts.

## Standalone Google API Server (Optional)

The `google_api_server` folder provides a separate FastAPI service for direct API checks:

- `GET /` status + auth state
- `GET /auth` start OAuth
- `GET /calendar/events` list calendar events
- `GET /gmail/messages` list recent message IDs
- `GET /gmail/messages/{message_id}` get one message summary

Install/run:

```bash
cd google_api_server
python3 -m pip install -r requirements.txt
python3 -m uvicorn main:app --reload --port 8000
```

## Notes

- Keep secrets out of git (`.env`, `credentials.json`, `token.json` are ignored).
- The agent requires `OPENROUTER_API_KEY` at startup.
- Current Gmail test responses may be empty if the mailbox has no messages.

## License

For learning and research purposes.
