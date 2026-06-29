from __future__ import annotations

import importlib.util
from pathlib import Path
from typing import Any

from .common import contains_all, file_exists, load_run_log_entries, read_text, state_flag


REQUIRED_CONTROL_FILES = [
    "LOOP.md",
    "STATE.md",
    "loop-budget.md",
    "loop-run-log.md",
    "loop-constraints.md",
    "docs/safety.md",
    "docs/09_loop_readiness.md",
    "docs/10_loop_usage.md",
    "docs/11_evidence_and_reports.md",
    "docs/12_command_matrix.md",
    "docs/13_codex_automations.md",
    "patterns/registry.yaml",
    "skills/loop-triage/SKILL.md",
    "skills/loop-budget/SKILL.md",
    "skills/loop-verifier/SKILL.md",
    "skills/product-implementer/SKILL.md",
    "skills/verifier/SKILL.md",
    "skills/acceptance-judge/SKILL.md",
    "skills/docs-drift/SKILL.md",
    ".codex/skills/loop-constraints/SKILL.md",
    ".codex/skills/loop-triage/SKILL.md",
    ".codex/skills/loop-verifier/SKILL.md",
    ".codex/skills/product-implementer/SKILL.md",
    ".codex/skills/acceptance-judge/SKILL.md",
    ".codex/skills/issue-triage/SKILL.md",
    ".codex/skills/pr-review-triage/SKILL.md",
    ".codex/skills/ci-triage/SKILL.md",
    ".codex/skills/dependency-triage/SKILL.md",
    ".codex/skills/changelog-scan/SKILL.md",
    ".codex/skills/draft-release-notes/SKILL.md",
    ".codex/skills/post-merge-scan/SKILL.md",
    ".codex/skills/minimal-fix/SKILL.md",
    ".github/PULL_REQUEST_TEMPLATE.md",
    ".github/workflows/loop-audit.yml",
    "issue-triage-state.md",
    "pr-babysitter-state.md",
    "ci-sweeper-state.md",
    "dependency-sweeper-state.md",
    "changelog-drafter-state.md",
    "post-merge-state.md",
]

REQUIRED_COMMAND_MODULES = [
    "tools.report_loop_readiness",
    "tools.report_docs_drift",
    "tools.report_budget",
    "tools.report_verifier",
    "tools.report_acceptance",
    "tools.report_static",
    "tools.report_unit",
    "tools.report_contract",
    "tools.report_api",
    "tools.report_integration",
    "tools.report_replay",
    "tools.report_snapshot",
    "tools.report_e2e",
    "tools.report_issue_triage",
    "tools.report_pr_babysitter",
    "tools.report_ci_sweeper",
    "tools.report_dependency_sweeper",
    "tools.report_changelog",
    "tools.report_post_merge",
]

GATES = [f"LOOP-READY-{index:03d}" for index in range(1, 25)]

CODEX_CORE_SKILLS = [
    ".codex/skills/loop-constraints/SKILL.md",
    ".codex/skills/loop-triage/SKILL.md",
    ".codex/skills/loop-verifier/SKILL.md",
    ".codex/skills/product-implementer/SKILL.md",
    ".codex/skills/acceptance-judge/SKILL.md",
]

CODEX_PERIPHERAL_SKILLS = [
    ".codex/skills/issue-triage/SKILL.md",
    ".codex/skills/pr-review-triage/SKILL.md",
    ".codex/skills/ci-triage/SKILL.md",
    ".codex/skills/dependency-triage/SKILL.md",
    ".codex/skills/changelog-scan/SKILL.md",
    ".codex/skills/draft-release-notes/SKILL.md",
    ".codex/skills/post-merge-scan/SKILL.md",
    ".codex/skills/minimal-fix/SKILL.md",
]

CODEX_STATE_FILES = [
    "issue-triage-state.md",
    "pr-babysitter-state.md",
    "ci-sweeper-state.md",
    "dependency-sweeper-state.md",
    "changelog-drafter-state.md",
    "post-merge-state.md",
]

CODEX_REPORT_MODULES = [
    "tools.report_issue_triage",
    "tools.report_pr_babysitter",
    "tools.report_ci_sweeper",
    "tools.report_dependency_sweeper",
    "tools.report_changelog",
    "tools.report_post_merge",
]

