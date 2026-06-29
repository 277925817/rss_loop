import json
import tempfile
import unittest
from pathlib import Path

from tools.common import is_valid_run_id, load_run_log_entries, write_json_report
from tools.budget import build_budget_report
from tools.codex_loop_reports import build_codex_loop_report
from tools.docs_drift import build_docs_drift_report
from tools.product_reports import build_product_stage_report
from tools.readiness import build_loop_readiness_report


REQUIRED_ROOT_FILES = {
    "LOOP.md": """Product Delivery
Daily Triage
Acceptance Sweeper
Docs Drift
Implementer
Verifier
The agent that implements a change must not approve it.
Acceptance Judge
Product-changing loops must use worktree isolation and must not edit main.
Human approval is required for denylisted paths and the third failed attempt.
MCP And Connector Policy
No MCP connector is required for local Product Delivery.
GitHub connector must not merge.
Codex Peripheral Automations
issue-triage
pr-babysitter
ci-sweeper
dependency-sweeper
changelog-drafter
post-merge-cleanup
gh
auto-close
branch protection
major dependency
""",
    "STATE.md": """# Loop State - RSS Loop

Last run: 2026-06-30T00:00:00Z

## Kill Switch

```yaml
loop_pause_all: false
product_delivery_pause: {pause}
reason: "{reason}"
```

## Current Mission

Control loop.

## Active Lanes

| lane_id | loop_id | acting_on | owner_agent | status | worktree_path | started_at |
| --- | --- | --- | --- | --- | --- | --- |
| none | none | none | none | idle | none | none |

## High Priority

- [x] HP-002 Produce the first readiness report.
- [x] HP-004 Implement command modules.

## Watch List

- none

## Human Inbox

- none

## Blocked Items

| blocker_id | scope | status | reason | required_resolution |
| --- | --- | --- | --- | --- |
| BLOCK-002 | product-delivery | {block_status} | {block_reason} | {block_resolution} |
""",
    "loop-budget.md": """Max runs/day
Max tokens/day
Max sub-agent spawns/run
Max attempts/item/day
Aggregate daily token cap
On Budget Exceed
budget_skipped
budget_exceeded
Daily Triage
Docs Drift
Acceptance Sweeper
Product Delivery
Issue Triage
PR Babysitter
CI Sweeper
Dependency Sweeper
Changelog Drafter
Post-Merge Cleanup
Kill Switches
""",
    "loop-run-log.md": """# Loop Run Log

Required fields:
- run_id
- loop_id
- started_at
- finished_at
- acting_on
- agents
- attempt
- tests
- gates
- outcome
- escalations

{"run_id":"seed","loop_id":"docs-drift","outcome":"report_only","agents":{}}
""",
    "loop-constraints.md": """Path Denylist
.env
Maker Checker Rules
Worktree Rules
Product-changing work must use a worktree and must not edit main.
Acceptance Rules
Auto-Merge Policy
Human Gate Rules
Escalate for denylisted paths and third failed attempt.
Secrets And Leak Rules
""",
    "workflows.md": """Maker/checker policy
Implementer
Verifier
The Implementer must not approve its own work.
Acceptance Judge
Product implementation must not start when STATE.md has product_delivery_pause: true.
""",
    "tasks.md": "loop_control:\n  control_plane: LOOP.md\n",
}


