# 09_loop_readiness.md

## 0. Purpose

This document defines whether RSS Loop is ready to run as an L3
loop-engineering system.

It does not define product behavior, API shape, data model, UI behavior, or
product completion. Product completion remains exclusively governed by
`docs/08_acceptance.md`.

Loop readiness answers one question:

> Are autonomous agents allowed to continuously operate this repository under
> `LOOP.md` without immediate human supervision?

## 1. Gate Configuration

```yaml
loop_readiness_gate:
  version: 09_loop_readiness@codex-automation-v3
  mode: loop_readiness_gate
  layer: HOW

  source_documents:
    loop_control: LOOP.md
    loop_state: STATE.md
    loop_budget: loop-budget.md
    loop_run_log: loop-run-log.md
    loop_constraints: loop-constraints.md
    safety_companion: docs/safety.md
    loop_usage: docs/10_loop_usage.md
    evidence_contract: docs/11_evidence_and_reports.md
    command_matrix: docs/12_command_matrix.md
    codex_automations: docs/13_codex_automations.md
    role_skills: skills/
    codex_skills: .codex/skills/
    pattern_registry: patterns/registry.yaml
    github_dogfood: .github/workflows/loop-audit.yml
    product_workflow: workflows.md
    product_tasks: tasks.md
    product_acceptance: docs/08_acceptance.md

  required_gates:
    - LOOP-READY-001
    - LOOP-READY-002
    - LOOP-READY-003
    - LOOP-READY-004
    - LOOP-READY-005
    - LOOP-READY-006
    - LOOP-READY-007
    - LOOP-READY-008
    - LOOP-READY-009
    - LOOP-READY-010
    - LOOP-READY-011
    - LOOP-READY-012
    - LOOP-READY-013
    - LOOP-READY-014
    - LOOP-READY-015
    - LOOP-READY-016
    - LOOP-READY-017
    - LOOP-READY-018
    - LOOP-READY-019
    - LOOP-READY-020
    - LOOP-READY-021
    - LOOP-READY-022
    - LOOP-READY-023
    - LOOP-READY-024

  gate_status_enum:
    - UNKNOWN
    - PASS
    - FAIL
    - BLOCKED

  stop_rule: ALL_REQUIRED_GATES_PASSED
  result_field: LOOP_READY
```

`LOOP_READY = true` only when every required gate is `PASS`.

## 2. Evidence Model

Readiness evidence must be explicit and inspectable:

| Evidence | Required content |
| --- | --- |
| Control document evidence | File exists, contains required sections, and names source documents. |
| State evidence | `STATE.md` has current mission, kill switch, active lanes, blockers, and human inbox. |
| Budget evidence | Daily and per-run caps exist, with budget exceed procedure. |
| Run log evidence | JSONL schema exists and at least one initial entry exists. |
| Constraint evidence | Denylist, maker/checker, worktree, acceptance, auto-merge, and human gate rules exist. |
| Separation evidence | Product acceptance and loop readiness are separate documents and do not satisfy each other. |
| Blocker evidence | Active blockers are listed with a required resolution. |
| Codex automation evidence | `.codex/skills`, automation prompts, state files, and report commands exist. |
| GitHub policy evidence | Codex automations are limited to read/report actions in week one and cannot merge or auto-close. |

Free-form confidence is not evidence.

## 2.1 Two-Step Product Delivery Enablement

Product Delivery enablement uses two readiness runs:

1. Bootstrap readiness run:
   - command: `python3 -m tools.report_loop_readiness --run-id <run_id>`
   - expected when control tooling exists but Product Delivery is paused:
     every gate except `LOOP-READY-010` is `PASS`,
     `LOOP-READY-010` is `BLOCKED`,
     `loop_ready = false`, and
     `required_next_action = enable_product_delivery`.
   - this report is allowed to be the evidence that clears
     `STATE.md` `product_delivery_pause`.
2. Final readiness run:
   - command: `python3 -m tools.report_loop_readiness --run-id <run_id>`
   - required after `STATE.md` sets `product_delivery_pause: false`.
   - every required gate must be `PASS`, `loop_ready = true`, and no relevant
     pause flag may be active.

The bootstrap report does not authorize product implementation by itself.
Product implementation may start only after the final readiness run passes.

## 3. Required Gates

### LOOP-READY-001 Control Documents Gate

Pass:

