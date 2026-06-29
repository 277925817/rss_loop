from __future__ import annotations

from .common import run_report_cli
from .readiness import build_loop_readiness_report


def main() -> int:
    return run_report_cli(
        description="Write RSS Loop loop-readiness report",
        filename="loop-readiness-report.json",
        builder=build_loop_readiness_report,
    )


if __name__ == "__main__":
    raise SystemExit(main())
