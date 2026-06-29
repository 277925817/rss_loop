---
name: ci-triage
description: Report-only CI sweeper loop for failing GitHub checks.
---

# ci-triage

## Purpose

Classify failing GitHub checks and route minimal fixes through verifier.

## Inputs

- `ci-sweeper-state.md`
- CI checks via `gh`.
- `loop-constraints.md`
- `docs/12_command_matrix.md`

## Allowed Actions

- Read recent failing checks and logs.
- Summarize suspected root causes.
- Write `reports/<run_id>/ci-sweeper-report.json`.
- Propose a minimal fix only after week-one report-only calibration ends.

## Forbidden Actions

- Do not edit source files during week one.
- Do not make a fourth attempt for the same root cause.
- Do not change secrets, branch protection, deployments, or dependency majors.
