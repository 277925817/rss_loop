# RSS Loop Agent Skills

These skills are repository-local role contracts for loop-engineering agents.

They are intentionally small and boring. Each skill defines one role, its
inputs, allowed actions, forbidden actions, outputs and reject conditions.

## Skills

| Skill | Role |
| --- | --- |
| `loop-triage` | Maintains `STATE.md` and triage findings. |
| `loop-budget` | Checks loop budgets and writes budget reports. |
| `loop-verifier` | Generic external-audit verifier entrypoint. |
| `product-implementer` | Implements one scoped product task in a worktree. |
| `verifier` | Independently reviews and approves or rejects task work. |
| `acceptance-judge` | Evaluates product Stop Gate evidence. |
| `docs-drift` | Repairs documentation/control-plane drift. |

## Usage

Agents must read `AGENTS.md`, `loop-constraints.md`, `LOOP.md`, `STATE.md` and
`loop-budget.md` before selecting a role skill.

Product Delivery requires at least:

1. `product-implementer`
2. `verifier`
3. `acceptance-judge`

The same agent context must not perform all three roles for a product task.
