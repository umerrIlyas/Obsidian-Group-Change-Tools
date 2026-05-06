# Observability

ChangeTools instruments the LangChain pipeline end-to-end so every brief
generation, refinement chat turn, and tool call is captured as a trace.

## LangSmith

LangSmith is wired through environment variables (no code change needed to
enable). It captures:

- Each generation graph node (`load_context`, `retrieve_evidence`,
  `draft_sections`, `validate`, `cite_evidence`, `detect_conflicts`,
  `assemble`, `persist`) as a distinct span
- Every LLM call with input/output, including retries
- Every tool call from the refinement ReAct agent
  (`retrieve_evidence`, `read_brief_section`, `update_brief_section`,
  `regenerate_deck`, `list_*`)
- The full message history for chat sessions

### Enable locally

In `.env`:

```ini
LANGCHAIN_TRACING_V2=true
LANGCHAIN_API_KEY=lsv2_pt_...     # from https://smith.langchain.com/settings
LANGCHAIN_PROJECT=changetools-obsidian
```

Restart the API. Subsequent runs will appear in the LangSmith dashboard
under the configured project.

### Reading a trace

Open <https://smith.langchain.com/o/-/projects/p/changetools-obsidian>.

For a brief generation, the trace tree looks like:

```
brief.generate (project_id=…, brief_id=…)
├── load_context                       ~50ms
├── retrieve_evidence                  ~250ms (8 parallel pgvector queries)
├── draft_sections                     ~30s   (semaphore=2 LLM calls)
│   ├── ChatGroq.invoke (executive_summary)
│   ├── ChatGroq.invoke (themes)
│   ├── ChatGroq.invoke (risks)
│   ├── ChatGroq.invoke (stakeholders)
│   ├── ChatGroq.invoke (kpis)
│   └── ChatGroq.invoke (recommendations)
├── validate                           ~5ms
├── cite_evidence                      ~10ms
├── detect_conflicts                   ~8s    (1 LLM call)
├── assemble                           ~5ms
└── persist                            ~30ms
```

For a chat refinement, the trace tree is the ReAct loop:

```
chat.send_message (session_id=…)
├── ChatGroq.invoke (planning)
├── tool: retrieve_evidence
├── ChatGroq.invoke (synthesizing)
├── tool: update_brief_section
└── ChatGroq.invoke (final answer)
```

### Trace screenshots

Add screenshots to this directory once you have traces in your dashboard:

- `trace-generation.png` — a full brief.generate run
- `trace-refinement.png` — a chat refinement that updates a section

These are referenced from the submission README.

## Eval reports

`make eval` writes `eval_report.md` at the repo root. The report includes:

- Brief metrics (`citation_rate`, `evidence_chunks`, `conflicts_detected`)
- Pass/fail per case with assertion-level detail
- The current LangSmith dashboard URL (when tracing is enabled)

Re-run after each pipeline change to spot regressions early.

## Sentry (optional)

Not wired by default. To add error tracking: install `sentry-sdk[fastapi]`,
call `sentry_sdk.init(dsn=...)` in `main.py` lifespan, and forward the same
events from `core/middleware.py`. Skipped for the MVP because LangSmith
already surfaces every LLM/tool failure with full context, and FastAPI's
default error handlers cover everything else.
