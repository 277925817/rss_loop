# Loop Constraints - RSS Loop

These constraints are mandatory for every L3 loop and every agent role. They
are safety rules, not suggestions.

## Enforcement Order

1. This file.
2. `LOOP.md`.
3. `STATE.md`.
4. `loop-budget.md`.
5. Product workflow and source documents.

When in doubt, choose the more restrictive rule and escalate.

## Path Denylist

Agents must never auto-edit these paths or patterns without explicit human
approval:

```text
.env
.env.*
**/secrets/**
**/credentials/**
**/*_key*
**/*_secret*
**/*.pem
**/*.key
.terraform/**
k8s/production/**
**/migrations/**
auth/**
payments/**
billing/**
```

Reading denylisted files is allowed only when needed to confirm safety, and
their contents must not be copied into state, logs, reports, or prompts.

## Maker Checker Rules

- The agent that implements a change must not approve it.
- The Verifier must run in a separate agent, fresh session, or explicitly
  separate instruction context.
- The Verifier starts from a reject-by-default stance.
- The Acceptance Judge must be separate from the Implementer.
- Product task status may become `passed` only after Verifier approval and
  required evidence exists.

## Worktree Rules

- Product-changing work must happen in an isolated git worktree.
- Product-changing loops must not edit `main` directly.
- The worktree path, branch, run id, and task id must be recorded in `STATE.md`
  before implementation begins.
- A loop must clean up its worktree or record a blocker explaining why cleanup
  did not happen.

## Acceptance Rules

- Product delivery completion can be claimed only when `docs/08_acceptance.md`
  evaluates all required gates as `PASS` and `STOP_ALLOWED = true`.
- Loop readiness can be claimed only when `docs/09_loop_readiness.md` evaluates
  all required gates as `PASS` and `LOOP_READY = true`.
- Loop readiness does not satisfy product acceptance.
- Product acceptance does not satisfy loop readiness.
- Logs, screenshots, and free-form summaries are diagnostics only; they do not
  replace structured evidence.

## Auto-Merge Policy

Auto-merge to `main` is disabled.

Agents may prepare a branch, pull request, or handoff summary after verification,
but a human must merge until a future `loop-auto-merge-allowlist.md` is created
and approved.

## Human Gate Rules

Escalate before acting when a change:

- touches denylisted paths,
- changes authentication, authorization, secrets, credentials, infrastructure,
  dependency versions, or deployment behavior,
- changes product API, data model, UI contract, product acceptance gates, or
  technology stack decisions,
- touches more than 10 tracked files in one product task,
- would make a fourth attempt after three failed attempts on the same task,
- would continue while a relevant pause flag is active in `STATE.md`,
- requires interpreting ambiguous product intent.

## Secrets And Leak Rules

- Never write secrets, tokens, credentials, full prompts, raw article bodies, or
  full raw pipeline payloads into `STATE.md`, `loop-run-log.md`, test reports,
  logs, or final responses.
- If a leak is detected, set `STATE.md` `loop_pause_all: true`, record a
  sanitized `human_escalated` run-log entry, and stop.
- Logs may include titles and URLs only when sanitized and bounded.

## Budget Rules

- Read `loop-budget.md` before each run.
- Do not start a run that would exceed the per-run or daily cap.
- On budget exceed, stop, log, and route to `Human Inbox`.

## Current Bootstrap Constraint

Product Delivery is paused only while `STATE.md` contains a relevant pause flag
or active Product Delivery blocker.

Current bootstrap pause reason: verification command implementations and the
first loop-readiness report must exist before Product Delivery is enabled.
Documentation-only work may continue while this pause is active. After HP-002
and HP-004 are resolved, a final loop-readiness report must pass before any
product implementation run starts.
