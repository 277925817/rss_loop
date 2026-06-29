from __future__ import annotations

from .common import run_report_cli
from .docs_drift import build_docs_drift_report


def main() -> int:
    return run_report_cli(
        description="Write RSS Loop docs-drift report",
        filename="docs-drift-report.json",
        builder=build_docs_drift_report,
    )


if __name__ == "__main__":
    raise SystemExit(main())
