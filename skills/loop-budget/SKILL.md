# loop-budget

## Purpose

Check loop budget before and after a run, then produce machine-readable budget
evidence.

## Inputs

- `loop-budget.md`
- `STATE.md`
- `loop-run-log.md`
- intended `loop_id`
- intended `run_id`

## Allowed Actions

- Estimate remaining run and token budget from documented caps and run-log
  entries.
- Produce `reports/<run_id>/budget-report.json`.
- Recommend `continue`, `budget_skipped`, or `budget_exceeded`.
- Route budget blockers to `STATE.md` Human Inbox through the Brain Controller.

## Forbidden Actions

- Do not edit product code.
- Do not change budget caps without human approval.
- Do not continue a loop when the estimate exceeds a cap.
- Do not store prompts, secrets, article bodies or raw payloads in budget
  reports.

## Output

- `reports/<run_id>/budget-report.json`.
- Required next action: `continue`, `skip`, or `pause`.

## Reject Conditions

Return `blocked` when:

- budget caps are missing,
- run-log entries are malformed,
- the intended loop id is unknown,
- the estimated run would exceed per-run or daily caps.
