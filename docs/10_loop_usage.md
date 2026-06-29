# 10_loop_usage.md

## 0. Purpose

This is the operator manual for running RSS Loop with loop engineering.

It tells a human or Brain Controller how to start, pause, resume and audit
multi-agent work. It does not define product behavior; product behavior remains
in `docs/01_prd.md` through `docs/08_acceptance.md`.

## 1. Start Checklist

Before any Product Delivery loop run:

1. Read `AGENTS.md`.
2. Read `loop-constraints.md`.
3. Read `LOOP.md`.
4. Read `STATE.md`.
5. Read `loop-budget.md`.
6. Confirm `STATE.md` has:
   - `loop_pause_all: false`
   - `product_delivery_pause: false`
   - no active Product Delivery blocker
7. Confirm `docs/09_loop_readiness.md` evaluates `LOOP_READY = true`.
8. For Codex App / CLI automations, read `docs/13_codex_automations.md`.
9. Confirm the assigned role skill exists under `skills/<role>/SKILL.md` or
   `.codex/skills/<role>/SKILL.md`.
10. Confirm the previous run either finished cleanly or has an explicit blocker.

If any check fails, do not start Product Delivery. Use Daily Triage or Docs
Drift to record the blocker.

## 2. Loop Selection

Use exactly one loop per run:

| Situation | Loop id | Role entry |
| --- | --- | --- |
| Need to inspect state and prioritize | `daily-triage` | `skills/loop-triage/SKILL.md` |
| Need to implement one product task | `product-delivery` | `skills/product-implementer/SKILL.md` |
| Need independent review of a change | `product-delivery` verifier phase | `skills/verifier/SKILL.md` |
| Need to evaluate product stop gates | `acceptance-sweeper` | `skills/acceptance-judge/SKILL.md` |
| Need to repair or align docs | `docs-drift` | `skills/docs-drift/SKILL.md` |
| Need to run Codex peripheral automation | see `docs/13_codex_automations.md` | `.codex/skills/<role>/SKILL.md` |

Do not let Daily Triage edit product code. Do not let Product Delivery perform
acceptance approval without Acceptance Judge.

## 3. Product Delivery Runbook

### 3.1 Brain Controller

1. Read `STATE.md` and select one actionable `tasks.md` task.
2. Check `loop-budget.md` for remaining daily budget.
3. Create a run id:

   ```text
   <UTC timestamp>-<loop_id>-<task_id>
   ```

4. Create an isolated worktree and branch:

   ```text
   branch: loop/product-delivery/<task_id>-<run_id>
   worktree_path: ../rss_loop-worktrees/<task_id>-<run_id>
   ```

5. Add or update one `STATE.md` Active Lanes row with:
   - `lane_id`
   - `loop_id`
   - `acting_on`
   - `owner_agent`
   - `status`
   - `worktree_path`
   - `started_at`

6. Append a `report_only` or `fix_proposed` entry to `loop-run-log.md` when the
   run ends.

### 3.2 Implementer

1. Work only inside the assigned worktree.
2. Read task source documents and `skills/product-implementer/SKILL.md`.
3. Define the smallest implementation slice.
4. Modify only files inside the slice.
5. Run only the relevant checks defined by `docs/11_evidence_and_reports.md`.
6. Write evidence under:

   ```text
   evidence/<run_id>/
   reports/<run_id>/
   ```

7. Do not mark a task as passed.
8. Hand off to Verifier with changed files, reports and evidence paths.

### 3.3 Verifier

1. Read `skills/verifier/SKILL.md`.
2. Inspect the diff, task scope, reports and evidence.
3. Re-run required checks in the worktree.
4. Reject if scope widened, evidence is missing, tests are weak, or complexity
   increased without justification.
5. If approved, write a verifier report to:

   ```text
   reports/<run_id>/verifier-report.json
   ```

6. Only after Verifier approval may Brain Controller update `tasks.md` task
   status or evidence fields.

### 3.4 Acceptance Judge

1. Read `skills/acceptance-judge/SKILL.md`.
2. Evaluate `docs/08_acceptance.md` from structured reports only.
3. Write:

   ```text
   reports/<run_id>/acceptance-report.json
   ```

4. If any gate is missing, failed, skipped, flaky or unproven, Product Delivery
   must continue or block. It must not claim delivery.

## 4. State Update Rules

`STATE.md` is updated by Brain Controller, Daily Triage, Docs Drift or explicit
human decision only.

Required state updates:

- At run start: Active Lanes row.
- At run end: Last run timestamp and lane status.
- On blocker: Human Inbox and Blocked Items.
- On resolved blocker: mark resolved and cite evidence path.
- On budget exceed: pause the loop and record in Human Inbox.

Never write secrets, full prompts, raw article bodies, raw pipeline payloads or
credentials to `STATE.md`.

## 5. Run Log Rules

Every loop run appends one JSON object to `loop-run-log.md`.

Minimum acceptable outcomes:

- `no_op`
- `report_only`
- `fix_proposed`
- `verifier_rejected`
- `verifier_approved`
- `acceptance_failed`
- `acceptance_passed`
- `human_escalated`
- `budget_skipped`
- `budget_exceeded`
- `collision_skipped`
- `blocked`

If a run modifies tracked files, the run-log entry must include changed file
paths in `notes` or in a referenced evidence file.

## 6. Stop And Handoff Rules

Stop immediately and route to Human Inbox when:

- `loop_pause_all: true`.
- `product_delivery_pause: true` and the loop wants to implement product code.
- Same task has three failed attempts.
- Work would touch denylisted paths.
- Product API, data model, UI contract, acceptance gates or technology stack
  need interpretation.
- Required report or evidence cannot be generated.
- Verifier and Implementer are the same agent context.

## 7. Success Definition

Loop success is not product success.

- Loop readiness success: `docs/09_loop_readiness.md` has all required gates
  `PASS` and `LOOP_READY = true`.
- Product success: `docs/08_acceptance.md` has all required gates `PASS` and
  `STOP_ALLOWED = true`.

Both must be true before claiming industrial-grade autonomous delivery.
