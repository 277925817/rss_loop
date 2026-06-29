---
name: pr-review-triage
description: Report-only pull request babysitter loop for checks and review comments.
---

# pr-review-triage

## Purpose

Watch pull requests for failing checks and actionable review comments.

## Inputs

- `pr-babysitter-state.md`
- Pull requests and checks via `gh` or a future least-privilege GitHub
  connector.
- `loop-constraints.md`
- `.codex/agents/verifier.toml`

## Allowed Actions

- Read PR metadata, checks, and review comments.
- Classify root cause and attempt count.
- Write `reports/<run_id>/pr-babysitter-report.json`.
- Comment with a proposal only after human-enabled minimal-fix mode and
  verifier approval.

## Forbidden Actions

- Do not merge pull requests.
- Do not push to `main`.
- Do not close PRs.
- Do not change branch protection, secrets, dependency versions, or deployment
  configuration.
