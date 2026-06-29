from __future__ import annotations

import argparse
import json
import re
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable


RUN_ID_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._:+=@-]{0,127}$")


def utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def is_valid_run_id(value: str) -> bool:
    if not value or value in {".", ".."}:
        return False
    if "/" in value or "\\" in value:
        return False
    if Path(value).is_absolute():
        return False
    return bool(RUN_ID_RE.fullmatch(value))


def validate_run_id(value: str) -> str:
    if not is_valid_run_id(value):
        raise ValueError("run_id must be a safe single path segment")
    return value


def parse_args(description: str) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=description)
    parser.add_argument("--run-id", required=True, help="Safe run id used under reports/<run_id>/")
    return parser.parse_args()


def report_path(root: Path, run_id: str, filename: str) -> Path:
    validate_run_id(run_id)
    if "/" in filename or "\\" in filename or filename in {"", ".", ".."}:
        raise ValueError("report filename must be a safe single path segment")
    return root / "reports" / run_id / filename


def write_json_report(root: Path, run_id: str, filename: str, payload: dict[str, Any]) -> Path:
    path = report_path(root, run_id, filename)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return path


def read_text(root: Path, relative_path: str) -> str:
    return (root / relative_path).read_text(encoding="utf-8")


def file_exists(root: Path, relative_path: str) -> bool:
    return (root / relative_path).is_file()


def contains_all(text: str, needles: list[str]) -> bool:
    return all(needle in text for needle in needles)


def load_run_log_entries(root: Path) -> list[dict[str, Any]]:
    path = root / "loop-run-log.md"
    if not path.exists():
        return []
    entries: list[dict[str, Any]] = []
    for line in path.read_text(encoding="utf-8").splitlines():
        stripped = line.strip()
        if not stripped.startswith("{"):
            continue
        try:
            entries.append(json.loads(stripped))
        except json.JSONDecodeError:
            continue
    return entries


def state_flag(state_text: str, name: str) -> bool | None:
    match = re.search(rf"\b{re.escape(name)}:\s*(true|false)\b", state_text, re.IGNORECASE)
    if not match:
        return None
    return match.group(1).lower() == "true"


def run_report_cli(
    *,
    description: str,
    filename: str,
    builder: Callable[[Path, str], dict[str, Any]],
) -> int:
    args = parse_args(description)
    root = Path.cwd()
    try:
        run_id = validate_run_id(args.run_id)
        payload = builder(root, run_id)
        path = write_json_report(root, run_id, filename, payload)
    except Exception as exc:  # CLI boundary: report generation failure is non-zero.
        print(f"error: {exc}", file=sys.stderr)
        return 1
    print(path)
    return 0
