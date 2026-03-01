# Resume Agent

An ML Agent system for screening and understanding candidates. Upload resumes (PDF/TXT), query them via natural language, and optionally access Google Calendar & Gmail via a separate API server.

---

## Architecture Overview

The project has **two subsystems** that run independently:

```
┌─────────────────────────────────────────────────────────────────────────────────┐
│                           RESUME AGENT (Main)                                     │
│  Upload PDF/TXT → LanceDB (vector store) → Agent (RAG) → Answer questions         │
│  Tech: Agno, OpenRouter LLM, LanceDB, Cohere reranker                             │
└─────────────────────────────────────────────────────────────────────────────────┘
                                      │
                                      │  (Not integrated yet)
                                      ▼
┌─────────────────────────────────────────────────────────────────────────────────┐
│                      GOOGLE API SERVER (Standalone)                               │
│  OAuth → Read Calendar events / Gmail messages → Return JSON                      │
│  Tech: FastAPI, Google API Python client                                          │
│  Note: Data is fetched on-demand; nothing is stored in the knowledge base         │
└─────────────────────────────────────────────────────────────────────────────────┘
```

See [ARCHITECTURE.md](ARCHITECTURE.md) for details.

---

## Project Structure

```
resume agent/
├── main.py                 # Entry point (demo / interactive / monitor)
├── batch_upload.py         # Batch upload PDFs from a directory
├── config.example.env      # Environment template
├── requirements.txt
│
├── agent/
│   └── knowledge_agent.py  # Agent: OpenRouter + RAG + insert tools
├── knowledge/
│   ├── config.py           # Config (LanceDB, embedder, dropbox path)
│   └── setup.py            # Knowledge base init (LanceDB + embedder)
├── tools/
│   └── knowledge_tool.py   # Insert text/file into knowledge base
├── ingestion/
│   └── dropbox_monitor.py  # Watch dropbox/ folder, auto-ingest new files
├── dropbox/                # Local folder for drag-and-drop (not cloud Dropbox)
│
├── google_api_server/      # Standalone FastAPI service
│   ├── main.py             # /auth, /calendar/events, /gmail/messages
│   ├── credentials.json    # OAuth client (get from teammate; not in git)
│   └── requirements.txt
│
├── ARCHITECTURE.md         # Architecture details
├── GOOGLE_CALENDAR_GMAIL_SETUP.md
└── DROPBOX_USAGE.md        # How to use the dropbox folder
```

---

## Setup for New Collaborators

### 1. Main Project

```bash
pip install -r requirements.txt
cp config.example.env .env
# Edit .env: add OPENROUTER_API_KEY (required), optionally COHERE_API_KEY
```

### 2. Google Calendar & Gmail (Optional)

Get `credentials.json` from a teammate or follow [GOOGLE_CALENDAR_GMAIL_SETUP.md](GOOGLE_CALENDAR_GMAIL_SETUP.md) to create it. Put it in `google_api_server/`. Then:

```bash
cd google_api_server
pip install -r requirements.txt
uvicorn main:app --reload --port 8000
```

Open **http://localhost:8000/auth** and sign in with your Google account. Then:

- **http://localhost:8000/calendar/events** — upcoming events
- **http://localhost:8000/gmail/messages** — recent emails

See [GOOGLE_CALENDAR_GMAIL_SETUP.md](GOOGLE_CALENDAR_GMAIL_SETUP.md) if you need to recreate credentials.

---

## Quick Start

### Interactive mode (chat with the agent)

```bash
python main.py interactive
```

- `insert <text>` — add text to knowledge base  
- `file <path>` — add PDF/TXT (e.g. `file dropbox/resume.pdf`)  
- Ask questions — agent answers from the knowledge base  
- `exit` — quit  

### Monitor mode (auto-ingest from dropbox)

```bash
python main.py monitor
# Then drop PDF/TXT files into dropbox/ — they are ingested automatically
```

### Batch upload

```bash
python batch_upload.py /path/to/resumes/
```

---

## Configuration

| Variable | Description | Default |
|----------|-------------|---------|
| `OPENROUTER_API_KEY` | Required for LLM and embeddings | — |
| `COHERE_API_KEY` | Optional; improves search ranking | — |
| `LLM_MODEL` | OpenRouter model | `openai/gpt-4o-mini` |
| `KNOWLEDGE_URI` | LanceDB path | `./knowledge/lancedb` |
| `DROPBOX_PATH` | Dropbox folder | `./dropbox` |

---

## Tech Stack

- **Python 3.9+**
- **Agno** — Knowledge, Agent, RAG
- **LanceDB** — Local vector store
- **OpenRouter** — LLM and embeddings
- **Cohere** — Reranker (optional)
- **pypdf**, **watchdog** — PDF handling, file monitoring

---

## License

For learning and research purposes.
