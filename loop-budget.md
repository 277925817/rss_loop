# Loop Budget - RSS Loop

This file defines L3 operating limits for autonomous agents. It controls loop
cost and blast radius; it does not define product acceptance.

## Daily Limits

| Loop | Level | Max runs/day | Max tokens/day | Max sub-agent spawns/run | Max attempts/item/day |
| --- | --- | ---: | ---: | ---: | ---: |
| Daily Triage | L3 state maintenance | 1 | 100000 | 1 | 0 |
| Docs Drift | L3 documentation | 2 | 200000 | 2 | 2 |
| Acceptance Sweeper | L3 verification | 4 | 400000 | 2 | 3 |
| Product Delivery | L3 implementation | 6 | 800000 | 4 | 3 |
| Issue Triage | Codex report-only operations | 4 | 120000 | 1 | 0 |
| PR Babysitter | Codex report-only PR watch | 32 | 320000 | 1 | 3 |
| CI Sweeper | Codex report-only CI watch | 32 | 320000 | 1 | 3 |
| Dependency Sweeper | Codex report-only dependency watch | 4 | 160000 | 1 | 1 |
| Changelog Drafter | Codex report-only release notes | 1 | 100000 | 1 | 0 |
| Post-Merge Cleanup | Codex report-only cleanup watch | 1 | 100000 | 1 | 1 |

Aggregate daily token cap: `1500000`.

## Per-Run Limits

- Max active worktrees per loop: `1`.
- Max changed tracked files per product task before human gate: `10`.
- Max same-failure attempts before human gate: `3`.
- Max wall-clock runtime per Product Delivery run: `90 minutes`.
- Max wall-clock runtime per verification-only run: `30 minutes`.

## On Budget Exceed

1. Stop the loop that exceeded budget.
2. Append a `budget_exceeded` entry to `loop-run-log.md`.
3. Set the matching pause flag in `STATE.md`.
4. Add a `Human Inbox` item with loop id, run id, estimate, and next action.
5. Do not resume until a human clears the pause flag in `STATE.md`.

## Kill Switches

- `STATE.md` `loop_pause_all: true`: all loops stop except read-only inspection.
- `STATE.md` `product_delivery_pause: true`: product implementation stops, but
  Daily Triage, Docs Drift, and readiness documentation may continue.
- Any secret exposure or forbidden-field leak: set `loop_pause_all: true`.
- Any third failed attempt on the same task: route to `Human Inbox`.

## Estimation Policy

Before running, each loop must estimate:

- input context size,
- number of expected sub-agent spawns,
- expected test or report cost,
- whether the remaining daily budget can cover the run.

If the estimate would exceed either the per-run or daily cap, the loop must
record `budget_skipped` in `loop-run-log.md` instead of acting.
