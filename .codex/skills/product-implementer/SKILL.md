---
name: product-implementer
description: Codex App entrypoint for one scoped Product Delivery implementation.
---

# product-implementer

## Purpose

Codex App entrypoint for one scoped Product Delivery implementation.

## Delegate Contract

Read and follow `skills/product-implementer/SKILL.md`.

## Required Behavior

- Work only in the assigned isolated worktree.
- Do not edit `main` directly.
- Do not mark tasks as passed.
- Write `reports/<run_id>/test-report.json` and
  `evidence/<run_id>/changed-files.txt`.
- Hand off to `verifier` before any task status update.
