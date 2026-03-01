# Architecture

## Two Subsystems

### 1. Resume Agent (Main)

Handles resume ingestion and RAG-based Q&A.

```
User Input                    Knowledge Base                    Agent
     │                              │                              │
     │  insert/file/query           │                              │
     ├─────────────────────────────►│                              │
     │                              │   LanceDB (vectors)          │
     │                              │   Cohere reranker            │
     │                              │◄─────────────────────────────┤
     │                              │   semantic search            │
     │◄────────────────────────────────────────────────────────────┤
     │   answer                     │                              │
```

**Data flow:**

1. **Insert**: Text or PDF/TXT → chunking → embedding → LanceDB  
2. **Query**: Question → embedding → vector search → rerank → LLM → answer  

**Modules:**

| Module | Responsibility |
|--------|----------------|
| `main.py` | Entry point; demo / interactive / monitor modes |
| `agent/knowledge_agent.py` | Build Agent with OpenRouter LLM + RAG + insert tools |
| `knowledge/setup.py` | Init Knowledge base: LanceDB + OpenAI embedder (via OpenRouter) + Cohere reranker |
| `tools/knowledge_tool.py` | `InsertKnowledgeTool`: insert text or PDF/TXT into knowledge base |
| `ingestion/dropbox_monitor.py` | Watch `dropbox/` for new files; auto-ingest via `InsertKnowledgeTool` |

**Storage:** LanceDB at `knowledge/lancedb/` (local). File contents are chunked, embedded, and stored as vectors.

---

### 2. Google API Server (Standalone)

Provides REST API for Google Calendar and Gmail. **Not integrated** with the main Agent.

```
Browser / Client                    google_api_server                 Google APIs
        │                                  │                               │
        │  GET /auth                       │                               │
        ├─────────────────────────────────►│                               │
        │  redirect to Google OAuth        │                               │
        │◄─────────────────────────────────┤                               │
        │  sign in, grant access           │                               │
        ├─────────────────────────────────────────────────────────────────►│
        │                                  │  token saved to token.json    │
        │                                  │                               │
        │  GET /calendar/events            │  GET /gmail/messages          │
        ├─────────────────────────────────►├──────────────────────────────►│
        │  JSON response                   │◄──────────────────────────────┤
        │◄─────────────────────────────────┤                               │
```

**Endpoints:**

| Endpoint | Returns |
|----------|---------|
| `GET /auth` | Redirects to Google OAuth |
| `GET /calendar/events` | Upcoming calendar events (JSON) |
| `GET /gmail/messages` | Recent message IDs |
| `GET /gmail/messages/{id}` | Single message (subject, from, snippet) |

**Storage:** None. Data is fetched from Google on each request and returned as JSON.

**Files:** `credentials.json` (OAuth client, shared) and `token.json` (per-user auth, not committed).

---

## Integration Status

| Feature | Status |
|---------|--------|
| Main Agent ↔ LanceDB | ✅ Integrated |
| Main Agent ↔ Gmail/Calendar | ❌ Not connected; google_api_server is standalone |
| Gmail/Calendar → Knowledge Base | ❌ Not implemented |

To have the Agent answer questions about emails or calendar events, the main project would need to call the Google API server (or Gmail/Calendar APIs directly) and either:

- Expose the data via Agent tools, or  
- Ingest email/calendar content into the knowledge base periodically.
