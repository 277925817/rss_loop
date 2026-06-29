from __future__ import annotations

import re
from pathlib import Path
from typing import Any


CHECKED_EXTENSIONS = {".md", ".txt"}


def _iter_checked_files(root: Path) -> list[Path]:
    ignored_parts = {".git", "reports", "evidence", "__pycache__", ".pytest_cache"}
    paths: list[Path] = []
    for path in root.rglob("*"):
        if not path.is_file():
            continue
        if any(part in ignored_parts for part in path.parts):
            continue
        if path.suffix in CHECKED_EXTENSIONS or path.name in {"AGENTS.md", "LOOP.md", "STATE.md"}:
            paths.append(path)
    return sorted(paths)


def build_docs_drift_report(root: Path, run_id: str) -> dict[str, Any]:
    findings: list[dict[str, str]] = []
    old_stack_blocker = "Flask versus " + "FastAPI"
    old_python_command = r"(?<!3)" + "python -m " + "tools"
    for path in _iter_checked_files(root):
        rel = path.relative_to(root).as_posix()
        text = path.read_text(encoding="utf-8")
        if old_stack_blocker in text:
            findings.append({"file": rel, "check": "old_stack_blocker", "message": "Old Flask/FastAPI blocker remains."})
        if re.search(old_python_command, text):
            findings.append({"file": rel, "check": "python3_command", "message": "Command docs must use python3 -m tools."})
        if rel == "AGENTS.md" and "Always start from `LOOP.md`." in text:
            findings.append({"file": rel, "check": "control_order", "message": "AGENTS.md still tells agents to start from LOOP.md first."})

        if rel == "docs/01_prd.md":
            old_table_terms = ["rss_source", "news_task", "title_domain_hash"]
            matches = [term for term in old_table_terms if term in text]
            if matches:
                findings.append(
                    {
                        "file": rel,
                        "check": "old_prd_table_names",
                        "message": "PRD still requires old table/task names.",
                        "matches": ", ".join(matches),
                    }
                )
            if re.search(r"pipeline_state[^.\n]*(selected|ready|translated|translation_failed)", text):
                findings.append(
                    {
                        "file": rel,
                        "check": "old_prd_lifecycle_state",
                        "message": "PRD still treats API/UI status as database pipeline_state.",
                    }
                )
            if "内部软删除" not in text or "已软删除 URL" not in text:
                findings.append(
                    {
                        "file": rel,
                        "check": "source_soft_delete_contract",
                        "message": "PRD must describe source delete as internal soft delete and reserve soft-deleted URLs.",
                    }
                )
            if "fallback `score = 0`" not in text or "`is_selected = 0`" not in text:
                findings.append(
                    {
                        "file": rel,
                        "check": "llm_scoring_fallback_contract",
                        "message": "PRD must define scoring retry failure as system fallback score 0 with is_selected 0.",
                    }
                )

        if rel == "docs/02_arch.md" and re.search(r"raw\s*→\s*scored\s*→\s*selected", text):
            findings.append(
                {
                    "file": rel,
                    "check": "old_arch_data_flow",
                    "message": "Architecture data flow still includes old selected/ready/translated database states.",
                }
            )

        if rel == "docs/03_ui_spec.md":
            if "MVP 不提供启用 / 禁用控件" in text:
                findings.append(
                    {
                        "file": rel,
                        "check": "ui_toggle_conflict",
                        "message": "UI spec conflicts with PATCH /api/sources/{id} source toggle contract.",
                    }
                )
            if "PATCH /api/sources/{id}" not in text:
                findings.append(
                    {
                        "file": rel,
                        "check": "ui_toggle_binding_missing",
                        "message": "UI spec does not bind source toggle to PATCH /api/sources/{id}.",
                    }
                )
            if "is_deleted" not in text or "未删除信息源" not in text:
                findings.append(
                    {
                        "file": rel,
                        "check": "ui_source_delete_contract",
                        "message": "UI spec must render only non-deleted sources and forbid reading is_deleted.",
                    }
                )

        if rel == "docs/04_data_model.md":
            required_terms = ["is_deleted", "软删除", "error_category", "fallback `score = 0`"]
            missing_terms = [term for term in required_terms if term not in text]
            if missing_terms:
                findings.append(
                    {
                        "file": rel,
                        "check": "data_contract_drift",
                        "message": "Data model lacks source soft-delete, processing_log error_category, or scoring fallback facts.",
                        "matches": ", ".join(missing_terms),
                    }
                )

        if rel == "docs/05_api_contract.md":
            if "Return all non-deleted RSS sources" not in text or "is_deleted" not in text:
                findings.append(
                    {
                        "file": rel,
                        "check": "api_source_soft_delete_contract",
                        "message": "API contract must return non-deleted sources and forbid exposing is_deleted.",
                    }
                )
            if "`summary_zh` is required" not in text or "type TranslatedNewsListItem" not in text:
                findings.append(
                    {
                        "file": rel,
                        "check": "api_translated_summary_contract",
                        "message": "API contract must require summary_zh for translated list/detail responses.",
                    }
                )
            if "`summary_zh` is optional" in text:
                findings.append(
                    {
                        "file": rel,
                        "check": "api_translated_summary_optional",
                        "message": "API contract still says summary_zh is optional for translated responses.",
                    }
                )

        if rel == "docs/06_dev_rules.md":
            if "fallback `score = 0`" not in text or "`timeout`" not in text:
                findings.append(
                    {
                        "file": rel,
                        "check": "dev_rules_llm_timeout_contract",
                        "message": "Dev rules must include scoring fallback and timeout error category.",
                    }
                )

        if rel == "docs/07_test_spec.md":
            if "validation | timeout | unknown" not in text or "score = 0" not in text:
                findings.append(
                    {
                        "file": rel,
                        "check": "test_spec_timeout_fallback_contract",
                        "message": "Test spec must include timeout error_category and scoring fallback checks.",
                    }
                )
            if "is_deleted" not in text:
                findings.append(
                    {
                        "file": rel,
                        "check": "test_spec_is_deleted_contract",
                        "message": "Test spec must assert is_deleted exists internally and is not exposed.",
                    }
                )

        if rel == "docs/09_loop_readiness.md" and "\t" in text:
            findings.append(
                {
                    "file": rel,
                    "check": "readiness_yaml_tabs",
                    "message": "Loop readiness YAML block must not contain tabs or tab-indented list items.",
                }
            )

        if rel == "tasks.md":
            if "max_retry: 2" in text:
                findings.append(
                    {
                        "file": rel,
                        "check": "task_retry_mismatch",
                        "message": "tasks.md retry policy must match workflow retry limit 3.",
                    }
                )
            non_canonical = [
                term
                for term in ["static_unit", "pipeline_test", "api_test", "ui_test", "integration_test"]
                if term in text
            ]
            if non_canonical:
                findings.append(
                    {
                        "file": rel,
                        "check": "non_canonical_stage_labels",
                        "message": "tasks.md still uses non-canonical stage labels.",
                        "matches": ", ".join(non_canonical),
                    }
                )
            if "is_deleted = 1" not in text or "fallback score = 0" not in text:
                findings.append(
                    {
                        "file": rel,
                        "check": "tasks_contract_drift",
                        "message": "tasks.md must encode source soft delete and scoring fallback requirements.",
                    }
                )

    status = "passed" if not findings else "failed"
    return {
        "run_id": run_id,
        "schema_ref": "docs/11_evidence_and_reports.md#docs-drift",
        "schema_version": "v1",
        "status": status,
        "checks_run": [
            "old_stack_blocker",
            "python3_command",
            "control_order",
            "old_prd_table_names",
            "old_prd_lifecycle_state",
            "old_arch_data_flow",
            "ui_toggle_conflict",
            "ui_toggle_binding_missing",
            "source_soft_delete_contract",
            "llm_scoring_fallback_contract",
            "ui_source_delete_contract",
            "data_contract_drift",
            "api_source_soft_delete_contract",
            "api_translated_summary_contract",
            "api_translated_summary_optional",
            "dev_rules_llm_timeout_contract",
            "test_spec_timeout_fallback_contract",
            "test_spec_is_deleted_contract",
            "readiness_yaml_tabs",
            "task_retry_mismatch",
            "non_canonical_stage_labels",
            "tasks_contract_drift",
        ],
        "findings": findings,
        "required_next_action": "continue" if status == "passed" else "fix",
    }