REQUIRED_DOC_FILES = {
    "docs/08_acceptance.md": "Product completion remains Stop Gate. STOP_ALLOWED does not satisfy LOOP_READY.\n",
    "docs/09_loop_readiness.md": "09_loop_readiness@codex-automation-v3\nLOOP-READY-001\nLOOP-READY-024\nLOOP_READY = true\nLoop readiness does not satisfy product acceptance.\n",
    "docs/safety.md": "loop-constraints.md\nAuto-merge\nConnector Policy\nGitHub connector\nmust not merge\nIncident Response\n",
    "docs/10_loop_usage.md": "Start Checklist\nProduct Delivery Runbook\n",
    "docs/11_evidence_and_reports.md": "Loop Readiness Report\nreports/<run_id>/loop-readiness-report.json\nbudget-report.json\nbudget_exceeded\nissue-triage-report.json\npr-babysitter-report.json\nci-sweeper-report.json\ndependency-sweeper-report.json\nchangelog-report.json\npost-merge-report.json\n",
    "docs/12_command_matrix.md": "python3 -m tools.report_loop_readiness\npython3 -m tools.report_static\npython3 -m tools.report_budget\ntools.report_issue_triage\ntools.report_pr_babysitter\ntools.report_ci_sweeper\ntools.report_dependency_sweeper\ntools.report_changelog\ntools.report_post_merge\nissue-triage-report.json\npr-babysitter-report.json\nci-sweeper-report.json\ndependency-sweeper-report.json\nchangelog-report.json\npost-merge-report.json\n",
    "docs/13_codex_automations.md": "Daily Triage\nIssue Triage\nPR Babysitter\nCI Sweeper\nDependency Sweeper\nChangelog Drafter\nPost-Merge Cleanup\nPrompt Templates\nWeek 1\nreport-only\ngh\nmust not merge\nauto-close\nbranch protection\nmajor dependency\nhuman explicitly enables\nMinimal-fix mode is disabled\nauto-merge remains disabled\n$issue-triage\n$pr-review-triage\n$ci-triage\n$dependency-triage\n$changelog-scan\n$post-merge-scan\nissue-triage-report.json\npr-babysitter-report.json\nci-sweeper-report.json\ndependency-sweeper-report.json\nchangelog-report.json\npost-merge-report.json\n",
}


REQUIRED_SKILL_FILES = [
    "skills/loop-triage/SKILL.md",
    "skills/loop-budget/SKILL.md",
    "skills/loop-verifier/SKILL.md",
    "skills/product-implementer/SKILL.md",
    "skills/verifier/SKILL.md",
    "skills/acceptance-judge/SKILL.md",
    "skills/docs-drift/SKILL.md",
]


