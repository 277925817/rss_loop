from __future__ import annotations

from pathlib import Path
from typing import Any

from .common import run_report_cli, utc_now


PRODUCT_STAGES = {
    "static",
    "unit",
    "contract",
    "api",
    "integration",
    "replay",
    "snapshot",
    "e2e",
}

ACC_STOP_GATES = [f"ACC-STOP-{index:03d}" for index in range(1, 11)]


def build_product_stage_report(root: Path, run_id: str, stage: str) -> dict[str, Any]:
    if stage not in PRODUCT_STAGES:
        raise ValueError(f"unknown product report stage: {stage}")
    status = "failed" if stage == "static" else "skipped"
    assertion_status = "failed" if status == "failed" else "skipped"
    return {
        "run_id": run_id,
        "schema_ref": "docs/07_test_spec.md#6",
        "schema_version": "v1",
        "reports": [
            {
                "schema_ref": "07_test_spec.md#6",
                "schema_version": "v1",
                "test_id": f"LOOP-BOOTSTRAP-{stage.upper()}",
                "stage": stage,
                "status": status,
                "failure_type": "contract" if stage in {"static", "contract"} else "integration",
                "error_category": "unknown",
                "trace_id": f"{run_id}-{stage}",
                "fixture_set": "mvp_acceptance_fixture@v1",
                "mock_set": "mvp_mock@v1",
                "clock_source": "fixed_clock_fixture@v1",
                "fixture_version": "v1",
                "mock_version": "v1",
                "assertions": [
                    {
                        "id": f"{stage}-product-not-implemented",
                        "type": "report_schema",
                        "status": assertion_status,
                        "expected": {"product_stage_ready": True},
                        "actual": {"product_stage_ready": False},
                        "diff": {
                            "reason": "Loop report tooling is available, but product implementation has not started."
                        },
                        "leak_detection": {
                            "method": "structured_field_scan",
                            "target": "test_report",
                            "forbidden_field_count": 0,
                            "sensitive_content_count": 0,
                            "matched_paths": [],
                        },
                    }
                ],
                "expected": {"product_stage_ready": True},
                "actual": {"product_stage_ready": False},
                "diff": {"status": "product task DAG remains pending"},
                "node": "static" if stage == "static" else "source",
                "timestamp": utc_now(),
            }
        ],
    }


def build_acceptance_report(root: Path, run_id: str) -> dict[str, Any]:
    return {
        "run_id": run_id,
        "schema_ref": "docs/08_acceptance.md",
        "schema_version": "08_acceptance@codex-stop-v5",
        "gate_status": {gate: "UNKNOWN" for gate in ACC_STOP_GATES},
        "stop_allowed": False,
        "evidence_paths": [],
        "failed_or_unproven_gates": ACC_STOP_GATES,
        "required_next_action": "continue",
        "notes": "Product tasks have not been executed; acceptance cannot pass from loop tooling alone.",
    }


def build_verifier_report(root: Path, run_id: str) -> dict[str, Any]:
    return {
        "run_id": run_id,
        "schema_ref": "docs/11_evidence_and_reports.md#3",
        "schema_version": "v1",
        "task_id": None,
        "verifier_agent": "verifier",
        "status": "blocked",
        "checked_files": [],
        "checks_run": [],
        "scope_result": "in_scope",
        "complexity_result": "acceptable",
        "evidence_result": "missing",
        "findings": [
            {
                "severity": "blocked",
                "message": "No implementer handoff or product task evidence was provided.",
            }
        ],
        "required_next_action": "human_handoff",
    }


def main_stage(stage: str) -> int:
    return run_report_cli(
        description=f"Write RSS Loop {stage} TestReport",
        filename="test-report.json",
        builder=lambda root, run_id: build_product_stage_report(root, run_id, stage),
    )


def main_acceptance() -> int:
    return run_report_cli(
        description="Write RSS Loop acceptance report",
        filename="acceptance-report.json",
        builder=build_acceptance_report,
    )


def main_verifier() -> int:
    return run_report_cli(
        description="Write RSS Loop verifier report",
        filename="verifier-report.json",
        builder=build_verifier_report,
    )
