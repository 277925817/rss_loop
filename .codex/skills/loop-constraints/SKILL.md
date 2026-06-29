---
name: loop-constraints
description: Load and enforce RSS Loop hard safety rules before any Codex automation runs.
---

# loop-constraints

## Purpose

Load and enforce RSS Loop hard safety rules before any Codex automation runs.

## Required Reading

1. `loop-constraints.md`
2. `LOOP.md`
3. `STATE.md`
4. `loop-budget.md`

## Required Behavior

- Treat `loop-constraints.md` as the hard runtime authority.
- Stop when `loop_pause_all: true`.
- Do not touch denylisted paths.
- Do not auto-merge, close issues, change secrets, or push to `main`.
- Route ambiguous, security-sensitive, dependency-major, or fourth-attempt work
  to `STATE.md` Human Inbox.
