---
name: loop-triage
description: Codex App entrypoint for Daily Triage state maintenance.
---

# loop-triage

## Purpose

Codex App entrypoint for Daily Triage.

## Delegate Contract

Read and follow `skills/loop-triage/SKILL.md`.

## Codex Automation Defaults

- Mode: report-only unless a human explicitly enables state maintenance.
- State: `STATE.md`.
- Report: `reports/<run_id>/triage-report.json`.
- Run log: append one JSON object to `loop-run-log.md`.
- Forbidden: product code edits, task pass/fail decisions, acceptance claims.
