---
name: dependency-triage
description: Report-only dependency and advisory inspection loop.
---

# dependency-triage

## Purpose

Inspect dependency files and advisories without changing dependency versions by
default.

## Inputs

- `dependency-sweeper-state.md`
- Local manifests and lockfiles.
- GitHub advisory or Dependabot metadata when available through `gh`.
- `loop-constraints.md`

## Allowed Actions

- Read dependency manifests and lockfiles.
- Classify patch, minor, and major update candidates.
- Write `reports/<run_id>/dependency-sweeper-report.json`.

## Forbidden Actions

- Do not change dependencies during week one.
- Do not apply major version bumps without human approval.
- Do not change deployment, secrets, or production infrastructure files.
