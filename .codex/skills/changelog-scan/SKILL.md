---
name: changelog-scan
description: Report-only scan for release-note candidates.
---

# changelog-scan

## Purpose

Scan recent commits and state to identify changes that may need release notes.

## Inputs

- `changelog-drafter-state.md`
- Git history since the last tag or state timestamp.
- `loop-run-log.md`

## Allowed Actions

- Read git history and loop reports.
- Classify user-visible changes.
- Write `reports/<run_id>/changelog-report.json`.

## Forbidden Actions

- Do not edit `CHANGELOG.md` automatically.
- Do not claim product release readiness from loop readiness.
