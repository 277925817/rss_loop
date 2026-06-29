from __future__ import annotations

from pathlib import Path
from typing import Any

from .common import contains_all, load_run_log_entries, read_text, state_flag


REQUIRED_BUDGET_TEXT = [
    "Max runs/day",
    "Max tokens/day",
    "Max sub-agent spawns/run",
    "Max attempts/item/day",
    "Aggregate daily token cap",
    "On Budget Exceed",
    "budget_skipped",
    "budget_exceeded",
]

KNOWN_LOOPS = [
    "daily-triage",
    "docs-drift",
    "acceptance-sweeper",
    "product-delivery",
    "issue-triage",
    "pr-babysitter",
    "ci-sweeper",
    "dependency-sweeper",
    "changelog-drafter",
    "post-merge-cleanup",
]

LOOP_BUDGET_LABELS = {
    "daily-triage": "Daily Triage",
    "docs-drift": "Docs Drift",
    "acceptance-sweeper": "Acceptance Sweeper",
    "product-delivery": "Product Delivery",
    "issue-triage": "Issue Triage",
    "pr-babysitter": "PR Babysitter",
    "ci-sweeper": "CI Sweeper",
    "dependency-sweeper": "Dependency Sweeper",
    "changelog-drafter": "Changelog Drafter",
    "post-merge-cleanup": "Post-Merge Cleanup",
}


def build_budget_report(root: Path, run_id: str) -> dict[str, Any]:
    findings: list[dict[str, str]] = []
    budget_text = read_text(root, "loop-budget.md") if (root / "loop-budget.md").exists() else ""
    state_text = read_text(root, "STATE.md") if (root / "STATE.md").exists() else ""
    run_log_entries = load_run_log_entries(root)

    missing_budget_terms = [term for term in REQUIRED_BUDGET_TEXT if term not in budget_text]
    if missing_budget_terms:
        findings.append(
            {
                "check": "budget_contract",
                "message": "loop-budget.md is missing required budget terms.",
                "details": ", ".join(missing_budget_terms),
            }
        )

    missing_loops = [
        loop_id
        for loop_id in KNOWN_LOOPS
        if loop_id not in budget_text and LOOP_BUDGET_LABELS[loop_id] not in budget_text
    ]
    if missing_loops:
        findings.append(
            {
                "check": "known_loop_caps",
                "message": "loop-budget.md lacks caps for known loops.",
                "details": ", ".join(missing_loops),
            }
        )

    if not run_log_entries:
        findings.append(
            {
                "check": "run_log_entries",
                "message": "loop-run-log.md has no parseable JSONL run entries.",
                "details": "none",
            }
        )

    if state_flag(state_text, "loop_pause_all") is True:
        findings.append(
            {
                "check": "loop_pause_all",
                "message": "Global loop pause is active.",
                "details": "STATE.md loop_pause_all=true",
            }
        )

    status = "passed" if not findings else "blocked"
    return {
        "run_id": run_id,
        "schema_ref": "docs/11_evidence_and_reports.md#budget-report",
        "schema_version": "v1",
        "status": status,
        "checks_run": [
            "budget_contract",
            "known_loop_caps",
            "run_log_entries",
            "loop_pause_all",
        ],
        "known_loops": KNOWN_LOOPS,
        "run_log_entry_count": len(run_log_entries),
        "findings": findings,
        "required_next_action": "continue" if status == "passed" else "pause",
    }
