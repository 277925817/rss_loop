---
name: post-merge-scan
description: Report-only post-merge cleanup scanner.
---

# post-merge-scan

## Purpose

Inspect recent merges for cleanup follow-up without changing product behavior.

## Inputs

- `post-merge-state.md`
- Git merge history.
- Recent reports under `reports/`.

## Allowed Actions

- Identify docs, lint, or follow-up cleanup candidates.
- Write `reports/<run_id>/post-merge-report.json`.
- Escalate architectural items to Human Inbox.

## Forbidden Actions

- Do not change product code during week one.
- Do not perform architecture refactors automatically.
- Do not hide or delete required evidence.
