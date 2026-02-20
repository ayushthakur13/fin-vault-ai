# FinVault AI

> A production-grade financial research agent for finance, investment, and strategy teams.
> Built for Hack Geek Room — Challenge 3: Financial & Market Research Agent.

---

## Overview

FinVault AI synthesizes real financial documents such as annual reports, earnings call transcripts, and market disclosures to deliver structured, decision-ready insights with traceable sources.

The system behaves like a junior financial research assistant: it reasons across multiple sources, detects inconsistencies, maintains user preferences across sessions, and produces structured analytical outputs rather than conversational summaries.

**Core principle:** Production patterns over clever hacks. Reliability over raw performance.

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

## Backend Project Structure

```
backend/
├── app/
│   ├── main.py
│   ├── config.py
│   ├── api/
│   ├── core/
│   ├── agents/
│   ├── utils/
│   └── data/
├── requirements.txt
├── .env.example
└── .env
```

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

## Judging Criteria Alignment

* Strong RAG over real documents
* Cost-efficient inference strategy
* Persistent memory usage
* Clean architecture
* Deployment readiness

---

## Project Philosophy

* Production over prototype
* Reliability over novelty
* Explainability over opacity
* Cost-awareness from day one
* Structured reasoning over conversational fluff

FinVault AI is designed to demonstrate practical, deployable financial AI engineering rather than experimental AI demos.