- `LOOP.md` exists.
- `STATE.md` exists.
- `loop-budget.md` exists.
- `loop-run-log.md` exists.
- `loop-constraints.md` exists.
- `docs/10_loop_usage.md` exists.
- `docs/11_evidence_and_reports.md` exists.
- `docs/12_command_matrix.md` exists.
- `docs/13_codex_automations.md` exists.
- `skills/loop-triage/SKILL.md` exists.
- `skills/product-implementer/SKILL.md` exists.
- `skills/verifier/SKILL.md` exists.
- `skills/acceptance-judge/SKILL.md` exists.
- `skills/docs-drift/SKILL.md` exists.
- `.codex/skills/loop-constraints/SKILL.md` exists.
- `.codex/skills/loop-triage/SKILL.md` exists.
- `.codex/skills/loop-verifier/SKILL.md` exists.
- `.codex/skills/product-implementer/SKILL.md` exists.
- `.codex/skills/acceptance-judge/SKILL.md` exists.
- Codex peripheral automation skill entrypoints exist.
- This file exists.

Fail:

- Any required control document is missing.

### LOOP-READY-002 Durable State Gate

Pass:

- `STATE.md` contains `Last run`, `Kill Switch`, `Current Mission`,
  `Active Lanes`, `High Priority`, `Watch List`, `Human Inbox`, and
  `Blocked Items`.
- `STATE.md` identifies whether Product Delivery is paused.

Fail:

- Agents cannot determine current mission, active work, blockers, or pause state.

### LOOP-READY-003 Budget Gate

Pass:

- `loop-budget.md` defines per-loop daily run caps.
- `loop-budget.md` defines token caps.
- `loop-budget.md` defines sub-agent caps.
- `loop-budget.md` defines budget exceed behavior.
- `loop-budget.md` defines kill-switch behavior.

Fail:

- A loop can run without a documented cost cap or pause procedure.

### LOOP-READY-004 Run Log Gate

Pass:

- `loop-run-log.md` defines a machine-readable JSONL schema.
- The schema includes `run_id`, `loop_id`, `started_at`, `finished_at`,
  `acting_on`, `agents`, `attempt`, `actions_taken`, `tests`, `gates`,
  `outcome`, and `escalations`.
- At least one bootstrap entry exists.

Fail:

- Runs cannot be audited without reading chat transcripts.

### LOOP-READY-005 Constraint And Denylist Gate

Pass:

- `loop-constraints.md` defines path denylist rules.
- It forbids automatic edits to secrets and credentials.
- It defines secret and forbidden-field leak handling.
- It defines auto-merge policy.

Fail:

- An agent can edit sensitive paths or merge without a documented human gate.

### LOOP-READY-006 Maker Checker Gate

Pass:

- Implementer and Verifier responsibilities are separate.
- The Implementer cannot mark its own work as passed.
- The Verifier is reject-by-default.
- Acceptance Judge is separate from Implementer.

Fail:

- A single agent can implement and approve the same work.

### LOOP-READY-007 Worktree Isolation Gate

Pass:

- Product-changing work requires an isolated git worktree.
- Worktree metadata is recorded in `STATE.md`.
- Worktree cleanup or cleanup blocker is required.

Fail:

- Product-changing loops can directly edit `main` or leave untracked worktrees
  without state.

### LOOP-READY-008 Human Handoff Gate

Pass:

- Human gates exist for denylist paths, security-sensitive changes,
  dependencies, product API, data model, UI contract, acceptance gates,
  technology stack decisions, and third failed attempt.
- `STATE.md` contains a `Human Inbox`.

Fail:

- Ambiguous or high-risk work can continue without human escalation.

### LOOP-READY-009 Product Acceptance Separation Gate

Pass:

- `docs/08_acceptance.md` remains the product Stop Gate.
- `docs/09_loop_readiness.md` remains the loop readiness gate.
- Neither document claims to satisfy the other.
- Product API, data model, and UI contracts are unchanged by loop readiness.

Fail:

- Loop readiness weakens or replaces product acceptance.

### LOOP-READY-010 Active Blocker Gate

Pass:

- `STATE.md` has no active blocker that pauses the loop being enabled.
- For Product Delivery, `product_delivery_pause` is `false`.

Blocked:

- `STATE.md` contains an active Product Delivery blocker.
- Bootstrap blocker pattern: if command implementations or the structured
  evidence chain are missing, Product Delivery remains blocked until a
  `reports/<run_id>/loop-readiness-report.json` proves the control layer.

Fail:

