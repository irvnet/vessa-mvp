# City Development Watch

City development can be somewhat unclear — experimenting with LangGraph agents to make it easier to follow.

City Planning, Zoning, and Historic Preservation Commission agendas
are public, but buried in PDF files. This project
asks whether a simple conversational agent — grounded in those agendas, can help a resident learn about the changing city without reading every available PDF first.

**Live demo:** https://jc-development-watch.vercel.app

Try: *What is case Z2026-0025?*

---

## What this is

A small end-to-end spike: ingest Jersey City public board agendas, index them in Qdrant, wire up a
LangGraph agent with retrieval + web search, deploy to a public URL, and measure answer quality with RAGAS.
The repo includes the agent, eval artifacts, EC2/Terraform deploy path, and a Next.js chat UI.
More detail in [`DEPLOY.md`](DEPLOY.md) and [`01-spike-pipeline.ipynb`](01-spike-pipeline.ipynb).

---

## What's working

| Layer | Notes |
|-------|-------|
| Corpus | ~30 unique 2026 agenda PDFs, 3 boards |
| Retrieval | Ensemble dense + BM25 with Cohere rerank (0.906 faithfulness) |
| Agent | LangGraph — agenda search tool + Tavily for news context |
| Vectors | Qdrant Cloud |
| Backend | LangGraph Server on EC2 |
| Frontend | Next.js on Vercel, mobile-checked |

---

## Stack

| Component | Choice |
|-----------|--------|
| LLM | gpt-4o-mini |
| Embeddings | text-embedding-3-large |
| Orchestration | LangGraph (`create_agent`) |
| Tools | Qdrant retriever + Tavily |
| Vector DB | Qdrant Cloud |
| UI | FastAPI (local) · Next.js + Vercel (public) |
| Backend | EC2 + `langgraph up` |
| Packaging | uv |

---

## Eval results

| Config | Faithfulness |
|--------|-------------|
| Baseline (naive dense) | 0.831 |
| Ensemble + Cohere rerank | **0.906** |
| Prompt-tight v2 | 0.721 |

Artifacts in `data/`.

---

## Project layout

```
app/           # Agent, retriever, ingest, graph
frontend/      # Next.js chat UI
scripts/       # Indexing, EC2 bootstrap, verification
ami/           # Packer image for EC2
provision/     # Terraform
data/          # Inventory, eval sets (PDFs downloaded at runtime)
```

---

## Quick start

```bash
uv sync
cp .env.example .env
uv run python scripts/index_corpus.py
uv run uvicorn app.main:app --reload --port 8000
```

Frontend:

```bash
cd frontend && npm install && cp .env.local.example .env.local && npm run dev
```

---

## Objectives

What I set out to learn and ship:

| Objective | Outcome |
|-----------|---------|
| Frame a real community data problem | JC development agendas — public but hard to use |
| Build a grounded RAG pipeline over municipal PDFs | Ingest → chunk → Qdrant → cited answers |
| Add agentic tooling (retrieval + external search) | LangGraph agent with agenda + Tavily tools |
| Measure retrieval quality, not just vibes | RAGAS evals; naive vs ensemble comparison |
| Deploy to a public endpoint | EC2 backend + Vercel frontend, phone-checked |
| Document decisions and reproducibility | This repo, deploy guide, pipeline notebook |

---

## Roadmap

| Item | Status |
|------|--------|
| 2026 agenda ingest | ✅ |
| Public agent deploy | ✅ |
| Retrieval eval comparison | ✅ |
| Case extraction, map, alerts | Later |
| Multi-city / historical backfill | Later |

---

## Data attribution

City of Jersey City Open Data Portal ([data.jerseycitynj.gov](https://data.jerseycitynj.gov)).
Agenda data is public record.
