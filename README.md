# ChangeTools

An agentic AI workflow that ingests an organization's change-programme materials
(call notes + data pack) and produces a structured **Change Strategy Brief** plus
a **branded slide deck**, with full source citations, schema validation,
LangSmith tracing, and an interactive chat for refinement.

Built as a 5-day technical assessment for Obsidian Group; the design generalizes
to any change-management programme.

## Live demo

- **Frontend:** _TBA — Vercel deploy URL_
- **API:** _TBA — Render deploy URL_
- **LangSmith dashboard:** [`changetools-obsidian`](https://smith.langchain.com/o/-/projects/p/changetools-obsidian)

## Demo walkthrough

1. **Create project**, upload the two source documents (`.docx` call notes + `.xlsx` data pack)
2. **Apply the Obsidian brand preset** (one click — palette + logo + Aptos fonts) or upload a custom logo
3. **Generate Brief** — watch the LangGraph pipeline stream over SSE: `load_context → retrieve_evidence → draft_sections → validate → cite_evidence → detect_conflicts → assemble → persist`
4. **Inspect the brief** — every claim is cited with a hover-popover showing the source chunk + confidence
5. **Generate Deck** — branded `.pptx` with title slide, exec summary, themes, KPI table, risks, stakeholders, recommendations, conflict callouts, and per-slide source footers. PDF preview rendered in-page (where LibreOffice is installed)
6. **Refine with chat** — *"Tighten the executive summary"* or *"List the top 3 risks"*. The ReAct agent calls tools (`retrieve_evidence`, `read_brief_section`, `update_brief_section`, `regenerate_deck`); each call appears live with arguments + results, and brief edits create a new version (history preserved via the version selector)
7. **Run the eval harness** — `make eval` writes a markdown report scoring the brief on 6 cases (KPI extraction, risk identification, stakeholder concerns, conflict detection, citation faithfulness, schema validity)

## Architecture

```
┌────────────────┐   ┌─────────────────────────────────────────────┐   ┌──────────────┐
│  Next.js 15    │   │           FastAPI (Python 3.11+)           │   │  Postgres +  │
│  App Router    │──▶│                                             │──▶│   pgvector   │
│  SSE streams   │   │  ┌─────────┐  ┌──────────┐  ┌────────────┐  │   │ (Neon prod)  │
└────────────────┘   │  │ Routers │─▶│ Services │─▶│Repositories│  │   └──────────────┘
                     │  └─────────┘  └──────────┘  └────────────┘  │
                     │       │             │              │        │
                     │       ▼             ▼              ▼        │   ┌──────────────┐
                     │  ┌─────────┐  ┌──────────┐  ┌────────────┐  │   │  Cloudflare  │
                     │  │ LangGraph│ │Renderers │  │  Storage   │──┼──▶│  R2 / Local  │
                     │  │  agents  │ │ pptx/pdf │  │            │  │   └──────────────┘
                     │  └─────────┘  └──────────┘  └────────────┘  │
                     │       │             │                       │
                     │       ▼             ▼                       │   ┌──────────────┐
                     │  ┌─────────┐  ┌──────────┐                  │   │   LangSmith  │
                     │  │  LLM    │  │Embeddings│                  ├──▶│   tracing    │
                     │  │ Groq /  │  │BAAI/BGE  │                  │   └──────────────┘
                     │  │ OpenAI  │  │  local   │                  │
                     │  └─────────┘  └──────────┘                  │
                     └─────────────────────────────────────────────┘
```

**Layers:**

- `api/routers/` — REST + SSE endpoints, no logic
- `api/schemas/` — request/response DTOs
- `services/` — use-case orchestration (per feature: brief, deck, chat, brand…)
- `agents/generation/` — brief-generation LangGraph (8 nodes + 1 retry loop)
- `agents/refinement/` — chat ReAct agent + tool definitions
- `infrastructure/{llm,embeddings,storage,parsing,rendering,branding}/` — provider-swappable adapters
- `repositories/` — async SQLAlchemy with Pydantic domain models at the boundary
- `domain/` — pure Pydantic models (no DB / framework deps)

## Stack

| Layer | Tech | Notes |
|---|---|---|
| Frontend | Next.js 15 + TypeScript + Tailwind + shadcn-style UI | App Router, typed routes, SSE async generators |
| Backend | FastAPI + Pydantic v2 | async, structlog JSON, X-Request-Id middleware |
| Agents | LangGraph + LangChain | ReAct + linear pipelines, both traced |
| LLM | Groq (`llama-3.3-70b-versatile`) | Provider-abstracted; OpenAI/Anthropic/Ollama via `LLM_PROVIDER` env |
| Embeddings | `sentence-transformers` (`BAAI/bge-small-en-v1.5`, 384-dim) | OpenAI `text-embedding-3-small` for prod |
| Database | Postgres 16 + pgvector (HNSW) | Neon serverless in prod |
| Storage | Cloudflare R2 (S3-compatible) | `LocalFileStorage` for dev; auto-selects via env |
| Slide rendering | python-pptx + LibreOffice (headless → PDF) | LibreOffice baked into Docker image |
| Tracing | LangSmith | Every graph node, tool call, LLM call (incl. retries) |

## Local setup

### Prerequisites

- Node 20+, pnpm 9+
- Python 3.11+
- [`uv`](https://docs.astral.sh/uv/): `curl -LsSf https://astral.sh/uv/install.sh | sh`
- Docker (local Postgres) — or any Postgres with `pgvector`
- LibreOffice (optional, for in-browser PDF preview): `brew install --cask libreoffice` — without it, the deck still generates as `.pptx`, the UI just hides the PDF iframe

### Steps

```bash
# 1. clone + configure env
git clone <repo-url> changetools && cd changetools
cp .env.example .env
# fill in GROQ_API_KEY (free tier from https://console.groq.com)
# optional: LANGCHAIN_API_KEY for tracing

# 2. install
make install

# 3. database
make db-up
make migrate

# 4. dev servers (two terminals)
make dev-api      # http://localhost:8000
make dev-web      # http://localhost:3000
```

Open <http://localhost:3000> and follow the demo walkthrough above.

## Eval harness

```bash
make eval
# writes ./eval_report.md
```

Six cases:

1. **KPI extraction** — expected KPIs present + cited
2. **Risk identification** — ≥3 risks, valid severities, unique IDs
3. **Stakeholder concerns** — Sana Patel / Elena Brooks (or matching roles) surfaced
4. **Conflict detection** — disagreements between call notes and data pack rendered with both sides cited
5. **Citation faithfulness** — sampled chunk_ids resolve to real chunks in the RAG index
6. **Schema validity** — `BriefContent` re-validates after JSON roundtrip

A failing case writes the assertion that failed plus the actual value, so regressions are easy to triage.

## Production swap notes

Every external dependency is behind a Protocol so you can swap without touching domain code:

| Concern | Dev default | Prod swap |
|---|---|---|
| LLM provider | Groq (`llama-3.3-70b-versatile`) | `LLM_PROVIDER=openai` / `anthropic`; set the matching API key |
| Embeddings | `BAAI/bge-small-en-v1.5` (local CPU) | `EMBEDDING_PROVIDER=openai`; re-embed with `make reembed` |
| Storage | Local filesystem | Set `R2_ACCOUNT_ID/R2_ACCESS_KEY_ID/...` — auto-selects S3 client |
| Database | Local Docker Postgres | Neon `DATABASE_URL` (any pgvector-enabled Postgres) |
| Tracing | Off | `LANGCHAIN_TRACING_V2=true` + `LANGCHAIN_API_KEY` |

The `domain/`, `services/`, and `repositories/` layers don't change.

### LLM-provider robustness

Some providers (notably Groq with `llama-3.3-70b-versatile`) reject complex
nested Pydantic schemas via their structured-output endpoint. The
`infrastructure/llm/structured.py` helper transparently falls back to JSON
mode + manual `model_validate_json` when this happens, so the pipeline keeps
producing valid structured output without provider-specific branching.
Switching `LLM_PROVIDER` is a single env-var change.

## Project structure

```
.
├── apps/
│   ├── api/                              # FastAPI backend
│   │   ├── alembic/versions/             # 7 migrations
│   │   ├── src/changetools/
│   │   │   ├── agents/{generation,refinement}/   # LangGraph pipelines
│   │   │   ├── api/{routers,schemas}/
│   │   │   ├── core/                     # logging, errors, middleware
│   │   │   ├── domain/                   # Pydantic models (Brief, Deck, …)
│   │   │   ├── eval/                     # eval harness + report writer
│   │   │   ├── infrastructure/           # llm/embeddings/storage/rendering/…
│   │   │   ├── repositories/             # async SQLAlchemy
│   │   │   ├── services/                 # business logic
│   │   │   ├── config.py
│   │   │   └── main.py
│   │   └── tests/                        # 49 unit tests
│   └── web/                              # Next.js 15 frontend
├── docs/observability.md                 # LangSmith / Sentry notes
├── examples/                             # Reference brief + deck outputs
├── specs/                                # Assessment input docs (gitignored)
├── docker-compose.yml                    # Postgres + pgvector
├── render.yaml                           # Render blueprint for one-click deploy
└── Makefile                              # All dev commands
```

## Testing

```bash
make test       # 49 unit tests (backend) + frontend
make lint       # ruff + eslint
make typecheck  # mypy + tsc
```

## License

MIT.
