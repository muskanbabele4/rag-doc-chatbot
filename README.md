# Document Q&A RAG Agent

An enterprise-style **Document Q&A chatbot** built as a single agent backed
by a Retrieval-Augmented Generation (RAG) pipeline, exposed through a
FastAPI service, with SQL-based persistence and an n8n workflow for
automatic document ingestion.

This project is intentionally scoped to mirror a real Software Developer
Intern (AI Engineering) job description.

## Architecture

```
 Document (PDF/DOCX/TXT)
        │
        ▼
 ┌─────────────────┐      ┌────────────────────┐
 │  Ingestion       │      │  n8n Workflow       │
 │  (load → chunk → │◄─────│  watches a folder /  │
 │   embed → store) │      │  webhook trigger     │
 └────────┬─────────┘      └────────────────────┘
          │ stores chunks
          ▼
 ┌─────────────────┐        ┌──────────────────┐
 │  Chroma Vector   │        │  SQLite (SQL)     │
 │  Store (RAG)     │        │  documents +      │
 │                  │        │  chat_messages    │
 └────────┬─────────┘        └─────────▲─────────┘
          │ retrieval tool             │ logs
          ▼                            │
 ┌─────────────────────────────────────┴───────┐
 │           LangChain Tool-Calling Agent        │
 │  tools: search_company_documents,             │
 │         list_uploaded_documents               │
 │  LLM: OpenAI / Anthropic (swappable)          │
 └────────────────────┬──────────────────────────┘
                       │
                       ▼
              ┌──────────────────┐
              │   FastAPI         │
              │  /chat /documents │
              │  /n8n/ingest-...  │
              └──────────────────┘
```

## How this maps to the JD

| JD Requirement | Where it's implemented |
|---|---|
| AI agents & agentic workflows | `app/agent/agent.py` — LangChain tool-calling agent |
| LangChain | Used throughout `rag/` and `agent/` |
| Orchestration tools (n8n) | `n8n/document_ingestion_workflow.json` + `/n8n/ingest-webhook` endpoint |
| RAG pipelines with documents & databases | `app/rag/ingest.py`, `app/rag/retriever.py` (Chroma) + `list_uploaded_documents` tool reading SQL |
| Python-based APIs/microservices | `app/main.py` (FastAPI) |
| LLM integration (OpenAI/Anthropic/open-source) | `get_llm()` in `agent.py`, switch via `LLM_PROVIDER` env var |
| SQL/NoSQL databases | SQLite via SQLAlchemy (SQL) + Chroma (vector/NoSQL-style store) |
| Git/version control | Ship this as a git repo; see Setup below |

## Setup

```bash
cd rag-doc-chatbot
python -m venv venv
source venv/bin/activate        # Windows: venv\Scripts\activate

pip install -r requirements.txt

cp .env.example .env
# edit .env and add your OPENAI_API_KEY (or ANTHROPIC_API_KEY + LLM_PROVIDER=anthropic)

uvicorn app.main:app --reload
```

API docs available at `http://localhost:8000/docs` (FastAPI auto Swagger UI).

## API Endpoints

| Method | Path | Purpose |
|---|---|---|
| POST | `/documents/upload` | Upload + ingest a PDF/DOCX/TXT into the vector store |
| GET | `/documents` | List ingested documents and their status |
| POST | `/chat` | Ask the agent a question (`{session_id, message}`) |
| GET | `/chat/{session_id}/history` | Retrieve chat history for a session |
| POST | `/n8n/ingest-webhook` | Called by n8n when a new file appears |
| GET | `/health` | Health check |

## n8n Setup

1. Import `n8n/document_ingestion_workflow.json` into your n8n instance.
2. Replace the Webhook trigger with a **Local File Trigger** or **Folder
   Watch** node pointing at your drop folder (or keep the webhook and POST
   `{"file_path": "..."}` to it manually/from another system).
3. Update the `X-N8N-Secret` header value to match `N8N_WEBHOOK_SECRET`
   in your `.env`.
4. Activate the workflow — new documents will be ingested automatically
   without touching the API by hand.

## Project Structure

```
rag-doc-chatbot/
├── app/
│   ├── main.py            # FastAPI app & routes
│   ├── config.py          # env-driven settings
│   ├── schemas.py         # Pydantic request/response models
│   ├── rag/
│   │   ├── ingest.py       # load → chunk → embed → store
│   │   └── retriever.py    # similarity search
│   ├── agent/
│   │   └── agent.py        # LangChain tool-calling agent
│   └── db/
│       ├── database.py     # SQLAlchemy engine/session
│       └── models.py       # Document, ChatMessage tables
├── n8n/
│   └── document_ingestion_workflow.json
├── data/documents/         # uploaded files land here
├── requirements.txt
├── .env.example
└── README.md
```

## Notes / Next Steps

- Swap `OpenAIEmbeddings` for a local model (e.g. `sentence-transformers`)
  in `rag/ingest.py` if you want a fully offline embedding step.
- Add authentication on `/documents/upload` and `/chat` before any real
  deployment.
- Add a `Dockerfile` + `docker-compose.yml` (FastAPI + n8n) for one-command
  local spin-up if you want to demo this end-to-end.
