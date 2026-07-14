#!/usr/bin/env python3
"""Run mypy on core/models/ui and enforce a frozen error baseline (PYPOST-734/815)."""
from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
BASELINE_PATH = REPO_ROOT / "mypy-baseline.json"
MYPY_PATHS = ("pypost/core", "pypost/models", "pypost/ui")
_ERROR_RE = re.compile(
    r"^(?P<path>pypost/(?:core|models|ui)/[^:]+):(?P<line>\d+): error: .* \[(?P<code>[^\]]+)\]$",
)


def _run_mypy() -> tuple[int, str]:
    cmd = [
        sys.executable,
        "-m",
        "mypy",
        *MYPY_PATHS,
        "--show-error-codes",
    ]
    completed = subprocess.run(
        cmd,
        cwd=REPO_ROOT,
        capture_output=True,
        text=True,
        check=False,
    )
    output = completed.stdout + completed.stderr
    return completed.returncode, output


def _parse_errors(output: str) -> list[str]:
    errors: list[str] = []
    for line in output.splitlines():
        match = _ERROR_RE.match(line.strip())
        if match is None:
            continue
        errors.append(
            f"{match.group('path')}:{match.group('line')}:{match.group('code')}",
        )
    return sorted(errors)


def _load_baseline() -> list[str]:
    data = json.loads(BASELINE_PATH.read_text(encoding="utf-8"))
    return sorted(data["errors"])


def _write_baseline(errors: list[str]) -> None:
    payload = {
        "scope": list(MYPY_PATHS),
        "error_count": len(errors),
        "errors": errors,
    }
    BASELINE_PATH.write_text(
        json.dumps(payload, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--update-baseline",
        action="store_true",
        help="Rewrite mypy-baseline.json from the current mypy run",
    )
    args = parser.parse_args()

    _returncode, output = _run_mypy()
    current = _parse_errors(output)

    if args.update_baseline:
        _write_baseline(current)
        print(f"Updated {BASELINE_PATH.name}: {len(current)} errors")
        return 0

    if not BASELINE_PATH.is_file():
        print(f"Missing {BASELINE_PATH.name}; run with --update-baseline", file=sys.stderr)
        return 1

    baseline = _load_baseline()
    baseline_set = set(baseline)
    current_set = set(current)

    new_errors = sorted(current_set - baseline_set)
    fixed_errors = sorted(baseline_set - current_set)

    if new_errors or fixed_errors:
        if new_errors:
            print("New mypy errors (not in baseline):", file=sys.stderr)
            for item in new_errors:
                print(f"  + {item}", file=sys.stderr)
        if fixed_errors:
            print("Resolved baseline errors (update baseline):", file=sys.stderr)
            for item in fixed_errors:
                print(f"  - {item}", file=sys.stderr)
        print(
            f"Baseline: {len(baseline)} errors; current: {len(current)} errors",
            file=sys.stderr,
        )
        return 1

    print(f"mypy baseline OK ({len(current)} known errors in {', '.join(MYPY_PATHS)})")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
