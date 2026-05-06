"""Section-drafting prompts.

Each prompt instructs the model to:

* ground every claim in one or more provided chunks (cite by ``chunk_id``)
* return JSON conforming to a section-specific Pydantic schema
* assign per-item confidence (high|medium|low) reflecting evidence strength

The chunks are formatted with a stable ``[chunk:UUID]`` marker the LLM is
told to copy into ``cited_chunk_ids`` when citing.
"""

from __future__ import annotations

VERSION = "2026-05-02.1"


SYSTEM = """You are an experienced organisational change strategist.
You write structured strategy briefs grounded *only* in the provided source
chunks. You do not invent stakeholder names, KPI values, or risks. When the
sources do not support a claim, you say so or omit the item.

You always:
- Quote-back evidence by referencing chunk_id values from the provided chunks
- Assign per-item confidence: "high" (multiple direct sources), "medium"
  (one clear source), "low" (inference from indirect signals)
- Output strictly valid JSON matching the schema you are given
- Use crisp, executive language (no filler, no hedging adverbs)
"""


CHUNKS_HEADER = """## Available source chunks
Each chunk is preceded by a stable identifier in the form [chunk:UUID]. When
you cite evidence, list those UUIDs in the cited_chunk_ids field.

"""


# ---------------------------------------------------------------------------
# Per-section instructions
# ---------------------------------------------------------------------------

EXECUTIVE_SUMMARY = """## Task
Write an executive summary of the change programme captured in the chunks.

Output JSON with:
- headline (one strong sentence; <= 140 chars)
- body (2-4 sentences; <= 1200 chars; covers what is changing, why now,
  and the headline state of progress)
- cited_chunk_ids: chunk UUIDs the summary draws on (1-5)
- confidence: high|medium|low
"""

THEMES = """## Task
Identify 3-5 cross-cutting themes that emerge from the chunks (e.g.
"messaging drift", "regional variance", "training velocity"). Each theme
must be supported by at least one chunk.

Output JSON with field ``items``: a list of:
- title (<= 80 chars)
- description (<= 800 chars; concrete, references the source signal)
- cited_chunk_ids: UUIDs (>= 1)
- confidence: high|medium|low
"""

RISKS = """## Task
Extract risks from the chunks. Use the existing risk_id values verbatim
(e.g. R-01, R-02) when present in the source. Otherwise, mint sequential
ids R-01, R-02, ... in priority order.

Output JSON with field ``items``: a list of:
- risk_id (e.g. "R-01")
- title (<= 100 chars)
- description (<= 800 chars; what could go wrong, plus current signal)
- severity: low|medium|high|critical
- likelihood: high|medium|low
- owner (string or null)
- mitigation (proposed mitigation, <= 600 chars; or null)
- cited_chunk_ids: UUIDs (>= 1)
- confidence: high|medium|low
"""

STAKEHOLDERS = """## Task
Map stakeholders the chunks call out by name or role. Capture their
position on the change programme.

Output JSON with field ``items``: a list of:
- name (string; if no name, use a role label like "Frontline managers")
- role (their role or function)
- concern (their stated concern or position; <= 600 chars)
- sentiment: positive|neutral|concerned|resistant
- cited_chunk_ids: UUIDs (>= 1)
- confidence: high|medium|low
"""

KPIS = """## Task
Extract the KPIs the programme is tracking. Use the values present in the
chunks; do not estimate. If the target is not stated, leave target_value
null.

Output JSON with field ``items``: a list of:
- name (<= 80 chars)
- current_value (string capturing the current value, e.g. "42%")
- target_value (string or null)
- gap (qualitative gap description, or null)
- trend (e.g. "up since Q2", or null)
- cited_chunk_ids: UUIDs (>= 1)
- confidence: high|medium|low
"""

RECOMMENDATIONS = """## Task
Given the themes, risks, KPIs, and stakeholder concerns surfaced in the
chunks, propose 3-5 recommendations the change programme should act on
within the next 30-90 days.

Output JSON with field ``items``: a list of:
- title (<= 100 chars; imperative, e.g. "Stand up regional change champion network")
- description (<= 800 chars; what to do, expected effect)
- priority: P0|P1|P2|P3
- addresses_risks: list of risk_id strings (may be empty)
- cited_chunk_ids: UUIDs that motivate the recommendation (>= 1)
- confidence: high|medium|low
"""


SECTION_PROMPTS: dict[str, str] = {
    "executive_summary": EXECUTIVE_SUMMARY,
    "themes": THEMES,
    "risks": RISKS,
    "stakeholders": STAKEHOLDERS,
    "kpis": KPIS,
    "recommendations": RECOMMENDATIONS,
}


CONFLICT_DETECTION = """You are reviewing two pools of evidence about the
same programme: one from call notes (qualitative) and one from the data pack
(quantitative).

Surface disagreements where the two pools tell different stories about the
same fact (e.g. a KPI target that is stated differently, a stakeholder whose
sentiment differs across sources, a milestone date that doesn't match).

Do NOT fabricate conflicts. If the sources align, return an empty list.

Output JSON with field ``items``: a list of:
- topic (one-line description of the disagreement, <= 200 chars)
- position_a (call-notes view, <= 600 chars)
- position_b (data-pack view, <= 600 chars)
- sources_a_chunk_ids: UUIDs from the call-notes pool that support position_a
- sources_b_chunk_ids: UUIDs from the data-pack pool that support position_b
- suggested_resolution (which side to defer to and why, or null)
"""


CITATION_GROUNDING = """You are an evidence auditor. Given a claim and a
candidate source chunk, decide whether the chunk directly supports the claim.

Output JSON:
- supported: true|false
- reasoning: <= 300 chars explaining the call
- confidence: high|medium|low
  - high: the chunk states the claim explicitly
  - medium: the chunk implies it without ambiguity
  - low: the chunk only weakly suggests it
"""
