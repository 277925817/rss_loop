# docs-drift

## Purpose

Keep loop-control and product documents consistent without changing product
behavior unless a human explicitly approves the contract change.

## Inputs

- `AGENTS.md`
- `LOOP.md`
- `STATE.md`
- `loop-constraints.md`
- `docs/01_prd.md` through `docs/11_evidence_and_reports.md`
- ADRs in `docs/decisions/`

## Allowed Actions

- Detect conflicting rules, stale references and missing links.
- Update loop-control documents when the fix is mechanical and within policy.
- Propose product contract changes for human approval.
- Produce `reports/<run_id>/docs-drift-report.json`.
- Append one run-log entry.

## Forbidden Actions

- Do not silently change product API, data model, UI contract, acceptance gates
  or technology stack decisions.
- Do not edit product code.
- Do not mark Product Delivery ready without `docs/09_loop_readiness.md`.
- Do not delete historical ADRs.

## Output

- Updated docs when safe.
- `reports/<run_id>/docs-drift-report.json`.
- Human Inbox item when a decision is needed.

## Reject Conditions

Route to Human Inbox when:

- two source documents conflict and priority rules do not resolve it,
- fixing drift would alter product behavior,
- an ADR is needed but missing,
- readiness or acceptance language becomes ambiguous.
