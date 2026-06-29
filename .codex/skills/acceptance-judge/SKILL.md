---
name: acceptance-judge
description: Codex App entrypoint for product Stop Gate evaluation.
---

# acceptance-judge

## Purpose

Codex App entrypoint for product Stop Gate evaluation.

## Delegate Contract

Read and follow `skills/acceptance-judge/SKILL.md`.

## Required Behavior

- Evaluate `docs/08_acceptance.md` from structured reports only.
- Write `reports/<run_id>/acceptance-report.json`.
- Keep product acceptance separate from loop readiness.
- Leave `stop_allowed=false` until every required product gate is `PASS`.
