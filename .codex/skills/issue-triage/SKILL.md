---
name: issue-triage
description: Report-only GitHub issue queue health loop.
---

# issue-triage

## Purpose

Keep the GitHub issue queue understandable without mutating issues during the
week-one calibration period.

## Inputs

- `issue-triage-state.md`
- GitHub issues via `gh` or a future least-privilege GitHub connector.
- `loop-constraints.md`
- `docs/13_codex_automations.md`

## Allowed Actions

- Read open issues and labels.
- Summarize top actionable items.
- Propose labels in the report only.
- Write `reports/<run_id>/issue-triage-report.json`.

## Forbidden Actions

- Do not close issues.
- Do not apply labels during week one.
- Do not edit source files.
- Escalate security, dependency-major, API, data-model, and auth-sensitive
  issues to Human Inbox.