- A loop starts despite an active relevant pause flag.

### LOOP-READY-011 Safety Companion Gate

Pass:

- `docs/safety.md` exists.
- It names `loop-constraints.md` as the hard runtime authority.
- It documents auto-merge, connector and incident-response guardrails.

Fail:

- Human-readable safety policy is missing or contradicts `loop-constraints.md`.

### LOOP-READY-012 Budget Enforcement Gate

Pass:

- `skills/loop-budget/SKILL.md` exists.
- `python3 -m tools.report_budget --run-id <run_id>` exists.
- `docs/11_evidence_and_reports.md` defines `budget-report.json`.
- `docs/12_command_matrix.md` lists the budget report command.

Fail:

- Budget is documented but not reportable by a loop command.

### LOOP-READY-013 Loop Verifier Compatibility Gate

Pass:

- `skills/loop-verifier/SKILL.md` exists as the generic loop verifier entry.
- Product verification remains delegated to `skills/verifier/SKILL.md`.
- A Codex verifier agent config exists or an equivalent verifier entrypoint is
  documented.

Fail:

- External audit tools cannot discover a verifier entrypoint.

### LOOP-READY-014 Pattern Registry Gate

Pass:

- `patterns/registry.yaml` exists.
- It lists `daily-triage`, `docs-drift`, `acceptance-sweeper` and
  `product-delivery`.
- `product-delivery` records `worktree_required: true`.

Fail:

- Loop patterns are not machine-readable.

### LOOP-READY-015 Connector Policy Gate

Pass:

- `LOOP.md` or `docs/safety.md` explicitly says no MCP connector is required for
  local Product Delivery.
- If a GitHub connector is enabled later, it is limited to read/comment/label/PR
  creation and must not merge or push to `main`.

Fail:

- MCP or connector permissions are ambiguous.

### LOOP-READY-016 GitHub Dogfood Gate

Pass:

- `.github/workflows/loop-audit.yml` runs local unit tests and
  `npx @cobusgreyling/loop-audit . --suggest`.
- `.github/PULL_REQUEST_TEMPLATE.md` asks for loop verification and safety
  checks.

Fail:

- Loop audit is not dogfooded in repository automation.

### LOOP-READY-017 External Audit Evidence Gate

Pass:

- Current run evidence includes `reports/<run_id>/loop-audit.txt`.
- The external `loop-audit` result reports `Level: L3`.

Fail:

- External audit evidence is missing or reports a level below L3.

### LOOP-READY-018 Codex Skills Gate

Pass:

- `.codex/skills/` exists.
- Core Codex entries exist for loop constraints, triage, verifier, product
  implementer and acceptance judge.
- Peripheral Codex entries exist for issue triage, PR review triage, CI triage,
  dependency triage, changelog scan, release-note drafting, post-merge scan and
  minimal fix.
- Week-one behavior is report-only unless a human explicitly enables more.

Fail:

- Codex App or CLI cannot discover required skill entrypoints.

### LOOP-READY-019 Codex Automation Manual Gate

Pass:

- `docs/13_codex_automations.md` exists.
- It documents Daily Triage, Issue Triage, PR Babysitter, CI Sweeper,
  Dependency Sweeper, Changelog Drafter and Post-Merge Cleanup.
- It includes cadence, state file, report file, prompt template, `gh` fallback
  and week-one report-only policy.

Fail:

- A human cannot configure Codex Automations without inventing prompts.

### LOOP-READY-020 Codex Peripheral State Gate

Pass:

- `issue-triage-state.md`, `pr-babysitter-state.md`,
  `ci-sweeper-state.md`, `dependency-sweeper-state.md`,
  `changelog-drafter-state.md` and `post-merge-state.md` exist.
- Each state file records last run, mode and recent result.

Fail:

- Peripheral loops have no durable memory outside chat.

### LOOP-READY-021 Codex GitHub Policy Gate

Pass:

- Codex automations prefer local `gh` on this computer.
- Future GitHub connector use is least-privilege.
- GitHub automation must not merge, auto-close, push to `main`, change branch
  protection, alter secrets, change deployment config or apply major dependency
  updates.

Fail:

- GitHub write permissions or forbidden actions are ambiguous.

### LOOP-READY-022 Codex Verifier Alias Gate

Pass:

- `.codex/agents/verifier.toml` uses `name = "verifier"`.
- The file states it is the examples-compatible alias for loop verifier.
- It references both `skills/loop-verifier/SKILL.md` and
  `skills/verifier/SKILL.md`.

