# loop-triage

## Purpose

Maintain durable loop state without changing product code.

Use this skill for Daily Triage runs and state-only inspections.

## Inputs

- `AGENTS.md`
- `LOOP.md`
- `STATE.md`
- `loop-budget.md`
- `loop-run-log.md`
- `docs/09_loop_readiness.md`
- recent task and report status

## Allowed Actions

- Update `STATE.md` Last run.
- Add or prune `High Priority`, `Watch List`, `Human Inbox`, and `Blocked Items`.
- Append one JSON object to `loop-run-log.md`.
- Classify items as `no_op`, `report_only`, `blocked`, or `human_escalated`.

## Forbidden Actions

- Do not edit product code.
- Do not mark `tasks.md` tasks as passed.
- Do not claim product acceptance.
- Do not bypass `product_delivery_pause`.
- Do not write secrets, raw article bodies, full prompts, or credentials.

## Output

- Updated `STATE.md`.
- One run-log JSON object.
- Optional `reports/<run_id>/triage-report.json`.

## Reject Conditions

Route to Human Inbox when:

- state is internally contradictory,
- active lanes collide,
- budget is exhausted,
- a loop wants to proceed while paused,
- a required control document is missing.
