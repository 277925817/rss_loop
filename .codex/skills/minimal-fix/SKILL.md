---
name: minimal-fix
description: Smallest safe fix entrypoint gated by human enablement and verifier approval.
---

# minimal-fix

## Purpose

Make the smallest safe fix after an automation loop has produced a precise,
verifier-eligible handoff.

## Required Preconditions

- Week-one report-only calibration has ended.
- A human explicitly enabled minimal-fix mode for the loop.
- The run has an isolated worktree.
- The target issue has fewer than three failed attempts.

## Required Behavior

- Touch only files named by the handoff.
- Run the relevant command from `docs/12_command_matrix.md`.
- Hand off to `verifier`.
- Do not merge, close issues, push to `main`, or change dependencies without
  explicit human approval.