Fail:

- Codex examples that spawn `verifier` cannot find the expected checker.

### LOOP-READY-023 Week-One Report-Only Gate

Pass:

- `docs/13_codex_automations.md` says week one is report-only.
- Minimal-fix mode is disabled until a human explicitly enables it.
- Auto-merge remains disabled.

Fail:

- New automations can mutate issues, PRs, dependencies, releases or source code
  without calibration.

### LOOP-READY-024 Codex Report Command Gate

Pass:

- `docs/12_command_matrix.md` lists report commands for issue triage,
  PR babysitter, CI sweeper, dependency sweeper, changelog drafter and
  post-merge cleanup.
- `docs/11_evidence_and_reports.md` defines their report files and shared
  schema.
- The corresponding `tools.report_*` modules exist.

Fail:

- Codex automations cannot produce machine-readable evidence.

## 4. Stop Decision

Codex or another agent may claim L3 loop readiness only when:

- LOOP-READY-001 through LOOP-READY-024 are all `PASS`.
- `LOOP_READY = true`.
- No relevant pause flag is active in `STATE.md`.
- No required control document is missing or internally contradictory.

Blocked readiness is not readiness.

If Product Delivery is blocked but documentation loops remain allowed, the final
state must say:

```text
LOOP_READY = false
product_delivery_pause = true
documentation_loops_allowed = true
```

## 5. Bootstrap Evaluation Sequence

Before command implementations existed, the expected bootstrap status was:

| Gate | Expected status | Reason |
| --- | --- | --- |
| LOOP-READY-001 | PASS | Required control documents exist. |
| LOOP-READY-002 | PASS | `STATE.md` has required sections. |
| LOOP-READY-003 | PASS | `loop-budget.md` has caps and exceed policy. |
| LOOP-READY-004 | PASS | `loop-run-log.md` has schema and bootstrap entry. |
| LOOP-READY-005 | PASS | `loop-constraints.md` has denylist and safety rules. |
| LOOP-READY-006 | PASS | Maker/checker roles are documented. |
| LOOP-READY-007 | PASS | Worktree isolation is documented. |
| LOOP-READY-008 | PASS | Human gates and inbox are documented. |
| LOOP-READY-009 | PASS | Product acceptance remains separate. |
| LOOP-READY-010 | BLOCKED | Product Delivery is paused pending command implementations and the first loop-readiness report. |
| LOOP-READY-011 | UNKNOWN | Safety companion document was not part of the original bootstrap. |
| LOOP-READY-012 | UNKNOWN | Budget report command and skill were not part of the original bootstrap. |
| LOOP-READY-013 | UNKNOWN | External-audit verifier entrypoint was not part of the original bootstrap. |
| LOOP-READY-014 | UNKNOWN | Pattern registry was not part of the original bootstrap. |
| LOOP-READY-015 | UNKNOWN | Connector policy was not part of the original bootstrap. |
| LOOP-READY-016 | UNKNOWN | GitHub dogfood workflow was not part of the original bootstrap. |
| LOOP-READY-017 | UNKNOWN | External audit evidence was not part of the original bootstrap. |
| LOOP-READY-018 | UNKNOWN | Codex skill entrypoints were not part of the original bootstrap. |
| LOOP-READY-019 | UNKNOWN | Codex automation manual was not part of the original bootstrap. |
| LOOP-READY-020 | UNKNOWN | Codex peripheral state files were not part of the original bootstrap. |
| LOOP-READY-021 | UNKNOWN | Codex GitHub policy was not part of the original bootstrap. |
| LOOP-READY-022 | UNKNOWN | Codex verifier alias was not part of the original bootstrap. |
| LOOP-READY-023 | UNKNOWN | Week-one report-only automation policy was not part of the original bootstrap. |
| LOOP-READY-024 | UNKNOWN | Codex automation report commands were not part of the original bootstrap. |

Therefore:

```text
LOOP_READY = false
product_delivery_pause = true
documentation_loops_allowed = true
```

After command implementations, L3 hardening artifacts and Codex automation
entrypoints exist but
`product_delivery_pause` is still true, the expected bootstrap status is:

```text
LOOP_READY = false
product_delivery_pause = true
required_next_action = enable_product_delivery
```

After `STATE.md` is updated from that bootstrap evidence, the expected final
status is:

```text
LOOP_READY = true
product_delivery_pause = false
required_next_action = continue
```
