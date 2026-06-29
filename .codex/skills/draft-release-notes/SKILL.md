---
name: draft-release-notes
description: Draft release notes only after explicit human enablement.
---

# draft-release-notes

## Purpose

Draft release notes for human review.

## Inputs

- `changelog-drafter-state.md`
- `reports/<run_id>/changelog-report.json`
- Git history since the last release point.

## Allowed Actions

- Draft `RELEASE_NOTES_DRAFT.md` only when explicitly enabled by a human.
- During week one, report only and do not write release-note drafts.

## Forbidden Actions

- Do not edit `CHANGELOG.md`.
- Do not tag releases.
- Do not publish releases.
