# ChangeTools — Obsidian Group MVP

Lightweight agentic AI workflow that ingests an organization's change-programme materials and produces a structured Change Strategy Brief plus a branded slide deck — with citations, validation, and an interactive chat for refinement.

> **Status:** MVP under active development for a 5-day technical assessment. See [`plan.md`](./plan.md) for architecture and [`tickets.md`](./tickets.md) for progress.

## Live demo

_Will be filled in once deployed (Phase 8)._

- Frontend: TBA (Vercel)
- API: TBA (Render)

## Stack

- **Frontend:** Next.js 15 (App Router) + TypeScript + Tailwind + shadcn/ui — deployed to Vercel
- **Backend:** Python 3.11+ FastAPI + LangGraph + LangChain — deployed to Render (Docker)
- **LLM:** Groq (`llama-3.3-70b-versatile`) for dev, abstraction for prod swap to OpenAI / Anthropic
- **Embeddings:** `sentence-transformers` (`BAAI/bge-small-en-v1.5`, 384-dim) local; OpenAI `text-embedding-3-small` for prod
- **Database:** Postgres + `pgvector` (Neon serverless in prod)
- **Storage:** Cloudflare R2 (S3-compatible)
- **Tracing:** LangSmith

See [`plan.md`](./plan.md) for the full architecture and [`finish_off.md`](./finish_off.md) for the production-swap notes.

## Local setup

### Prerequisites
- Node 20+, pnpm 9+
- Python 3.11+
- [`uv`](https://docs.astral.sh/uv/) (`curl -LsSf https://astral.sh/uv/install.sh | sh`)
- Docker (for local Postgres + pgvector)

### 1. Clone + env
```bash
git clone <repo>
cd obsidian
cp .env.example .env       # fill in GROQ_API_KEY, optionally LANGCHAIN_API_KEY + R2_*
```

### 2. Install dependencies
```bash
make install
```

### 3. Start the database
```bash
make db-up
make migrate
```

### 4. Run dev servers (in two terminals)
```bash
# Terminal 1 — backend
make dev-api

# Terminal 2 — frontend
make dev-web
```

Open http://localhost:3000.

## Run with the Obsidian inputs
1. Open the app, click **New Project**.
2. Upload `specs/Obsidian_Group_AI_Call_Notes.docx` and `specs/Obsidian_Group_Change_Data_Pack.xlsx`.
3. Upload `specs/Obsidian_Group_Logo.png` for the brand profile (or use the pre-seeded Obsidian palette).
4. Click **Generate Brief** — watch the LangGraph progress stream.
5. Inspect the brief, citations, and confidence indicators.
6. Click **Generate Deck** to produce the `.pptx` and PDF preview.
7. Use the chat panel to refine — try _"make the executive summary tighter"_ or _"add a slide on training completion gaps"_.

## Testing
```bash
make test           # unit + integration
make eval           # eval harness — produces eval_report.md
make lint           # ruff + eslint
make typecheck      # mypy + tsc
```

## Project structure
```
.
├── apps/
│   ├── api/          # FastAPI backend (Python)
│   └── web/          # Next.js frontend (TypeScript)
├── specs/            # Assessment input documents
├── examples/         # Generated example outputs
├── docs/             # Architecture diagrams, screenshots
├── plan.md           # Design + phasing
├── tickets.md        # Implementation tickets
├── finish_off.md     # Pre-delivery checklist + prod-swap notes
└── eval_report.md    # Latest evaluation run
```

## License
MIT (TBC).
