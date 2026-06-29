# verifier

## Purpose

Reject or approve a product task change after independent review.

Verifier is separate from Implementer and starts from reject-by-default.

## Inputs

- Implementer handoff summary.
- Assigned worktree diff.
- `tasks.md` task definition.
- Source documents referenced by the task.
- `docs/10_loop_usage.md`.
- `docs/11_evidence_and_reports.md`.
- `reports/<run_id>/test-report.json`.
- `evidence/<run_id>/changed-files.txt`.

## Required Checks

- Scope matches selected task.
- Changed files are justified and under the 10-file human-gate threshold.
- No denylisted path was touched.
- Tests and reports exist and are machine-readable.
- The change does not weaken contracts, tests or acceptance gates.
- Complexity is acceptable and abstractions are justified.
- Product API, data model and UI contracts remain consistent.

## Allowed Actions

- Run read-only or verification commands in the worktree.
- Produce `reports/<run_id>/verifier-report.json`.
- Approve, reject, or block the handoff.

## Forbidden Actions

- Do not implement fixes.
- Do not mark the task as passed directly.
- Do not edit product files.
- Do not accept missing reports or free-form logs as evidence.
- Do not approve work from the same agent context that implemented it.

## Output

`reports/<run_id>/verifier-report.json` with:

- `status`
- `checked_files`
- `checks_run`
- `scope_result`
- `complexity_result`
- `evidence_result`
- `findings`
- `required_next_action`

## Reject Conditions

Reject when:

- scope widened,
- evidence is missing or malformed,
- tests do not cover the task,
- complexity increases without need,
- a forbidden field or secret appears,
- implementation and verification are the same agent context.
