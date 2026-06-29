# ADR-002: Standardize on FastAPI and React/Vite

## Status

Accepted

## Date

2026-06-29

## Context

The project documents previously disagreed on the MVP technology stack:

- `docs/01_prd.md` described an HTML/CSS/JavaScript frontend and Flask backend.
- `docs/02_arch.md`, `docs/05_api_contract.md`, `docs/06_dev_rules.md`,
  `docs/07_test_spec.md`, and `tasks.md` described React + Vite, FastAPI and
  SQLite.
- `requirements.txt` still included Flask.

This conflict blocked L3 Product Delivery because agents could not safely
choose an implementation target.

## Decision

Standardize the MVP technology stack on:

- Frontend: React + Vite
- Backend: Python FastAPI
- Database: SQLite
- Scheduler: in-process backend scheduler

Update dependency intent by replacing Flask with FastAPI and Uvicorn in
`requirements.txt`.

## Alternatives Considered

### Keep Flask and static HTML

- Pros: Matches the current prototype dependency and simple static page.
- Cons: Conflicts with the majority of architecture, API, development, test and
  task documents.
- Rejected because it would require rewriting the stronger contract set.

### Keep both stacks temporarily

- Pros: Avoids immediate migration pressure.
- Cons: Lets agents choose different targets and increases the chance of
  incompatible implementation slices.
- Rejected because L3 agents need one clear target.

## Consequences

- Product Delivery agents now target FastAPI + React/Vite.
- Existing static `index.html` is treated as prototype/reference material until
  TASK-001 creates the runtime skeleton.
- `STATE.md` no longer blocks on the technology stack conflict.
- Product Delivery remains paused until loop usage, role skills and structured
  evidence generation are verified.
