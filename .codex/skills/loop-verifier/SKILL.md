---
name: loop-verifier
description: Codex App entrypoint for reject-by-default loop and product verification.
---

# loop-verifier

## Purpose

Codex App entrypoint for reject-by-default verification.

## Delegate Contract

Read and follow `skills/loop-verifier/SKILL.md`. For product-task handoffs,
also read `skills/verifier/SKILL.md`.

## Required Behavior

- Do not implement fixes.
- Do not approve work from the same context that implemented it.
- Reject missing, malformed, or stale reports.
- Treat screenshots, logs, and chat summaries as diagnostics only.
