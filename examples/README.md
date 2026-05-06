# Examples

Reference outputs from running ChangeTools against the Obsidian Group source
documents (`Obsidian_Group_AI_Call_Notes.docx` + `Obsidian_Group_Change_Data_Pack.xlsx`).

| File | What it is |
|---|---|
| `obsidian-brief.json` | Raw `Brief` structure persisted in Postgres — every field, including per-claim `evidence` chunk references and `confidence` ratings |
| `obsidian-brief.md` | Human-readable rendering of the same brief |
| `obsidian-deck.pptx` | Branded slide deck rendered from the brief — title, executive summary, themes, KPIs, recommendations slides with per-slide source footers |

These are real outputs from a Groq `llama-3.3-70b-versatile` run, not curated.

## Known content gap in this snapshot

The `risks` and `stakeholders` sections in this particular run are empty. That
isn't a code bug — Groq's free-tier daily token quota (100K TPD) was exhausted
mid-run, and both the structured-output path and the JSON-mode fallback got
HTTP 429s. The pipeline continues with the sections it could render and the
eval harness flags the gaps explicitly.

A run with quota headroom (or with `LLM_PROVIDER=openai`) populates all
sections. The structured-output → JSON-mode fallback in
`infrastructure/llm/structured.py` handles Groq's schema-rejection edge case;
the only thing that can't be worked around is total API unavailability.

To regenerate from your own dev env:

```bash
make dev-api &
curl -N -X POST http://localhost:8000/projects/<your-project-id>/brief
# then inspect via GET /briefs/<id>
```

…and overwrite these files with `make examples` (or copy from the API
storage directory).
