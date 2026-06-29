# 13_codex_automations.md

## 0. Purpose

This document tells a human operator how to configure Codex App or Codex CLI
automations for RSS Loop on this computer.

It does not define product behavior or product completion. Product completion
remains governed by `docs/08_acceptance.md`.

Week 1 default for every automation in this file is `report-only`: read state,
write structured reports, and propose next actions without editing source
files, issues, pull requests, dependency versions, releases, or labels.

## 1. Shared Rules

- Project: this repository checkout.
- Environment: local checkout or background worktree.
- Hard preflight prompt prefix:

  ```text
  Run $loop-constraints first. Read loop-constraints.md, LOOP.md, STATE.md,
  loop-budget.md, docs/10_loop_usage.md, docs/11_evidence_and_reports.md,
  docs/12_command_matrix.md, and docs/13_codex_automations.md.
  Week 1 is report-only. Do not edit source files, close issues, merge PRs,
  push to main, change branch protection, change secrets, change deployments,
  or change dependency major versions.
  ```

- GitHub access: prefer `gh` on this computer for issue, PR, check, and commit
  reads. A future GitHub connector may read issue, pull request, repository and
  check metadata, and may comment, apply allowlisted labels, or open a PR only
  when explicitly instructed.
- GitHub forbidden actions: must not merge, must not auto-close, must not push
  to `main`, must not change branch protection, must not alter secrets, must
  not edit production deployment configuration, and must not apply major
  dependency updates.
- Minimal-fix mode is disabled until a human explicitly enables it after week
  one report stability and verifier approval.

## 2. Automations

| Automation | Cadence | Skill | State | Report |
| --- | --- | --- | --- | --- |
| Daily Triage | Daily 08:00 local | `$loop-triage` | `STATE.md` | `triage-report.json` |
| Issue Triage | Daily for quiet repos, every 2h when busy | `$issue-triage` | `issue-triage-state.md` | `issue-triage-report.json` |
| PR Babysitter | Every 15m during work hours | `$pr-review-triage` | `pr-babysitter-state.md` | `pr-babysitter-report.json` |
| CI Sweeper | Every 15m during work hours | `$ci-triage` | `ci-sweeper-state.md` | `ci-sweeper-report.json` |
| Dependency Sweeper | Every 6h | `$dependency-triage` | `dependency-sweeper-state.md` | `dependency-sweeper-report.json` |
| Changelog Drafter | Daily | `$changelog-scan`, `$draft-release-notes` | `changelog-drafter-state.md` | `changelog-report.json` |
| Post-Merge Cleanup | Daily | `$post-merge-scan` | `post-merge-state.md` | `post-merge-report.json` |

## 3. Prompt Templates

### Daily Triage

```text
Run $loop-triage on this project after the shared preflight. Update STATE.md
only if needed for High Priority, Watch List, Human Inbox, Blocked Items, Last
run, or resolved noise. Write reports/<run_id>/triage-report.json and append
one loop-run-log.md entry. Week 1: report-only for product work.
```

### Issue Triage

```text
Run $issue-triage after the shared preflight. Read issue-triage-state.md and
open GitHub issues through gh. Write reports/<run_id>/issue-triage-report.json
with open actionable count, delta, top prioritized issues, proposed labels, and
needs-human items. Week 1: do not apply labels, close issues, or edit source.
```

### PR Babysitter

```text
Run $pr-review-triage after the shared preflight. Read pr-babysitter-state.md
and open PR/check metadata through gh. Write
reports/<run_id>/pr-babysitter-report.json. If CI is red or a review comment is
actionable, propose next action only. Week 1: do not open worktrees, comment,
push, merge, or close.
```

### CI Sweeper

```text
Run $ci-triage after the shared preflight. Read ci-sweeper-state.md and failing
checks through gh. Write reports/<run_id>/ci-sweeper-report.json with suspected
root causes and attempt counts. Week 1: do not edit source. Stop after three
failures on the same root cause.
```

### Dependency Sweeper

```text
Run $dependency-triage after the shared preflight. Read
dependency-sweeper-state.md, local manifests, lockfiles, and advisory metadata
available through gh. Write reports/<run_id>/dependency-sweeper-report.json.
Week 1: do not edit manifests or lockfiles. Major version bumps always require
human approval.
```

### Changelog Drafter

```text
Run $changelog-scan after the shared preflight. Read
changelog-drafter-state.md and git history since the last tag or state date.
Write reports/<run_id>/changelog-report.json. Week 1: do not edit
RELEASE_NOTES_DRAFT.md or CHANGELOG.md. Human review is required before any
CHANGELOG.md update.
```

### Post-Merge Cleanup

```text
Run $post-merge-scan after the shared preflight. Read post-merge-state.md,
recent merges, and relevant reports. Write reports/<run_id>/post-merge-report.json
with docs/lint cleanup candidates and architecture follow-ups. Week 1: do not
edit source. Escalate architectural items to Human Inbox.
```

## 4. Enabling Minimal Fixes Later

After week one, a human may enable minimal-fix mode for PR Babysitter or CI
Sweeper only if:

- the loop has produced stable reports for at least three runs,
- the target has fewer than three failed attempts,
- an isolated worktree is recorded,
- `$minimal-fix` is used for implementation,
- `verifier` approves before any PR comment or proposed patch is published,
- auto-merge remains disabled.