CODEX_REPORT_FILES = [
    "issue-triage-report.json",
    "pr-babysitter-report.json",
    "ci-sweeper-report.json",
    "dependency-sweeper-report.json",
    "changelog-report.json",
    "post-merge-report.json",
]


def _module_exists(name: str) -> bool:
    return importlib.util.find_spec(name) is not None


def _read_optional(root: Path, relative_path: str) -> str:
    path = root / relative_path
    if not path.exists():
        return ""
    return path.read_text(encoding="utf-8")


def _state_has_active_product_blocker(state_text: str) -> bool:
    return "| BLOCK-002 | product-delivery | blocked |" in state_text


def _current_loop_audit_text(root: Path, run_id: str) -> str:
    candidates = [
        root / "reports" / run_id / "loop-audit.txt",
        root / "reports" / "loop-audit-latest.txt",
    ]
    for path in candidates:
        if path.exists():
            return path.read_text(encoding="utf-8")
    return ""


def build_loop_readiness_report(root: Path, run_id: str) -> dict[str, Any]:
    gate_status: dict[str, str] = {}
    evidence: list[str] = []
    notes: dict[str, str] = {}

    missing_files = [path for path in REQUIRED_CONTROL_FILES if not file_exists(root, path)]
    missing_modules = [name for name in REQUIRED_COMMAND_MODULES if not _module_exists(name)]
    if missing_files or missing_modules:
        gate_status["LOOP-READY-001"] = "FAIL"
        notes["LOOP-READY-001"] = f"missing_files={missing_files}; missing_modules={missing_modules}"
    else:
        gate_status["LOOP-READY-001"] = "PASS"
        evidence.extend(REQUIRED_CONTROL_FILES)

    state_text = _read_optional(root, "STATE.md")
    state_sections = [
        "Last run",
        "## Kill Switch",
        "## Current Mission",
        "## Active Lanes",
        "## High Priority",
        "## Watch List",
        "## Human Inbox",
        "## Blocked Items",
    ]
    if contains_all(state_text, state_sections) and state_flag(state_text, "product_delivery_pause") is not None:
        gate_status["LOOP-READY-002"] = "PASS"
        evidence.append("STATE.md")
    else:
        gate_status["LOOP-READY-002"] = "FAIL"
        notes["LOOP-READY-002"] = "STATE.md lacks required sections or product_delivery_pause flag."

    budget_text = _read_optional(root, "loop-budget.md")
    if contains_all(budget_text, ["Max runs/day", "Max tokens/day", "Max sub-agent", "On Budget Exceed", "Kill"]):
        gate_status["LOOP-READY-003"] = "PASS"
        evidence.append("loop-budget.md")
    else:
        gate_status["LOOP-READY-003"] = "FAIL"
        notes["LOOP-READY-003"] = "loop-budget.md lacks caps or exceed behavior."

    run_log_text = _read_optional(root, "loop-run-log.md")
    run_log_entries = load_run_log_entries(root)
    run_log_fields = ["run_id", "loop_id", "started_at", "finished_at", "acting_on", "agents", "attempt", "tests", "gates", "outcome", "escalations"]
    if contains_all(run_log_text, run_log_fields) and run_log_entries:
        gate_status["LOOP-READY-004"] = "PASS"
        evidence.append("loop-run-log.md")
    else:
        gate_status["LOOP-READY-004"] = "FAIL"
        notes["LOOP-READY-004"] = "loop-run-log.md lacks schema fields or parseable JSONL entries."

    constraints_text = _read_optional(root, "loop-constraints.md")
    if contains_all(constraints_text, ["Path Denylist", ".env", "Maker Checker", "Worktree", "Auto-Merge", "Human Gate", "Secrets"]):
        gate_status["LOOP-READY-005"] = "PASS"
        evidence.append("loop-constraints.md")
    else:
        gate_status["LOOP-READY-005"] = "FAIL"
        notes["LOOP-READY-005"] = "loop-constraints.md lacks denylist, auto-merge, human gate or secret rules."

    loop_text = _read_optional(root, "LOOP.md")
    workflows_text = _read_optional(root, "workflows.md")
    if contains_all(loop_text + workflows_text + constraints_text, ["Implementer", "Verifier", "must not approve", "Acceptance Judge"]):
        gate_status["LOOP-READY-006"] = "PASS"
        evidence.extend(["LOOP.md", "workflows.md", "loop-constraints.md"])
    else:
        gate_status["LOOP-READY-006"] = "FAIL"
        notes["LOOP-READY-006"] = "Maker/checker separation is incomplete."

    if contains_all(loop_text + constraints_text, ["worktree", "Product-changing", "main"]):
        gate_status["LOOP-READY-007"] = "PASS"
        evidence.extend(["LOOP.md", "loop-constraints.md"])
    else:
        gate_status["LOOP-READY-007"] = "FAIL"
        notes["LOOP-READY-007"] = "Worktree isolation policy is incomplete."

    handoff_text = loop_text + constraints_text + state_text
    has_attempt_gate = "third failed attempt" in handoff_text or "three failed attempts" in handoff_text
    if contains_all(handoff_text, ["Human", "denylisted", "Human Inbox"]) and has_attempt_gate:
        gate_status["LOOP-READY-008"] = "PASS"
        evidence.extend(["LOOP.md", "loop-constraints.md", "STATE.md"])
    else:
        gate_status["LOOP-READY-008"] = "FAIL"
        notes["LOOP-READY-008"] = "Human handoff rules are incomplete."

    acceptance_text = _read_optional(root, "docs/08_acceptance.md")
    readiness_text = _read_optional(root, "docs/09_loop_readiness.md")
    if "STOP_ALLOWED" in acceptance_text and "LOOP_READY" in readiness_text and "does not" in acceptance_text + readiness_text:
        gate_status["LOOP-READY-009"] = "PASS"
        evidence.extend(["docs/08_acceptance.md", "docs/09_loop_readiness.md"])
    else:
        gate_status["LOOP-READY-009"] = "FAIL"
        notes["LOOP-READY-009"] = "Product acceptance and loop readiness separation is incomplete."

    loop_paused = state_flag(state_text, "loop_pause_all")
    product_paused = state_flag(state_text, "product_delivery_pause")
    if loop_paused:
        gate_status["LOOP-READY-010"] = "BLOCKED"
        notes["LOOP-READY-010"] = "loop_pause_all is true."
    elif product_paused:
        gate_status["LOOP-READY-010"] = "BLOCKED"
        notes["LOOP-READY-010"] = "product_delivery_pause is true; bootstrap report may enable Product Delivery."
    elif _state_has_active_product_blocker(state_text):
        gate_status["LOOP-READY-010"] = "BLOCKED"
        notes["LOOP-READY-010"] = "STATE.md contains an active Product Delivery blocker."
    else:
        gate_status["LOOP-READY-010"] = "PASS"
        evidence.append("STATE.md")

    safety_text = _read_optional(root, "docs/safety.md")
    if contains_all(
        safety_text,
        [
            "loop-constraints.md",
            "Auto-merge",
            "Connector Policy",
            "GitHub connector",
            "must not merge",
            "Incident Response",
        ],
    ):
        gate_status["LOOP-READY-011"] = "PASS"
        evidence.append("docs/safety.md")
    else:
        gate_status["LOOP-READY-011"] = "FAIL"
        notes["LOOP-READY-011"] = "docs/safety.md lacks safety companion, connector, auto-merge or incident response policy."

    command_matrix_text = _read_optional(root, "docs/12_command_matrix.md")
    evidence_text = _read_optional(root, "docs/11_evidence_and_reports.md")
    budget_skill_text = _read_optional(root, "skills/loop-budget/SKILL.md")
    if contains_all(
        budget_skill_text + command_matrix_text + evidence_text,
        ["budget-report.json", "tools.report_budget", "loop-budget.md", "budget_exceeded"],
    ):
        gate_status["LOOP-READY-012"] = "PASS"
        evidence.extend(["skills/loop-budget/SKILL.md", "docs/12_command_matrix.md", "docs/11_evidence_and_reports.md"])
    else:
        gate_status["LOOP-READY-012"] = "FAIL"
        notes["LOOP-READY-012"] = "Budget skill, command matrix or report contract is incomplete."

    loop_verifier_text = _read_optional(root, "skills/loop-verifier/SKILL.md")
    codex_verifier_text = _read_optional(root, ".codex/agents/verifier.toml")
    verifier_text = _read_optional(root, "skills/verifier/SKILL.md")
    if contains_all(loop_verifier_text + codex_verifier_text + verifier_text, ["loop-verifier", "skills/verifier/SKILL.md", "reject-by-default", "Do not implement fixes"]):
        gate_status["LOOP-READY-013"] = "PASS"
        evidence.extend(["skills/loop-verifier/SKILL.md", "skills/verifier/SKILL.md", ".codex/agents/verifier.toml"])
    else:
        gate_status["LOOP-READY-013"] = "FAIL"
        notes["LOOP-READY-013"] = "Loop verifier compatibility entrypoint is incomplete."

    registry_text = _read_optional(root, "patterns/registry.yaml")
    if contains_all(registry_text, ["daily-triage", "docs-drift", "acceptance-sweeper", "product-delivery", "worktree_required"]):
        gate_status["LOOP-READY-014"] = "PASS"
        evidence.append("patterns/registry.yaml")
    else:
        gate_status["LOOP-READY-014"] = "FAIL"
        notes["LOOP-READY-014"] = "patterns/registry.yaml lacks required loop pattern entries."

    if contains_all(loop_text + safety_text, ["MCP", "GitHub connector", "must not merge", "No MCP connector is required"]):
        gate_status["LOOP-READY-015"] = "PASS"
        evidence.extend(["LOOP.md", "docs/safety.md"])
    else:
        gate_status["LOOP-READY-015"] = "FAIL"
        notes["LOOP-READY-015"] = "MCP/connector least-privilege policy is missing."

    workflow_text = _read_optional(root, ".github/workflows/loop-audit.yml")
    pr_template_text = _read_optional(root, ".github/PULL_REQUEST_TEMPLATE.md")
    if contains_all(workflow_text + pr_template_text, ["python3 -m unittest discover -s tests", "npx @cobusgreyling/loop-audit . --suggest", "No denylisted paths touched"]):
        gate_status["LOOP-READY-016"] = "PASS"
        evidence.extend([".github/workflows/loop-audit.yml", ".github/PULL_REQUEST_TEMPLATE.md"])
    else:
        gate_status["LOOP-READY-016"] = "FAIL"
        notes["LOOP-READY-016"] = "GitHub audit workflow or PR safety template is incomplete."

    loop_audit_text = _current_loop_audit_text(root, run_id)
    if "Level: L3" in loop_audit_text:
        gate_status["LOOP-READY-017"] = "PASS"
        evidence.append(f"reports/{run_id}/loop-audit.txt")
    else:
        gate_status["LOOP-READY-017"] = "FAIL"
        notes["LOOP-READY-017"] = "Current external loop-audit evidence is missing or not Level: L3."

    missing_codex_skills = [
        path
        for path in CODEX_CORE_SKILLS + CODEX_PERIPHERAL_SKILLS
        if not file_exists(root, path)
    ]
    codex_skill_text = "\n".join(_read_optional(root, path) for path in CODEX_CORE_SKILLS + CODEX_PERIPHERAL_SKILLS)
    if not missing_codex_skills and contains_all(codex_skill_text, ["report-only", "Do not", "SKILL.md"]):
        gate_status["LOOP-READY-018"] = "PASS"
        evidence.extend(CODEX_CORE_SKILLS + CODEX_PERIPHERAL_SKILLS)
    else:
        gate_status["LOOP-READY-018"] = "FAIL"
        notes["LOOP-READY-018"] = f"Codex skill entrypoints are missing or incomplete: {missing_codex_skills}"

    automation_text = _read_optional(root, "docs/13_codex_automations.md")
    automation_terms = [
        "Daily Triage",
        "Issue Triage",
        "PR Babysitter",
        "CI Sweeper",
        "Dependency Sweeper",
        "Changelog Drafter",
        "Post-Merge Cleanup",
        "Prompt Templates",
        "Week 1",
        "report-only",
        "gh",
    ]
    if contains_all(automation_text, automation_terms):
        gate_status["LOOP-READY-019"] = "PASS"
        evidence.append("docs/13_codex_automations.md")
    else:
        gate_status["LOOP-READY-019"] = "FAIL"
        notes["LOOP-READY-019"] = "docs/13_codex_automations.md lacks required automation prompts, cadence, gh fallback or report-only policy."

    missing_state_files = [path for path in CODEX_STATE_FILES if not file_exists(root, path)]
    state_file_text = "\n".join(_read_optional(root, path) for path in CODEX_STATE_FILES)
    if not missing_state_files and contains_all(state_file_text, ["Last run", "Mode:", "Recent Result"]):
        gate_status["LOOP-READY-020"] = "PASS"
        evidence.extend(CODEX_STATE_FILES)
    else:
        gate_status["LOOP-READY-020"] = "FAIL"
        notes["LOOP-READY-020"] = f"Codex peripheral state files are missing or incomplete: {missing_state_files}"

    github_policy_text = loop_text + "\n" + safety_text + "\n" + automation_text
    if contains_all(
        github_policy_text,
        ["gh", "GitHub connector", "must not merge", "auto-close", "branch protection", "major dependency"],
    ):
        gate_status["LOOP-READY-021"] = "PASS"
        evidence.extend(["LOOP.md", "docs/safety.md", "docs/13_codex_automations.md"])
    else:
        gate_status["LOOP-READY-021"] = "FAIL"
        notes["LOOP-READY-021"] = "Codex GitHub least-privilege policy is incomplete."

    if contains_all(
        codex_verifier_text,
        ['name = "verifier"', "examples-compatible verifier alias", "skills/loop-verifier/SKILL.md", "skills/verifier/SKILL.md"],
    ):
        gate_status["LOOP-READY-022"] = "PASS"
        evidence.append(".codex/agents/verifier.toml")
    else:
        gate_status["LOOP-READY-022"] = "FAIL"
        notes["LOOP-READY-022"] = "Codex verifier agent is not examples-compatible."

    if contains_all(
        automation_text,
        ["Week 1", "report-only", "human explicitly enables", "Minimal-fix mode is disabled", "auto-merge remains disabled"],
    ):
        gate_status["LOOP-READY-023"] = "PASS"
        evidence.append("docs/13_codex_automations.md")
    else:
        gate_status["LOOP-READY-023"] = "FAIL"
        notes["LOOP-READY-023"] = "Week-one report-only and human-enabled minimal-fix policy is incomplete."

    missing_codex_modules = [name for name in CODEX_REPORT_MODULES if not _module_exists(name)]
    report_docs_text = command_matrix_text + "\n" + evidence_text
    missing_report_docs = [
        item
        for item in CODEX_REPORT_MODULES + CODEX_REPORT_FILES
        if item not in report_docs_text
    ]
    if not missing_codex_modules and not missing_report_docs:
        gate_status["LOOP-READY-024"] = "PASS"
        evidence.extend(["docs/11_evidence_and_reports.md", "docs/12_command_matrix.md"])
    else:
        gate_status["LOOP-READY-024"] = "FAIL"
        notes["LOOP-READY-024"] = f"Codex report commands or report docs are incomplete: modules={missing_codex_modules}; docs={missing_report_docs}"

    failed_or_blocked = [gate for gate in GATES if gate_status.get(gate) != "PASS"]
    loop_ready = not failed_or_blocked
    only_pause_blocked = failed_or_blocked == ["LOOP-READY-010"] and product_paused is True and not loop_paused
    if loop_ready:
        next_action = "continue"
    elif only_pause_blocked:
        next_action = "enable_product_delivery"
    else:
        next_action = "block"

    return {
        "run_id": run_id,
        "schema_ref": "docs/09_loop_readiness.md",
        "schema_version": "09_loop_readiness@codex-automation-v3",
        "gate_status": gate_status,
        "loop_ready": loop_ready,
        "evidence_paths": sorted(set(evidence)),
        "failed_or_blocked_gates": failed_or_blocked,
        "required_next_action": next_action,
        "notes": notes,
    }
