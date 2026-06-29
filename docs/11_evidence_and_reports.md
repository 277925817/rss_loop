# 11_evidence_and_reports.md

## 0. Purpose

This document defines where loop runs, test runs, verifier reviews and
acceptance judgments store machine-readable evidence.

It bridges:

- `docs/07_test_spec.md` TestReport contract.
- `docs/08_acceptance.md` product Stop Gate.
- `docs/09_loop_readiness.md` loop readiness gate.
- `docs/12_command_matrix.md` command interface.
- `STATE.md` and `loop-run-log.md` durable loop memory.

## 1. Directory Layout

Each run uses the same run id in both directories:

```text
reports/<run_id>/
evidence/<run_id>/
```

Required files by run type:

| Run type | Required files |
| --- | --- |
| Daily Triage | `reports/<run_id>/triage-report.json` |
| Product Delivery implementer | `reports/<run_id>/test-report.json`, `evidence/<run_id>/changed-files.txt` |
| Verifier | `reports/<run_id>/verifier-report.json` |
| Acceptance Sweeper | `reports/<run_id>/acceptance-report.json` |
| Docs Drift | `reports/<run_id>/docs-drift-report.json` |
| Budget Check | `reports/<run_id>/budget-report.json` |
| Loop Readiness | `reports/<run_id>/loop-readiness-report.json` |
| Issue Triage | `reports/<run_id>/issue-triage-report.json` |
| PR Babysitter | `reports/<run_id>/pr-babysitter-report.json` |
| CI Sweeper | `reports/<run_id>/ci-sweeper-report.json` |
| Dependency Sweeper | `reports/<run_id>/dependency-sweeper-report.json` |
| Changelog Drafter | `reports/<run_id>/changelog-report.json` |
| Post-Merge Cleanup | `reports/<run_id>/post-merge-report.json` |

The run id must also appear in `loop-run-log.md`.

## 2. Product Test Report

`reports/<run_id>/test-report.json` must be either:

- one `TestReport` object from `docs/07_test_spec.md#6`, or
- an object with a `reports` array of `TestReport` objects.

Minimum wrapper:

```json
{
  "run_id": "2026-06-29T16:30:00Z-product-delivery-TASK-001",
  "schema_ref": "docs/07_test_spec.md#6",
  "schema_version": "v1",
  "reports": []
}
```

The report must not contain raw article bodies, full prompts, secrets,
credentials, `content_raw`, or `content_full`.

## 3. Verifier Report

`reports/<run_id>/verifier-report.json` must use:

```json
{
  "run_id": "...",
  "schema_ref": "docs/11_evidence_and_reports.md#3",
  "schema_version": "v1",
  "task_id": "TASK-001",
  "verifier_agent": "verifier",
  "status": "approved | rejected | blocked",
  "checked_files": [],
  "checks_run": [],
  "scope_result": "in_scope | out_of_scope",
  "complexity_result": "acceptable | rejected",
  "evidence_result": "complete | missing | malformed",
  "findings": [],
  "required_next_action": "summarize | fix | human_handoff"
}
```

Verifier approval requires:

- `status = approved`
- `scope_result = in_scope`
- `complexity_result = acceptable`
- `evidence_result = complete`
- `findings` contains no required unresolved issue

## 4. Acceptance Report

`reports/<run_id>/acceptance-report.json` must use:

```json
{
  "run_id": "...",
  "schema_ref": "docs/08_acceptance.md",
  "schema_version": "08_acceptance@codex-stop-v5",
  "gate_status": {
    "ACC-STOP-001": "PASS | FAIL | BLOCKED | UNKNOWN"
  },
  "stop_allowed": false,
  "evidence_paths": [],
  "failed_or_unproven_gates": [],
  "required_next_action": "continue | block | done"
}
```

`stop_allowed` may be `true` only when every required gate is `PASS`.

## 5. Loop Readiness Report

`reports/<run_id>/loop-readiness-report.json` must use:

```json
{
  "run_id": "...",
  "schema_ref": "docs/09_loop_readiness.md",
  "schema_version": "09_loop_readiness@codex-automation-v3",
  "gate_status": {
    "LOOP-READY-001": "PASS | FAIL | BLOCKED | UNKNOWN"
  },
  "loop_ready": false,
  "evidence_paths": [],
  "failed_or_blocked_gates": [],
  "required_next_action": "continue | block | enable_product_delivery"
}
```

`loop_ready` may be `true` only when every required readiness gate is `PASS`.

## 5.1 Budget Report

`reports/<run_id>/budget-report.json` must use:

```json
{
  "run_id": "...",
  "schema_ref": "docs/11_evidence_and_reports.md#budget-report",
  "schema_version": "v1",
  "status": "passed | blocked",
  "checks_run": [],
  "known_loops": [],
  "run_log_entry_count": 0,
  "findings": [],
  "required_next_action": "continue | pause"
}
```

Budget checks must treat missing caps, missing run-log evidence, active global
pause flags and budget exceed findings as blockers. A passed process exit does
not mean budget passed; consumers must read `status`.

## 5.2 Codex Peripheral Loop Reports

`reports/<run_id>/<loop-report>.json` for Issue Triage, PR Babysitter, CI
Sweeper, Dependency Sweeper, Changelog Drafter and Post-Merge Cleanup must use:

```json
{
  "run_id": "...",
  "schema_ref": "docs/11_evidence_and_reports.md#codex-peripheral-loop-report",
  "schema_version": "v1",
  "loop_id": "issue-triage",
  "mode": "report-only",
  "status": "passed | blocked",
  "state_file": "issue-triage-state.md",
  "skill_files": [],
  "checks_run": [],
  "findings": [],
  "required_next_action": "continue | block | human_handoff"
}
```

Week-one Codex peripheral loop reports must not claim source edits, issue
closure, PR merge, dependency changes, release publication, or product
acceptance. Consumers must read `status` and `required_next_action`.

## 6. Changed Files Evidence

`evidence/<run_id>/changed-files.txt` must list tracked files changed by the
run, one path per line.

If more than 10 tracked files changed, the Verifier must reject or require human
approval unless `LOOP.md` explicitly permits the broader change.

## 7. Task Linkage

When a product task is summarized, the task record must link:

- `run_id`
- `evidence`
- `test_report`
- `verifier_report`
- `acceptance_gate`

`tasks.md` remains the product DAG. It must not store long logs or raw evidence.

## 8. Retention And Hygiene

- Reports and evidence are committed only when they are required to prove task
  completion or loop readiness.
- Do not commit transient caches, screenshots or logs unless a contract requires
  them.
- Prune or archive reports older than 30 days only through Docs Drift and record
  the pruning run in `loop-run-log.md`.
