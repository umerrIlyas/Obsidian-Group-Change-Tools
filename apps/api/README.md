# `apps/api` — ChangeTools backend

FastAPI + LangGraph + LangChain. See top-level [`plan.md`](../../plan.md) for architecture.

## Local development

```bash
uv sync                    # install deps in .venv
uv run uvicorn changetools.main:app --reload
```

Or from the repo root:

```bash
make dev-api
```

## Layout

```
src/changetools/
├── api/              # HTTP boundary (FastAPI routers, DTOs, deps)
├── services/         # Use-cases — orchestrate agents + repos + storage
├── agents/           # LangGraph workflows + prompts + tools
├── domain/           # Pydantic domain models
├── repositories/     # DB access
├── infrastructure/   # External adapters (LLM, embeddings, storage, parsing, rendering, tracing)
├── config.py         # Typed settings (pydantic-settings)
├── core/             # logging, errors, ids, request_id middleware
└── main.py           # FastAPI app factory
```

## Tests

```bash
uv run pytest                    # unit + integration (skip integration with -m 'not integration')
uv run pytest tests/eval -v      # eval harness
```
