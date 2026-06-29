from __future__ import annotations

from pathlib import Path
from typing import Any

from .common import run_report_cli


CODEX_LOOP_CONFIGS: dict[str, dict[str, Any]] = {
    "issue-triage": {
        "state_file": "issue-triage-state.md",
        "report_file": "issue-triage-report.json",
        "skill_files": [".codex/skills/issue-triage/SKILL.md"],
        "command_module": "tools.report_issue_triage",
        "required_terms": ["Issue Triage", "$issue-triage", "issue-triage-report.json"],
    },
    "pr-babysitter": {
        "state_file": "pr-babysitter-state.md",
        "report_file": "pr-babysitter-report.json",
        "skill_files": [".codex/skills/pr-review-triage/SKILL.md", ".codex/skills/minimal-fix/SKILL.md"],
        "command_module": "tools.report_pr_babysitter",
        "required_terms": ["PR Babysitter", "$pr-review-triage", "pr-babysitter-report.json"],
    },
    "ci-sweeper": {
        "state_file": "ci-sweeper-state.md",
        "report_file": "ci-sweeper-report.json",
        "skill_files": [".codex/skills/ci-triage/SKILL.md", ".codex/skills/minimal-fix/SKILL.md"],
        "command_module": "tools.report_ci_sweeper",
        "required_terms": ["CI Sweeper", "$ci-triage", "ci-sweeper-report.json"],
    },
    "dependency-sweeper": {
        "state_file": "dependency-sweeper-state.md",
        "report_file": "dependency-sweeper-report.json",
        "skill_files": [".codex/skills/dependency-triage/SKILL.md"],
        "command_module": "tools.report_dependency_sweeper",
        "required_terms": ["Dependency Sweeper", "$dependency-triage", "dependency-sweeper-report.json"],
    },
    "changelog-drafter": {
        "state_file": "changelog-drafter-state.md",
        "report_file": "changelog-report.json",
        "skill_files": [".codex/skills/changelog-scan/SKILL.md", ".codex/skills/draft-release-notes/SKILL.md"],
        "command_module": "tools.report_changelog",
        "required_terms": ["Changelog Drafter", "$changelog-scan", "changelog-report.json"],
    },
    "post-merge-cleanup": {
        "state_file": "post-merge-state.md",
        "report_file": "post-merge-report.json",
        "skill_files": [".codex/skills/post-merge-scan/SKILL.md"],
        "command_module": "tools.report_post_merge",
        "required_terms": ["Post-Merge Cleanup", "$post-merge-scan", "post-merge-report.json"],
    },
}


def _read_optional(root: Path, relative_path: str) -> str:
    path = root / relative_path
    if not path.exists():
        return ""
    return path.read_text(encoding="utf-8")


def _exists(root: Path, relative_path: str) -> bool:
    return (root / relative_path).is_file()


def build_codex_loop_report(root: Path, run_id: str, loop_id: str) -> dict[str, Any]:
    if loop_id not in CODEX_LOOP_CONFIGS:
        raise ValueError(f"unknown Codex loop: {loop_id}")

    config = CODEX_LOOP_CONFIGS[loop_id]
    findings: list[dict[str, str]] = []
    checks_run = [
        "state_file_exists",
        "skill_files_exist",
        "automation_manual_mentions_loop",
        "pattern_registry_mentions_loop",
        "command_matrix_mentions_module",
        "report_only_policy_present",
    ]

    state_file = config["state_file"]
    if not _exists(root, state_file):
        findings.append(
            {
                "check": "state_file_exists",
                "message": f"{state_file} is missing.",
                "details": state_file,
            }
        )

    missing_skills = [path for path in config["skill_files"] if not _exists(root, path)]
    if missing_skills:
        findings.append(
            {
                "check": "skill_files_exist",
                "message": "Required Codex skill files are missing.",
                "details": ", ".join(missing_skills),
            }
        )

    automation_text = _read_optional(root, "docs/13_codex_automations.md")
    missing_terms = [term for term in config["required_terms"] if term not in automation_text]
    if missing_terms:
        findings.append(
            {
                "check": "automation_manual_mentions_loop",
                "message": "Codex automation manual does not fully describe this loop.",
                "details": ", ".join(missing_terms),
            }
        )

    registry_text = _read_optional(root, "patterns/registry.yaml")
    if loop_id not in registry_text:
        findings.append(
            {
                "check": "pattern_registry_mentions_loop",
                "message": "Pattern registry does not list this loop.",
                "details": loop_id,
            }
        )

    command_matrix_text = _read_optional(root, "docs/12_command_matrix.md")
    if config["command_module"] not in command_matrix_text:
        findings.append(
            {
                "check": "command_matrix_mentions_module",
                "message": "Command matrix does not list this report command.",
                "details": config["command_module"],
            }
        )

    policy_text = automation_text + "\n" + _read_optional(root, "LOOP.md") + "\n" + _read_optional(root, "docs/safety.md")
    if not all(term in policy_text for term in ["Week 1", "report-only", "must not merge", "auto-close"]):
        findings.append(
            {
                "check": "report_only_policy_present",
                "message": "Week-one report-only or GitHub forbidden-action policy is incomplete.",
                "details": "Week 1, report-only, must not merge, auto-close",
            }
        )

    status = "passed" if not findings else "blocked"
    return {
        "run_id": run_id,
        "schema_ref": "docs/11_evidence_and_reports.md#codex-peripheral-loop-report",
        "schema_version": "v1",
        "loop_id": loop_id,
        "mode": "report-only",
        "status": status,
        "state_file": state_file,
        "skill_files": config["skill_files"],
        "report_file": config["report_file"],
        "checks_run": checks_run,
        "findings": findings,
        "required_next_action": "continue" if status == "passed" else "block",
        "notes": "Week-one Codex automation report generator; no source, issue, PR, dependency or release mutations are performed.",
    }


def main_codex_loop(loop_id: str) -> int:
    config = CODEX_LOOP_CONFIGS[loop_id]
    return run_report_cli(
        description=f"Write RSS Loop {loop_id} Codex automation report",
        filename=config["report_file"],
        builder=lambda root, run_id: build_codex_loop_report(root, run_id, loop_id),
    )

