# ChangeTools — eval report

_Generated 2026-05-06 11:49 UTC in 0.1s_

## Status: ❌ FAIL (6 assertions)

## Run context

- **Project**: `Obsidian Group v2` (`e23950df-bc4f-4f41-9261-bcffa752f26e`)
- **Brief**: `44d3643d-afd5-41e5-9a5f-2b9f56fe9fdb` (v5, status `ready`)
- **Provider/model**: `groq/llama-3.3-70b-versatile`
- **Embedding provider**: `local`
- **LangSmith tracing**: disabled
- **Metrics**:
  - `items_total`: 17
  - `citation_rate`: 1.0
  - `items_grounded`: 17
  - `evidence_chunks`: 42

## Cases

| # | Case | Result | Summary |
|---|------|--------|---------|
| 1 | Case 1 — KPI extraction | ✅ | 6 KPIs, 6 cited |
| 2 | Case 2 — Risk identification | ❌ | (no risks) |
| 3 | Case 3 — Stakeholder concerns | ❌ | 0 stakeholders: (none) |
| 4 | Case 4 — Conflict detection | ✅ | 0 conflicts surfaced |
| 5 | Case 5 — Citation faithfulness | ✅ | 10/10 sampled citations valid; 15 distinct total |
| 6 | Case 6 — Schema validity | ✅ | schema OK |

### Case 1 — KPI extraction

- **Result**: ✅ PASS
- **Summary**: 6 KPIs, 6 cited
- **Assertions**:
  - ✅ KPI mentions "digital adoption"
  - ✅ KPI mentions "training completion"
  - ✅ KPI mentions "sentiment"
  - ✅ KPI mentions "support handling time"
  - ✅ At least 4 KPIs extracted — _got 6_
  - ✅ Every KPI has at least 1 citation — _6 of 6 cited_

### Case 2 — Risk identification

- **Result**: ❌ FAIL
- **Summary**: (no risks)
- **Assertions**:
  - ❌ At least 3 risks present — _got 0_
  - ✅ Severities are valid (low/medium/high/critical)
  - ✅ risk_id values are unique
  - ❌ Every risk has at least one cited chunk — _0 cited of 0_

### Case 3 — Stakeholder concerns

- **Result**: ❌ FAIL
- **Summary**: 0 stakeholders: (none)
- **Assertions**:
  - ❌ At least 1 stakeholder identified — _got 0_
  - ❌ Sana Patel or a "regional"/role-impact stakeholder present — _names=[], roles=[]_
  - ❌ Elena Brooks or a comms/messaging stakeholder present — _names=[], roles=[]_
  - ❌ Every stakeholder has a sentiment

### Case 4 — Conflict detection

- **Result**: ✅ PASS
- **Summary**: 0 conflicts surfaced
- **Assertions**:
  - ✅ Conflicts list rendered (may be empty if LLM saw no disagreement)

### Case 5 — Citation faithfulness

- **Result**: ✅ PASS
- **Summary**: 10/10 sampled citations valid; 15 distinct total
- **Assertions**:
  - ✅ All 10 sampled citations resolve to a real chunk — _10/10 resolved_
  - ✅ At least 5 distinct citations across the brief — _got 15_

### Case 6 — Schema validity

- **Result**: ✅ PASS
- **Summary**: schema OK
- **Assertions**:
  - ✅ BriefContent re-validates after model_dump roundtrip
  - ✅ Brief status is 'ready' — _status=ready_
  - ✅ Executive summary is non-empty

