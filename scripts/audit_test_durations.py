#!/usr/bin/env python3
"""Audit pytest durations against timeout markers for CI (PYPOST-573)."""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

_SCRIPTS_DIR = Path(__file__).resolve().parent
if str(_SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(_SCRIPTS_DIR))

from parse_timeout_audit import (  # noqa: E402
    build_entries,
    load_timeout_map,
    parse_durations,
    resolve_timeout,
)

REPO_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_TESTS_DIR = REPO_ROOT / "tests"

WARN_UTILIZATION = 80.0
FAIL_UTILIZATION = 95.0


def _github_annotation(level: str, nodeid: str, message: str) -> str:
    file_part, _, test_part = nodeid.partition("::")
    line = f"file={file_part}"
    if test_part:
        line = f"{line},title={test_part}"
    return f"::{level} {line}::{message}"


def audit_durations(
    durations_file: Path,
    tests_dir: Path,
    warn_pct: float = WARN_UTILIZATION,
    fail_pct: float = FAIL_UTILIZATION,
) -> tuple[list[str], list[str], int]:
    """Return warnings, failures, exit code."""
    lines = durations_file.read_text(encoding="utf-8", errors="replace").splitlines()
    all_durations = parse_durations(lines)
    timeout_map = load_timeout_map(tests_dir)

    warnings: list[str] = []
    failures: list[str] = []

    for nodeid, duration in sorted(all_durations.items(), key=lambda x: -x[1]):
        timeout_s, _ = resolve_timeout(nodeid, timeout_map)
        if timeout_s <= 0:
            continue
        utilization = (duration / timeout_s) * 100.0
        msg = (
            f"{nodeid}: {duration:.2f}s / {timeout_s}s timeout "
            f"({utilization:.1f}% utilization)"
        )
        if utilization >= fail_pct:
            failures.append(msg)
            print(
                _github_annotation("error", nodeid, msg),
                flush=True,
            )
        elif utilization >= warn_pct:
            warnings.append(msg)
            print(
                _github_annotation("warning", nodeid, msg),
                flush=True,
            )

    return warnings, failures, 1 if failures else 0


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "durations_file",
        type=Path,
        help="Pytest output containing --durations section",
    )
    parser.add_argument(
        "--tests-dir",
        type=Path,
        default=DEFAULT_TESTS_DIR,
        help="Directory containing test_*.py files",
    )
    parser.add_argument(
        "--warn-utilization",
        type=float,
        default=WARN_UTILIZATION,
        help=f"Emit warning at this %% of timeout (default: {WARN_UTILIZATION})",
    )
    parser.add_argument(
        "--fail-utilization",
        type=float,
        default=FAIL_UTILIZATION,
        help=f"Fail at this %% of timeout (default: {FAIL_UTILIZATION})",
    )
    args = parser.parse_args()

    warnings, failures, exit_code = audit_durations(
        args.durations_file,
        args.tests_dir,
        warn_pct=args.warn_utilization,
        fail_pct=args.fail_utilization,
    )

    print(
        f"Duration audit: {len(warnings)} warning(s), {len(failures)} failure(s)",
        flush=True,
    )
    for line in warnings:
        print(f"WARN: {line}", flush=True)
    for line in failures:
        print(f"FAIL: {line}", flush=True)

    if failures:
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
