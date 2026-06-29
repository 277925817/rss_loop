# ADR-003: Resolve Product Contract Drift

## Status

Accepted

## Date

2026-06-30

## Context

The L3 control plane passed loop-readiness checks, but a documentation review
found product-contract drift that would make Product Delivery ambiguous:

- Source delete behavior conflicted across PRD, API, UI and task documents.
- LLM scoring failure behavior conflicted between fallback scoring and an
  undefined `llm_error` marker.
- Translated DTO rules disagreed on whether `summary_zh` was required.
- TestReport required timeout classification but the closed enum omitted
  `timeout`.
- Refresh/run summary evidence was required internally while public API
  non-goals forbid progress and processing-log endpoints.

These conflicts affect API, data, UI and test contracts, so they require a
recorded human-approved documentation correction before implementation agents
can proceed safely.

## Decision

Adopt these contract corrections:

- Source deletion uses internal soft delete: `source.is_deleted = 1` and
  `source.is_enabled = 0`. `GET /api/sources` returns only non-deleted sources,
  but includes disabled non-deleted sources. `is_deleted` is never exposed by
  API/UI. Historical `news_item` records remain visible.
- Soft-deleted RSS URLs remain reserved. A future reset-configuration flow may
  define restoration, but MVP re-add attempts return duplicate conflict.
- LLM scoring retry failure writes system fallback facts:
  `score = 0`, `is_selected = 0`, `pipeline_state = scored`, and a failed
  `processing_log(stage = score)` with fixed `error_category`. Invalid LLM
  returned scores are never written.
- LLM translation retry failure keeps `pipeline_state = fetched`, writes no
  partial Chinese fields, sets `has_translate_failed = 1`, and records
  `processing_log(stage = translate, success = 0)`.
- `status = translated` requires non-empty `title_zh`, `summary_zh`, and
  `content_zh`. Translated list/detail responses include `summary_zh`;
  translated detail responses include `content_zh`.
- TestReport `error_category` includes `timeout`.
- Refresh/run summary facts are internal evidence from pipeline-owned records,
  structured reports, or processing logs. Public API remains limited to
  `POST /api/refresh -> { refreshed_at }`.

## Alternatives Considered

### Physical source deletion

- Pros: Simple list behavior.
- Cons: Weakens historical traceability and complicates default-source seed
  behavior.
- Rejected because the MVP must preserve historical news and avoid restoring a
  deleted default source.

### Keep scoring failures in raw state

- Pros: Strictly distinguishes successful scoring from fallback.
- Cons: Conflicts with the existing `raw -> scored -> fetched` finite-state
  model and leaves low-value failed items repeatedly eligible for scoring.
- Rejected in favor of an explicit fallback score with failed processing log.

### Make `summary_zh` optional for translated detail

- Pros: Slightly smaller detail payload.
- Cons: Contradicts UI card requirements and status projection rules.
- Rejected because `translated` should mean all translated fields are complete.

## Consequences

- Product Delivery agents have one deterministic contract for source deletion,
  scoring failures, translated DTOs, timeout reporting and refresh evidence.
- `source.is_deleted` is an internal schema addition, not a public API field.
- Docs Drift can enforce these decisions and reject future regressions.
- Product acceptance remains unfinished until product tasks produce structured
  `ACC-STOP-*` evidence; this ADR does not make `STOP_ALLOWED` true.
