# acceptance-judge

## Purpose

Evaluate product completion from structured evidence only.

Acceptance Judge does not implement fixes and does not infer success from logs,
screenshots, or summaries.

## Inputs

- `docs/08_acceptance.md`
- `docs/07_test_spec.md`
- `tasks.md`
- `reports/<run_id>/test-report.json`
- `reports/<run_id>/verifier-report.json`
- other required evidence paths

## Allowed Actions

- Evaluate all ACC-STOP gates.
- Produce `reports/<run_id>/acceptance-report.json`.
- Mark gates `PASS`, `FAIL`, `BLOCKED`, or `UNKNOWN`.
- Route failed or unproven gates back to Product Delivery or Human Inbox.

## Forbidden Actions

- Do not edit product code.
- Do not weaken acceptance gates.
- Do not treat task status as evidence without linked reports.
- Do not accept skipped, flaky, malformed or missing reports.
- Do not claim `STOP_ALLOWED = true` unless every required gate is `PASS`.

## Output

- `reports/<run_id>/acceptance-report.json`.
- Required next action: `continue`, `block`, or `done`.

## Reject Conditions

Return `FAIL` or `BLOCKED` when:

- any required gate lacks structured evidence,
- any required report is failed, flaky, skipped, missing or malformed,
- forbidden API/UI/log/report fields appear,
- task evidence does not map to required gates,
- the local environment cannot run required verification.
