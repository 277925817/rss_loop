# LOOP.md - RSS Loop Control Plane

This file is the L3 loop-engineering entrypoint for the RSS Loop project.
It defines the control system that prompts agents, coordinates work, records
state, and decides when autonomous execution must stop or hand off.

Product delivery remains governed by `workflows.md`, `tasks.md`, and
`docs/08_acceptance.md`. Loop readiness is governed by
`docs/09_loop_readiness.md`.

## Control Order

Every agent must read documents in this order before acting:

1. `loop-constraints.md` for hard safety rules.
2. `LOOP.md` for loop ownership, cadence, roles, and handoff.
3. `STATE.md` for current mission, active lanes, blockers, and kill switches.
4. `loop-budget.md` for run, token, sub-agent, and attempt caps.
5. `docs/10_loop_usage.md` for runbook steps.
6. `docs/11_evidence_and_reports.md` for report and evidence contracts.
7. `docs/12_command_matrix.md` for verification command interfaces.
8. `docs/13_codex_automations.md` for Codex App / CLI automation prompts.
9. `skills/<role>/SKILL.md` or `.codex/skills/<role>/SKILL.md` for the active
   agent role.
10. `workflows.md` for product delivery state transitions.
11. `tasks.md` for the product task DAG.
12. `docs/01_prd.md` through `docs/09_loop_readiness.md` for source truth.

If documents conflict, the more restrictive loop constraint wins for agent
operation. Product behavior conflicts still follow the priority order in
`docs/06_dev_rules.md`.

## Operating Level

Target level: L3 unattended control system.

L3 means agents may continuously triage, plan, implement in isolated worktrees,
verify with separate checker agents, update state, and produce delivery evidence.
L3 does not mean agents may merge to `main` without an explicit future
auto-merge allowlist. The default auto-merge policy is off.

Before Product Delivery can run at L3, `docs/09_loop_readiness.md` must evaluate
`LOOP_READY = true`, `docs/10_loop_usage.md` must define executable operator
steps, and `STATE.md` must not contain an active kill switch or blocking
high-priority item.

## Active Loops

### Product Delivery

- Loop id: `product-delivery`
- Goal: Move the product task DAG in `tasks.md` to the `docs/08_acceptance.md`
  stop condition.
- Level: L3 after `docs/09_loop_readiness.md` passes.
- Cadence target: continuous while an actionable task exists; otherwise every
  2 hours during active work windows.
- State: `STATE.md` sections `Current Mission`, `Active Lanes`,
  `Blocked Items`, and `Human Inbox`.
- Run log: append every run to `loop-run-log.md`.
- Worktree: required for every product implementation attempt.
- Branch shape: `loop/product-delivery/<task_id>-<run_id>`.
- Stop condition: all required product gates in `docs/08_acceptance.md` are
  `PASS` and `STOP_ALLOWED = true`.
- Human handoff: required for contract conflicts, denylist paths, security
  changes, dependency upgrades, schema/API ambiguity, or the third failed
  attempt on the same task.

Agent split:

| Role | Responsibility | May modify files |
| --- | --- | --- |
| Brain Controller | Selects loop, reads state, assigns lane, records run outcome. | `STATE.md`, `loop-run-log.md` only. |
| Explorer | Reads docs, code, reports, and failure evidence. | No. |
| Implementer | Uses `skills/product-implementer/SKILL.md` to make the smallest scoped change in the assigned worktree. | Yes, inside worktree and scope. |
| Verifier | Uses `skills/verifier/SKILL.md` to run checks, review scope, and approve or reject. | No product edits. |
| Acceptance Judge | Uses `skills/acceptance-judge/SKILL.md` to evaluate `docs/08_acceptance.md` evidence and stop condition. | Reports only. |

An Implementer must never mark its own work as passed. A Verifier must be a
separate agent, fresh session, or clearly separate instruction context.

### Daily Triage

- Loop id: `daily-triage`
- Goal: Keep the durable project state accurate and actionable.
- Level: L3 state maintenance; report-first for product work.
- Cadence target: daily at 08:00 local time or on explicit request.
- State: `STATE.md`.
- Run log: append every run to `loop-run-log.md`.
- Allowed actions: prune resolved watch items, add high-priority findings,
  update `Last run`, and route ambiguous work to `Human Inbox`.
- Forbidden actions: product code edits, direct task pass/fail decisions, or
  product acceptance claims.

### Acceptance Sweeper

- Loop id: `acceptance-sweeper`
- Goal: Detect missing, stale, failed, or unproven product gate evidence.
- Level: L3 verification loop.
- Cadence target: after every Product Delivery verifier approval and at least
  daily while product tasks remain.
- State: `STATE.md` sections `High Priority`, `Blocked Items`, and `Watch List`.
- Run log: append every run to `loop-run-log.md`.
- Allowed actions: run deterministic checks, classify gate evidence, map failed
  gates to existing tasks, and create state findings.
- Forbidden actions: changing product code, weakening tests, or treating logs
  or screenshots as product pass evidence.

