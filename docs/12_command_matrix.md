# 12_command_matrix.md

## 0. Purpose

This document defines the command interface that loop runners use.

Commands are implemented under the local `tools` Python package and must be run
with `python3 -m tools.<module>` from the repository root or assigned worktree.
Until a command exists and produces the required report, the related gate
remains unproven.

## 1. Command Contract

Every command must:

- run from the repository root or assigned worktree root,
- use fixture/mock/fixed-clock inputs for product verification,
- write machine-readable output under `reports/<run_id>/`,
- avoid live RSS, live HTML, live LLM, production databases and wall-clock
  assertion inputs,
- fail non-zero when its required report cannot be produced.

Exit semantics:

- Exit `0` when a structurally valid report is written, even if the report
  contains `FAIL`, `UNKNOWN`, `BLOCKED` or `skipped` results.
- Exit non-zero only for CLI argument errors, unsafe `run_id`, report write
  failures, schema construction failures or unexpected tool errors.
- A passing process exit never means product acceptance passed; consumers must
  read the structured report fields.

## 2. Product Verification Commands

| Stage | Target command | Required report |
| --- | --- | --- |
| static | `python3 -m tools.report_static --run-id <run_id>` | `reports/<run_id>/test-report.json` |
| unit | `python3 -m tools.report_unit --run-id <run_id>` | `reports/<run_id>/test-report.json` |
| contract | `python3 -m tools.report_contract --run-id <run_id>` | `reports/<run_id>/test-report.json` |
| api | `python3 -m tools.report_api --run-id <run_id>` | `reports/<run_id>/test-report.json` |
| integration | `python3 -m tools.report_integration --run-id <run_id>` | `reports/<run_id>/test-report.json` |
| replay | `python3 -m tools.report_replay --run-id <run_id>` | `reports/<run_id>/test-report.json` |
| snapshot | `python3 -m tools.report_snapshot --run-id <run_id>` | `reports/<run_id>/test-report.json` |
| e2e | `python3 -m tools.report_e2e --run-id <run_id>` | `reports/<run_id>/test-report.json` |
| acceptance | `python3 -m tools.report_acceptance --run-id <run_id>` | `reports/<run_id>/acceptance-report.json` |

These module paths are reserved. If implementation chooses different command
names, this document must be updated before Product Delivery can use them.

## 3. Loop Verification Commands

| Gate | Target command | Required report |
| --- | --- | --- |
| loop readiness | `python3 -m tools.report_loop_readiness --run-id <run_id>` | `reports/<run_id>/loop-readiness-report.json` |
| docs drift | `python3 -m tools.report_docs_drift --run-id <run_id>` | `reports/<run_id>/docs-drift-report.json` |
| budget | `python3 -m tools.report_budget --run-id <run_id>` | `reports/<run_id>/budget-report.json` |
| verifier | `python3 -m tools.report_verifier --run-id <run_id>` | `reports/<run_id>/verifier-report.json` |

## 3.1 Codex Automation Report Commands

These commands are deterministic report generators for week-one report-only
Codex automations. They may read local repository files and locally available
GitHub state through `gh`, but must not edit source files, issues, pull
requests, dependency versions, labels, releases, or branch protection.

| Loop | Target command | Required report |
| --- | --- | --- |
| issue-triage | `python3 -m tools.report_issue_triage --run-id <run_id>` | `reports/<run_id>/issue-triage-report.json` |
| pr-babysitter | `python3 -m tools.report_pr_babysitter --run-id <run_id>` | `reports/<run_id>/pr-babysitter-report.json` |
| ci-sweeper | `python3 -m tools.report_ci_sweeper --run-id <run_id>` | `reports/<run_id>/ci-sweeper-report.json` |
| dependency-sweeper | `python3 -m tools.report_dependency_sweeper --run-id <run_id>` | `reports/<run_id>/dependency-sweeper-report.json` |
| changelog-drafter | `python3 -m tools.report_changelog --run-id <run_id>` | `reports/<run_id>/changelog-report.json` |
| post-merge-cleanup | `python3 -m tools.report_post_merge --run-id <run_id>` | `reports/<run_id>/post-merge-report.json` |

## 4. Current Bootstrap Status

Current status: command interface implemented for loop readiness, docs drift,
budget, verifier, acceptance, product stage bootstrap reports, and week-one
Codex automation report-only loops.

Product Delivery must remain paused until:

- `python3 -m tools.report_loop_readiness --run-id <run_id>` writes
  `reports/<run_id>/loop-readiness-report.json`;
- a bootstrap report shows only `LOOP-READY-010` blocked by
  `product_delivery_pause: true` and returns
  `required_next_action = enable_product_delivery`;
- `STATE.md` sets `product_delivery_pause: false` with evidence.
- a final report proves all `LOOP-READY-*` gates are `PASS`.

## 5. Failure Policy

If a command is missing:

- mark the related gate `UNKNOWN` or `BLOCKED`,
- write or update a Human Inbox item in `STATE.md`,
- do not treat the missing command as pass,
- do not substitute logs or screenshots for reports.
