# FinVault AI

> A production-grade financial research agent for finance, investment, and strategy teams.
> Built for Hack Geek Room — Challenge 3: Financial & Market Research Agent.

---

## Overview

FinVault AI synthesizes real financial documents such as annual reports, earnings call transcripts, and market disclosures to deliver structured, decision-ready insights with traceable sources.

The system behaves like a junior financial research assistant: it reasons across multiple sources, detects inconsistencies, maintains user preferences across sessions, and produces structured analytical outputs rather than conversational summaries.

**Core principle:** Production patterns over clever hacks. Reliability over raw performance.

---

## 🚀 Quick Start

### Prerequisites
- Python 3.10+
- Node.js 18+
- Groq API Key ([Free signup](https://console.groq.com))
- PostgreSQL (or use free tier)
- Qdrant Cloud account (free tier available)

### Local Development Setup

**Backend:**
```bash
cd backend
python -m venv venv
source venv/bin/activate  # or `venv\Scripts\activate` on Windows
pip install -r requirements.txt
uvicorn app.main:app --reload
```

**Frontend:**
```bash
cd frontend
npm install
npm run dev
```

### Complete Setup
See [DEVELOPMENT.md](./DEVELOPMENT.md) for detailed step-by-step instructions including environment configuration, data ingestion, and testing.

### First Steps
1. Configure `.env` files with API keys
2. Ingest financial documents: `python backend/app/data/scripts/ingest_narratives.py`
3. Start backend: `uvicorn app.main:app --reload`
4. Start frontend: `npm run dev`
5. Open [http://localhost:3000](http://localhost:3000)
6. Ask a financial question
7. Set memory preferences
8. Run queries in both Quick and Deep modes

---

## What Is Actually Built (MVP Scope)

### Real Data — No Placeholder Retrieval

* **Qdrant Cloud** stores real chunked and embedded financial documents:

  * 2–3 companies minimum
  * Annual filings + earnings transcripts per company
  * Documents are cleaned, chunked (~500 tokens with ~50 overlap), embedded, and indexed before demo
* **Neon PostgreSQL** stores persistent user preferences (risk tolerance, KPIs, sectors, geography)

  * Memory survives page refreshes and session restarts
* **Dual model routing is real** (not simulated):

  * Quick Mode → `llama-3.1-8b-instant` via Groq
  * Deep Mode → `llama-3.3-70b-versatile` via Groq
  * Each query logs model, latency, and token usage

---

## Key Features

### Dual Research Modes

**Quick Mode** — Target latency: < 30 seconds

* Earnings summaries
* KPI extraction (revenue, margins, YoY growth)
* Key risk highlights
* Fast structured responses

**Deep Mode** — Target latency: < 3 minutes

* Fundamental financial analysis across documents
* Peer benchmarking with citations
* Bull vs. bear thesis generation
* Scenario reasoning based on retrieved context
* Detection of potentially conflicting statements across sources

Mode classification is automatic and logged.

---

### Persistent Financial Memory

Stored in **Neon PostgreSQL** and injected into query context:

* Risk tolerance (conservative, moderate, aggressive)
* Preferred KPIs (e.g., EBITDA, ROE, FCF)
* Sector interests
* Geographic preferences

Preferences persist across sessions and influence future analyses.

---

### Structured Financial Output

Outputs follow consistent schemas such as:

* Investment-style analysis memos
* Risk summaries with cited sources
* Comparative peer analysis tables
* Confidence indicators
* Explicit assumption disclosure

Claims are grounded in retrieved documents with citations where applicable.

---

### Production Observability

Each response includes a metadata block:

* Mode used
* Model name
* Latency
* Token usage
* Estimated marginal cost (generally zero under free-tier usage)
* Source references

---

## Technical Stack

| Layer           | Technology                                           | Purpose                                      |
| --------------- | ---------------------------------------------------- | -------------------------------------------- |
| Agent Framework | LangGraph (Python)                                   | Stateful orchestration and reasoning control |
| LLM Provider    | Groq API                                             | Free-tier inference with fast latency        |
| Quick Model     | llama-3.1-8b-instant                                 | Fast summarization and extraction            |
| Deep Model      | llama-3.3-70b-versatile                              | Multi-step reasoning and analysis            |
| Embeddings      | Open embedding model (e.g., BGE-small or equivalent) | Retrieval grounding                          |
| Vector DB       | Qdrant Cloud                                         | Financial document semantic search           |
| Relational DB   | Neon PostgreSQL                                      | User memory, logs, caching                   |
| Backend         | FastAPI                                              | API + agent orchestration                    |
| Frontend        | Next.js + TypeScript                                 | Chat UI and report viewer                    |
| Deployment      | Render / Railway + Vercel                            | Live demo hosting                            |

---

## System Architecture

```
User Query
  │
  ▼
LangGraph Agent
  ├─ Query classification (Quick / Deep)
  ├─ Memory injection (Neon)
  ├─ Retrieval tool
  │    ├─ Query embedding
  │    ├─ Qdrant vector search
  │    └─ Context assembly
  ├─ Reasoning
  │    ├─ Quick → single-pass reasoning
  │    └─ Deep → multi-step reasoning
  ├─ Structured output generation
  ├─ Memory update
  └─ Metrics logging
  ▼
Structured response + citations + confidence
```

---

## Data Pipeline

### Documents Used (MVP)

* Publicly accessible company filings
* Earnings transcripts from investor relations sources
* Limited but realistic dataset (depth over breadth)

### Processing Steps

1. Clean raw documents
2. Chunk (~500 tokens with ~50 overlap)
3. Generate embeddings
4. Store in Qdrant with metadata
5. Extract structured KPIs into PostgreSQL where feasible

---

## Project Structure

### Backend
```
backend/
├── app/
│   ├── main.py
│   ├── config.py
│   ├── api/
│   │   └── routes.py          # FastAPI endpoints
│   ├── core/
│   │   ├── db.py              # PostgreSQL connection
│   │   ├── llm.py             # Groq integration
│   │   ├── vector.py          # Qdrant integration
│   │   └── retrieval.py       # Hybrid retrieval engine
│   ├── agents/
│   │   └── graph.py           # LangGraph orchestration
│   ├── utils/
│   │   └── helpers.py
│   └── data/
│       └── scripts/           # Data ingestion scripts
├── requirements.txt
├── README.md                  # Backend documentation
└── .env.example
```

**[Backend Setup & API Reference →](./backend/README.md)**

### Frontend
```
frontend/
├── src/
│   ├── app/
│   │   ├── page.tsx           # Main query interface
│   │   ├── layout.tsx         # Root layout
│   │   └── globals.css        # Global styles
│   ├── components/
│   │   ├── QueryPanel.tsx          # Query input + mode
│   │   ├── ResultsView.tsx         # Structured results
│   │   ├── MemoryPreferencesSidebar.tsx
│   │   ├── SourcesView.tsx         # Sources & citations
│   │   ├── QueryHistory.tsx        # Query history
│   │   └── MetricsFooter.tsx       # Performance metrics
│   ├── hooks/
│   │   └── index.ts           # React Query + localStorage
│   ├── lib/
│   │   ├── api.ts             # Axios API client
│   │   └── queryClient.ts     # React Query config
│   └── types/
│       └── index.ts           # TypeScript interfaces
├── package.json
├── tsconfig.json
├── tailwind.config.ts
├── next.config.ts
└── README.md
```

**[Frontend Setup & Components →](./frontend/README.md)**

---

## Memory Design

### PostgreSQL Tables

**user_preferences**

* user_id
* risk_tolerance
* preferred_kpis
* sectors
* geographies
* updated_at

**query_logs**

* query
* mode
* model
* latency
* tokens_used
* estimated_cost
* timestamp

---

## Cost Optimization Strategy

* Tiered model routing
* Retrieval-first design
* Response caching
* Token budgeting
* Full system designed to stay within free-tier limits

Estimated marginal demo cost: effectively zero.

---

## Reliability Measures

* Retrieval grounding reduces hallucination risk
* API retry logic on model failures
* Memory read fallback to defaults
* Clear error messaging (no silent failures)

---

## Deployment Checklist

* Vector DB populated
* Database schema migrated
* Backend deployed and healthy
* Frontend connected
* Environment variables configured
* Memory persistence verified
* End-to-end test completed

---

## Demo Flow

1. Set investor preference (e.g., conservative tech investor)
2. Run quick earnings summary
3. Perform deep comparative analysis
4. Demonstrate memory persistence
5. Show cost / latency logging

Focus: reliability, traceability, and structured insight.

---

## Complete MVP Status

### ✅ Backend (Production-Ready)
- **Phase 1**: Code audit completed (16 issues fixed)
- **Phase 2**: Hybrid retrieval fully implemented (8 features)
- **Production Hardening**: 10-point checklist completed
- **E2E Testing**: 3/3 tests passing ✅
- **Deployment**: Ready for Render/Railway
- [Backend Documentation →](./backend/README.md)

### ✅ Frontend (Complete)
- **6 Core Components**: QueryPanel, ResultsView, SourcesView, QueryHistory, MemoryPreferencesSidebar, MetricsFooter
- **State Management**: React Query + localStorage
- **Type Safety**: 100% TypeScript
- **Styling**: Tailwind CSS with responsive design
- **API Integration**: Axios with error handling
- **Deployment**: Ready for Vercel
- **Build Status**: Production build passing ✓
- [Frontend Documentation →](./frontend/README.md)

### ✅ Infrastructure
- **Backend**: FastAPI with full error handling and observability
- **Frontend**: Next.js with TypeScript and production build passing
- **Database**: PostgreSQL schema ready with migration scripts
- **Vector DB**: Qdrant integration with real financial documents
- **Environment**: .env template files with clear configuration guide
- **API**: Fully documented with Swagger UI at `/docs`

### 📚 Documentation
- [Development Guide](./DEVELOPMENT.md) — Complete setup, configuration, and troubleshooting
- [Backend README](./backend/README.md) — Backend API reference and architecture
- [Frontend README](./frontend/README.md) — Frontend components, setup, and development guide

### 🚀 Quick Start

```bash
# Backend Setup
cd backend
python -m venv venv
source venv/bin/activate       # macOS/Linux
# venv\Scripts\activate         # Windows
pip install -r requirements.txt
uvicorn app.main:app --reload

# Frontend Setup (new terminal)
cd frontend
npm install
npm run dev

# Access
Frontend:  http://localhost:3000
Backend:   http://localhost:8000
API Docs:  http://localhost:8000/docs
```

**For detailed setup including environment variables, data ingestion, and troubleshooting, see [DEVELOPMENT.md](./DEVELOPMENT.md)**

### 📊 Project Statistics

| Component | Status | Details |
|-----------|--------|---------|
| Backend | ✅ Complete | FastAPI + LangGraph + PostgreSQL + Qdrant |
| Frontend | ✅ Complete | Next.js 14 + TypeScript + Tailwind + React Query |
| Type Coverage | ✅ Complete | 100% TypeScript with strict mode |
| Tests | ✅ Complete | 3/3 E2E tests passing |
| Documentation | ✅ Complete | 4 comprehensive guides |
| Docker Setup | ✅ Complete | docker-compose with all services |
| Production Harden | ✅ Complete | 10-point security & stability checklist |

---

## Judging Criteria Alignment

✅ **Strong RAG** — Hybrid numeric + narrative retrieval with real documents in Qdrant Cloud
✅ **Cost-Efficient** — Groq free-tier models with token tracking and budget awareness
✅ **Persistent Memory** — PostgreSQL + localStorage for user preferences across sessions
✅ **Clean Architecture** — Modular FastAPI + Next.js separation with clear interfaces
✅ **Deployment-Ready** — Docker, environment configs, health checks, error handling
✅ **Production Quality** — Type-safe code, comprehensive error handling, observability

---

## Project Philosophy

* **Production over prototype** — Real data, real deployment, not MVPs
* **Reliability over novelty** — Comprehensive error handling across all layers
* **Explainability over opacity** — Full source citations, contradiction detection, cost tracking
* **Cost-awareness from day one** — Free-tier design, token budgeting, latency optimization
* **Structured reasoning over conversational fluff** — Financial insights, not chatbot responses

---

FinVault AI demonstrates practical, deployable financial AI engineering at production quality for the Hack Geek Room Challenge.

[**→ Start Development**](./DEVELOPMENT.md)