### Docs Drift

- Loop id: `docs-drift`
- Goal: Keep agent-facing and product-facing documents consistent.
- Level: L3 documentation loop.
- Cadence target: daily off-peak and after any documentation change.
- State: `STATE.md` section `Watch List`.
- Run log: append every run to `loop-run-log.md`.
- Allowed actions: identify conflicting rules, propose documentation fixes, and
  update loop-control documents when the fix is within documented policy.
- Human handoff: required before changing product API, data model, UI contract,
  acceptance gates, or technology stack decisions.

### Codex Peripheral Automations

These loops support repository operations around Product Delivery. Week 1 mode
is report-only for all of them.

| Loop id | Cadence target | State | Report |
| --- | --- | --- | --- |
| issue-triage | daily or every 2 hours when busy | `issue-triage-state.md` | `issue-triage-report.json` |
| pr-babysitter | every 15 minutes during work hours | `pr-babysitter-state.md` | `pr-babysitter-report.json` |
| ci-sweeper | every 15 minutes during work hours | `ci-sweeper-state.md` | `ci-sweeper-report.json` |
| dependency-sweeper | every 6 hours | `dependency-sweeper-state.md` | `dependency-sweeper-report.json` |
| changelog-drafter | daily | `changelog-drafter-state.md` | `changelog-report.json` |
| post-merge-cleanup | daily | `post-merge-state.md` | `post-merge-report.json` |

Allowed actions in week one: read repository and GitHub metadata, write
structured reports, update only the loop's state file when explicitly running
that loop, and route ambiguous work to Human Inbox.

Forbidden actions: source edits, issue close, PR merge, push to `main`, branch
protection changes, secret changes, deployment changes, dependency major
updates, and release publication.

## Multi-Loop Coordination

Priority when loops conflict:

1. Acceptance Sweeper - failing or missing acceptance evidence blocks delivery.
2. Product Delivery - owns active task worktrees and product implementation.
3. Docs Drift - repairs control/document consistency after active delivery work.
4. Daily Triage - reports and prunes state; it must not compete with action loops.

Collision rules:

- At most one loop may act on the same `task_id`, branch, or worktree.
- Each action loop must write `acting_on` in `STATE.md` before work begins.
- If another active lane has the same `acting_on`, the later loop must skip,
  append a `collision_skipped` entry to `loop-run-log.md`, and return.
- Daily Triage may update state during another loop only if it does not change
  that loop's `acting_on`, task status, attempt count, or blocker.

## Worktree Policy

Product-changing loops must use isolated git worktrees.

Required worktree metadata:

- `run_id`
- `loop_id`
- `task_id`
- `branch`
- `worktree_path`
- `owner_agent`
- `started_at`
- `cleanup_status`

Worktrees must be removed after verifier rejection, human handoff, PR creation,
or accepted merge. Unclean worktrees must be listed in `STATE.md` under
`Blocked Items`.

## State And Run Log Policy

`STATE.md` is the durable brain. It must answer:

- What is the current mission?
- What is each loop acting on?
- Which blockers require human input?
- Which items were ignored or deferred?
- Which kill switches are active?

`loop-run-log.md` is the audit trail. Every loop run must append one JSON object
using the schema in that file. Free-form summaries are allowed only after the
structured entry.

## Human Gates

Human approval is required before any loop:

- Changes authentication, authorization, secrets, credentials, infrastructure,
  production deploy configuration, or dependency versions.
- Changes `docs/05_api_contract.md`, `docs/04_data_model.md`,
  `docs/08_acceptance.md`, or technology stack decisions.
- Touches more than 10 tracked files in one product task.
- Makes a fourth attempt after three failed attempts on the same task.
- Enables auto-merge or writes to `main`.
- Continues when `STATE.md` contains `loop_pause_all: true`.

## MCP And Connector Policy

No MCP connector is required for local Product Delivery. Local L3 execution uses
repository files, deterministic report commands, isolated worktrees, `STATE.md`
and `loop-run-log.md`.

For Codex automations, prefer the local `gh` CLI on this computer. If a GitHub
connector is enabled in a future run, it may read repository, issue, pull
request and check metadata, and may comment, apply allowlisted labels, or open a
pull request only when instructed. It must not merge pull requests, auto-close
issues, push to `main`, change branch protections, alter secrets, update major
dependency versions, or edit production deployment configuration.

## Budget And Kill Switch

Budget rules live in `loop-budget.md`. Hard safety and pause rules live in
`loop-constraints.md`.

Kill switches:

- `loop_pause_all: true` pauses all loops except state inspection.
- `product_delivery_pause: true` pauses product implementation but allows
  Daily Triage, Docs Drift, and documentation repair.
- Budget exceed pauses the loop that exceeded budget and records the event.

## Current L3 Bootstrap Note

Product Delivery remains paused until the first loop-readiness report proves
that loop usage, role skills, command interfaces and the report/evidence chain
are usable. The product technology stack is FastAPI + React/Vite + SQLite.
