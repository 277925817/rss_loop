from __future__ import annotations

from .budget import build_budget_report
from .common import run_report_cli


def main() -> int:
    return run_report_cli(
        description="Write RSS Loop budget report",
        filename="budget-report.json",
        builder=build_budget_report,
    )


if __name__ == "__main__":
    raise SystemExit(main())
