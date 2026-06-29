# ADR-001: Adopt Loop Engineering Control Documents

## Status

Accepted

## Date

2026-06-29

## Context

RSS Loop already has detailed product documents:

- `docs/01_prd.md` for product requirements.
- `docs/02_arch.md` for architecture.
- `docs/03_ui_spec.md` for UI behavior.
- `docs/04_data_model.md` for data facts.
- `docs/05_api_contract.md` for API contracts.
- `docs/06_dev_rules.md` for implementation rules.
- `docs/07_test_spec.md` for test evidence.
- `docs/08_acceptance.md` for the product Stop Gate.
- `tasks.md` and `workflows.md` for the local product delivery loop.

Those documents are strong enough for a single agent to work deterministically,
but they do not yet define an L3 multi-agent operating system. Missing pieces
include durable loop state, run logs, budget limits, kill switches, maker/checker
separation, worktree isolation, multi-loop coordination, and readiness gates.

The project wants to apply loop-engineering principles from
`cobusgreyling/loop-engineering`: design the control system that prompts agents,
instead of relying on a human to prompt every step.

## Decision

Adopt a documentation-first loop-engineering control layer:

- `LOOP.md` is the loop control plane.
- `STATE.md` is durable agent memory.
- `loop-budget.md` defines operating budgets.
- `loop-run-log.md` defines the append-only audit trail.
- `loop-constraints.md` defines hard safety rules.
- `docs/09_loop_readiness.md` defines L3 readiness gates.

Keep product completion separate:

- `docs/08_acceptance.md` remains the only product Stop Gate.
- `docs/09_loop_readiness.md` decides whether agents may run at L3.
- Loop readiness never substitutes for product acceptance.

Product Delivery starts paused until loop usage, role skills and structured
evidence generation are documented and verified. The product technology stack
is FastAPI + React/Vite + SQLite.

## Alternatives Considered

### Keep the existing single-agent workflow only

- Pros: Smaller documentation surface and fewer operating concepts.
- Cons: No durable memory, no budget, no run log, no maker/checker split, and no
  safe way for multiple agents to keep working over time.
- Rejected because it does not meet the L3 multi-agent goal.

### Add GitHub Actions, scripts, and automation immediately

- Pros: Faster path to executable automation.
- Cons: Automates before the control contract is stable; increases blast radius
  while safety, budget, and handoff rules are still implicit.
- Rejected for this phase because the requested scope is documentation only.

### Use `docs/08_acceptance.md` for both product and loop readiness

- Pros: Fewer documents.
- Cons: Mixes product correctness with operations readiness and risks weakening
  the product Stop Gate.
- Rejected because product acceptance and loop readiness answer different
  questions.

## Consequences

- Agents have a clear entrypoint and durable state model before automation is
  added.
- Future L3 execution can be audited through `loop-run-log.md`.
- Product implementation remains blocked until role skills and structured
  evidence generation are documented and verified.
- Documentation loops can continue while product implementation is paused.
- The repository now has two distinct gates:
  - product completion: `docs/08_acceptance.md`
  - loop readiness: `docs/09_loop_readiness.md`
