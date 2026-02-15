# Nebula - AI Onboarding Assistant

[![CI](https://github.com/tawfik37/Nebula-onboarding/actions/workflows/ci.yml/badge.svg)](https://github.com/tawfik37/Nebula-onboarding/actions)
[![Python 3.10](https://img.shields.io/badge/python-3.10-blue.svg)](https://www.python.org/downloads/)

An **Agentic RAG system** that helps new hires navigate company policies, org structure, and role-specific requirements. Built with LangGraph, FastAPI, and Streamlit.

## Highlights

- **ReAct Agent** — Reasons over multiple tools before answering (not a simple prompt chain)
- **Streaming + Reasoning UI** — Watch the agent think in real-time: tool calls, results, and final answer
- **Smart Ingestion** — Incremental vector ingestion with MD5 change detection (no re-processing unchanged files)
- **Persistent Memory** — SQLite-backed conversation history survives backend restarts
- **Docker Ready** — `docker-compose up` spins up the full stack
- **CI Pipeline** — Ruff linting + 23 unit tests on every push

## Architecture

```
┌──────────────────────────────────────┐
│          Streamlit Frontend          │
│   Chat UI  ·  Agent Reasoning Panel  │
└──────────────────┬───────────────────┘
                   │ SSE Stream
┌──────────────────▼───────────────────┐
│          FastAPI Backend             │
│  /api/v1/chat/stream  ·  /health    │
└──────────────────┬───────────────────┘
                   │
┌──────────────────▼───────────────────┐
│     LangGraph ReAct Agent            │
│     (Gemini 2.5 Flash, temp=0)       │
│                                      │
│  Tools:                              │
│  🔍 search_policies  → ChromaDB     │
│  👤 lookup_employee   → org_chart    │
│  📋 lookup_role_reqs  → role_defs   │
└──────────────────────────────────────┘
```

## Tech Stack

| Layer | Technology |
|-------|-----------|
| LLM | Google Gemini 2.5 Flash |
| Agent Framework | LangGraph (ReAct pattern) |
| Vector Store | ChromaDB with Gemini Embeddings |
| Backend | FastAPI + Uvicorn |
| Frontend | Streamlit |
| Memory | SQLite (langgraph-checkpoint-sqlite) |
| CI | GitHub Actions (ruff + pytest) |

## Quick Start

### Option 1: Docker (Recommended)

```bash
# Clone and configure
git clone https://github.com/tawfik37/Nebula-onboarding.git
cd Nebula-onboarding
cp .env.example .env  # Add your GOOGLE_API_KEY

# Run
docker-compose up --build
```

- Frontend: http://localhost:8501
- API: http://localhost:8000
- Health: http://localhost:8000/health

### Option 2: Local

```bash
# Initialize
chmod +x scripts/init.sh
./scripts/init.sh

# Add your API key
echo "GOOGLE_API_KEY=your-key-here" > .env

# Run
./scripts/run_app.sh
```

## API Endpoints

| Method | Path | Description |
|--------|------|-------------|
| `GET` | `/` | Root status check |
| `GET` | `/health` | Detailed health (DB doc count, data file status) |
| `POST` | `/api/v1/chat` | Synchronous chat (JSON response) |
| `POST` | `/api/v1/chat/stream` | Streaming chat (SSE with tool events) |

## Project Structure

```
Nebula-onboarding/
├── backend/
│   └── app/
│       ├── main.py              # FastAPI endpoints + SSE streaming
│       └── models/schemas.py    # Pydantic request/response models
├── rag_engine/
│   ├── agents/
│   │   ├── onboarding_agent.py  # LangGraph ReAct agent setup
│   │   └── tools.py             # 3 agent tools (policies, employees, roles)
│   └── ingestion/
│       └── ingest.py            # Incremental vector ingestion pipeline
├── frontend/
│   └── app.py                   # Streamlit chat UI with reasoning panel
├── data_seed/
│   ├── policies/                # Markdown policy documents
│   └── structured/              # JSON org chart + role definitions
├── test/
│   ├── test_tools.py            # Unit tests for tools + schemas
│   ├── test_ingestion.py        # Unit tests for ingestion pipeline
│   └── test_api.py              # Integration tests (requires running server)
├── scripts/
│   ├── init.sh                  # Project initialization
│   └── run_app.sh               # Start backend + frontend
├── Dockerfile
├── docker-compose.yml
├── requirements.txt
└── ruff.toml
```

## Running Tests

```bash
# Unit tests (no server needed)
pytest test/test_tools.py test/test_ingestion.py -v

# Integration tests (requires running backend)
./scripts/run_app.sh &
pytest test/test_api.py -v
```

## Knowledge Base

The system ingests two types of data:

**Unstructured (Vector Search):**
- `HR_001_Employee_Handbook.md` — PTO, stipends, core hours, communication
- `IT_002_Information_Security_Policy.md` — Passwords, MFA, data classification, prohibited software

**Structured (JSON Lookup):**
- `org_chart.json` — 6 employees with IDs, titles, managers, locations
- `role_definitions.json` — 3 roles with required tools, permissions, first-week goals

## License

MIT