def create_loop_fixture(root: Path, *, paused: bool) -> None:
    reason = (
        "Bootstrap readiness report has not enabled Product Delivery yet."
        if paused
        else "Product Delivery enabled by final readiness report."
    )
    block_status = "blocked" if paused else "resolved"
    block_reason = "Pending bootstrap enablement" if paused else "Resolved by bootstrap report"
    block_resolution = "Run final readiness report" if paused else "none"

    for relative_path, content in REQUIRED_ROOT_FILES.items():
        path = root / relative_path
        path.parent.mkdir(parents=True, exist_ok=True)
        rendered = content
        if relative_path == "STATE.md":
            rendered = content.format(
                pause=str(paused).lower(),
                reason=reason,
                block_status=block_status,
                block_reason=block_reason,
                block_resolution=block_resolution,
            )
        path.write_text(rendered, encoding="utf-8")

    for relative_path, content in REQUIRED_DOC_FILES.items():
        path = root / relative_path
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content, encoding="utf-8")

    for relative_path in REQUIRED_SKILL_FILES:
        path = root / relative_path
        path.parent.mkdir(parents=True, exist_ok=True)
        if relative_path == "skills/loop-budget/SKILL.md":
            content = "# loop-budget\n\nPurpose\n\nloop-budget.md\nbudget-report.json\n"
        elif relative_path == "skills/loop-verifier/SKILL.md":
            content = "# loop-verifier\n\nskills/verifier/SKILL.md\nDo not implement fixes\n"
        elif relative_path == "skills/verifier/SKILL.md":
            content = "# verifier\n\nreject-by-default\nDo not implement fixes\n"
        else:
            content = "# skill\n\nPurpose\n"
        path.write_text(content, encoding="utf-8")

    extra_files = {
        "patterns/registry.yaml": "daily-triage\ndocs-drift\nacceptance-sweeper\nproduct-delivery\nworktree_required\nissue-triage\npr-babysitter\nci-sweeper\ndependency-sweeper\nchangelog-drafter\npost-merge-cleanup\n",
        ".github/PULL_REQUEST_TEMPLATE.md": "No denylisted paths touched\nnpx @cobusgreyling/loop-audit . --suggest\n",
        ".github/workflows/loop-audit.yml": "python3 -m unittest discover -s tests\nnpx @cobusgreyling/loop-audit . --suggest\n",
        ".codex/agents/verifier.toml": "name = \"verifier\"\nexamples-compatible verifier alias\nskills/loop-verifier/SKILL.md\nskills/verifier/SKILL.md\n",
        ".codex/skills/loop-constraints/SKILL.md": "# loop-constraints\n\nreport-only\nDo not\nSKILL.md\n",
        ".codex/skills/loop-triage/SKILL.md": "# loop-triage\n\nreport-only\nDo not\nSKILL.md\n",
        ".codex/skills/loop-verifier/SKILL.md": "# loop-verifier\n\nreport-only\nDo not\nSKILL.md\n",
        ".codex/skills/product-implementer/SKILL.md": "# product-implementer\n\nreport-only\nDo not\nSKILL.md\n",
        ".codex/skills/acceptance-judge/SKILL.md": "# acceptance-judge\n\nreport-only\nDo not\nSKILL.md\n",
        ".codex/skills/issue-triage/SKILL.md": "# issue-triage\n\nreport-only\nDo not\nSKILL.md\n",
        ".codex/skills/pr-review-triage/SKILL.md": "# pr-review-triage\n\nreport-only\nDo not\nSKILL.md\n",
        ".codex/skills/ci-triage/SKILL.md": "# ci-triage\n\nreport-only\nDo not\nSKILL.md\n",
        ".codex/skills/dependency-triage/SKILL.md": "# dependency-triage\n\nreport-only\nDo not\nSKILL.md\n",
        ".codex/skills/changelog-scan/SKILL.md": "# changelog-scan\n\nreport-only\nDo not\nSKILL.md\n",
        ".codex/skills/draft-release-notes/SKILL.md": "# draft-release-notes\n\nreport-only\nDo not\nSKILL.md\n",
        ".codex/skills/post-merge-scan/SKILL.md": "# post-merge-scan\n\nreport-only\nDo not\nSKILL.md\n",
        ".codex/skills/minimal-fix/SKILL.md": "# minimal-fix\n\nreport-only\nDo not\nSKILL.md\n",
        "issue-triage-state.md": "Last run: never\nMode: report-only\nRecent Result\n",
        "pr-babysitter-state.md": "Last run: never\nMode: report-only\nRecent Result\n",
        "ci-sweeper-state.md": "Last run: never\nMode: report-only\nRecent Result\n",
        "dependency-sweeper-state.md": "Last run: never\nMode: report-only\nRecent Result\n",
        "changelog-drafter-state.md": "Last run: never\nMode: report-only\nRecent Result\n",
        "post-merge-state.md": "Last run: never\nMode: report-only\nRecent Result\n",
        "reports/run-bootstrap/loop-audit.txt": "Score: 100/100  Level: L3\n",
        "reports/run-final/loop-audit.txt": "Score: 100/100  Level: L3\n",
    }
    for relative_path, content in extra_files.items():
        path = root / relative_path
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content, encoding="utf-8")


