# Safety And Guardrails

This document is the human-readable companion to `loop-constraints.md`.
`loop-constraints.md` remains the hard runtime authority when the two documents
overlap.

## Minimum Safety Rules

- Auto-merge to `main` is disabled.
- Secrets, credentials, private keys, `.env` files, production infrastructure,
  auth, payments and billing paths require human approval before editing.
- Product API, data model, UI contract, acceptance gates and technology stack
  changes require explicit human approval.
- Product-changing work must use an isolated git worktree.
- The agent that implements a change must not approve it.
- Third failed attempt on the same item routes to `STATE.md` Human Inbox.
- Reports and state files must not contain secrets, raw article bodies, full
  prompts, raw pipeline payloads or credentials.

## Connector Policy

No MCP connector is required for local Product Delivery. The local L3 loop can
operate from repository files, reports, worktrees and deterministic commands.

For Codex automations, prefer the local `gh` CLI on this computer.

If a GitHub connector is enabled later, it is limited to:

- read repository, issue, pull request and check metadata;
- create or update comments and allowlisted labels;
- open a pull request when a human asks for it.

It must not merge pull requests, auto-close issues, push to `main`, change
branch protections, alter secrets, apply major dependency updates, or write
production deployment config.

## Incident Response

If a loop leaks sensitive content, touches a denylisted path, or continues while
paused:

1. Set `STATE.md` `loop_pause_all: true`.
2. Append a sanitized `human_escalated` entry to `loop-run-log.md`.
3. Record the blocker in `STATE.md` Human Inbox.
4. Stop autonomous action until a human clears the pause flag.

## Preflight Checklist

- `loop-constraints.md` has been read.
- `STATE.md` pause flags are false for the intended loop.
- `loop-budget.md` allows the run.
- Required role skill exists.
- Required report command exists.
- Work does not touch denylisted paths.
