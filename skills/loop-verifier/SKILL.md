# loop-verifier

## Purpose

Provide the generic loop-engineering verifier entrypoint expected by external
audit tools. For product work, this skill delegates to `skills/verifier/SKILL.md`.

## Inputs

- Implementer or loop handoff summary.
- Changed files or report-only evidence.
- `docs/10_loop_usage.md`.
- `docs/11_evidence_and_reports.md`.
- Role-specific verifier skill when one exists.

## Allowed Actions

- Verify loop-control evidence, reports, state updates and changed-file scope.
- Delegate product-task verification rules to `skills/verifier/SKILL.md`.
- Produce or inspect verifier reports.
- Approve, reject, or block a loop handoff.

## Forbidden Actions

- Do not implement fixes.
- Do not approve work from the same agent context that implemented it.
- Do not treat logs, screenshots or summaries as pass evidence.
- Do not weaken readiness, acceptance, test or safety gates.

## Output

- A verifier report or a handoff decision using the report schema required by
  `docs/11_evidence_and_reports.md`.

## Reject Conditions

Reject when:

- the implementer and verifier are the same agent context,
- required reports are missing or malformed,
- scope widened without human approval,
- denylisted paths were touched,
- the loop continued while paused.