class LoopReportsTest(unittest.TestCase):
    def test_run_id_validation_rejects_path_traversal(self) -> None:
        self.assertTrue(is_valid_run_id("2026-06-30T10:00:00Z-readiness-final"))
        for value in ["", "../x", "/tmp/x", "a/b", "a\\b", ".", ".."]:
            self.assertFalse(is_valid_run_id(value))

    def test_write_json_report_round_trips_under_run_directory(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            path = write_json_report(root, "run-1", "sample.json", {"ok": True})

            self.assertEqual(path, root / "reports" / "run-1" / "sample.json")
            self.assertEqual(json.loads(path.read_text(encoding="utf-8")), {"ok": True})

    def test_load_run_log_entries_ignores_markdown_lines(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "loop-run-log.md").write_text(
                "# log\n\nnot json\n{\"run_id\":\"a\",\"loop_id\":\"daily-triage\"}\n",
                encoding="utf-8",
            )

            entries = load_run_log_entries(root)

            self.assertEqual(entries, [{"run_id": "a", "loop_id": "daily-triage"}])

    def test_readiness_bootstrap_blocks_only_active_pause_gate(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            create_loop_fixture(root, paused=True)

            report = build_loop_readiness_report(root, "run-bootstrap")

            self.assertEqual(report["gate_status"]["LOOP-READY-010"], "BLOCKED")
            self.assertFalse(report["loop_ready"])
            self.assertEqual(report["required_next_action"], "enable_product_delivery")

    def test_readiness_final_passes_when_pause_is_cleared(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            create_loop_fixture(root, paused=False)

            report = build_loop_readiness_report(root, "run-final")

            self.assertTrue(report["loop_ready"])
            self.assertEqual(set(report["failed_or_blocked_gates"]), set())
            self.assertTrue(all(value == "PASS" for value in report["gate_status"].values()))

    def test_product_stage_report_does_not_fake_completion(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)

            report = build_product_stage_report(root, "run-static", "static")

            self.assertEqual(report["reports"][0]["status"], "failed")
            self.assertEqual(report["reports"][0]["stage"], "static")
            self.assertNotEqual(report["reports"][0]["assertions"], [])

    def test_budget_report_passes_with_caps_and_run_log(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            create_loop_fixture(root, paused=False)

            report = build_budget_report(root, "run-budget")

            self.assertEqual(report["status"], "passed")
            self.assertEqual(report["required_next_action"], "continue")

    def test_codex_loop_report_passes_for_issue_triage(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            create_loop_fixture(root, paused=False)

            report = build_codex_loop_report(root, "run-codex", "issue-triage")

            self.assertEqual(report["status"], "passed")
            self.assertEqual(report["mode"], "report-only")
            self.assertEqual(report["required_next_action"], "continue")

    def test_docs_drift_catches_old_prd_table_names(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            create_loop_fixture(root, paused=False)
            (root / "docs/01_prd.md").write_text("requires rss_source and news_task\n", encoding="utf-8")

            report = build_docs_drift_report(root, "run-drift")

            self.assertEqual(report["status"], "failed")
            self.assertIn("old_prd_table_names", {finding["check"] for finding in report["findings"]})

    def test_docs_drift_accepts_resolved_contracts(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            create_loop_fixture(root, paused=False)
            contract_files = {
                "docs/01_prd.md": "内部软删除 已软删除 URL fallback `score = 0` `is_selected = 0`\n",
                "docs/03_ui_spec.md": "PATCH /api/sources/{id} is_deleted 未删除信息源\n",
                "docs/04_data_model.md": "is_deleted 软删除 error_category fallback `score = 0`\n",
                "docs/05_api_contract.md": "Return all non-deleted RSS sources is_deleted `summary_zh` is required type TranslatedNewsListItem\n",
                "docs/06_dev_rules.md": "fallback `score = 0` `timeout`\n",
                "docs/07_test_spec.md": "validation | timeout | unknown score = 0 is_deleted\n",
                "tasks.md": "is_deleted = 1 fallback score = 0\n",
            }
            for relative_path, text in contract_files.items():
                path = root / relative_path
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_text(text, encoding="utf-8")

            report = build_docs_drift_report(root, "run-drift")

            self.assertEqual(report["status"], "passed")
            self.assertEqual(report["findings"], [])

    def test_docs_drift_catches_source_delete_contract_drift(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            create_loop_fixture(root, paused=False)
            (root / "docs/05_api_contract.md").write_text(
                "Return all RSS sources. MVP delete is implemented as disabling the source.\n",
                encoding="utf-8",
            )

            report = build_docs_drift_report(root, "run-drift")

            self.assertEqual(report["status"], "failed")
            self.assertIn("api_source_soft_delete_contract", {finding["check"] for finding in report["findings"]})

    def test_docs_drift_catches_readiness_yaml_tabs(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            create_loop_fixture(root, paused=False)
            (root / "docs/09_loop_readiness.md").write_text(
                "```yaml\nloop_readiness_gate:\n\tbad_indent: true\n```\n",
                encoding="utf-8",
            )

            report = build_docs_drift_report(root, "run-drift")

            self.assertEqual(report["status"], "failed")
            self.assertIn("readiness_yaml_tabs", {finding["check"] for finding in report["findings"]})


if __name__ == "__main__":
    unittest.main()
