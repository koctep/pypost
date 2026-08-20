#!/usr/bin/env python3
"""Run mypy on core/models/ui and enforce a frozen error baseline (PYPOST-734/815/1007).

Baselined errors are identified by ``(path, code, message)`` — deliberately
excluding the source line number, which shifts whenever unrelated code moves
above an error (e.g. an import added/removed/reordered). See
``ai-tasks/PYPOST-1007/20-architecture.md`` for the full design rationale,
including why the diff is a Counter-based multiset difference rather than a
set difference (roughly half of today's baselined errors share a duplicate
``(path, code, message)`` key across different lines).
"""
from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
from collections import Counter
from collections.abc import Sequence
from pathlib import Path
from typing import NamedTuple

REPO_ROOT = Path(__file__).resolve().parents[1]
BASELINE_PATH = REPO_ROOT / "mypy-baseline.json"
MYPY_PATHS = ("pypost/core", "pypost/models", "pypost/ui")
BASELINE_VERSION = 2
_MYPY_PATH_RE = "|".join(
    re.escape(path)
    for path in sorted(MYPY_PATHS, key=lambda path: (-len(path), path))
)
_ERROR_RE = re.compile(
    rf"^(?P<path>(?:{_MYPY_PATH_RE})/[^:]+):(?P<line>\d+): error: "
    r"(?P<message>.*) \[(?P<code>[^\]]+)\]$",
)


class MypyError(NamedTuple):
    """A single error instance parsed from a live mypy run.

    ``line`` is retained for human-facing display only; it is never part of
    the comparison identity (see ``_error_key``).
    """

    path: str
    line: int
    code: str
    message: str


class BaselineEntry(NamedTuple):
    """A single error instance recorded in ``mypy-baseline.json``.

    The baseline never stores a line number — it is not part of an error's
    identity.
    """

    path: str
    code: str
    message: str


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


def _parse_errors(output: str) -> list[MypyError]:
    errors: list[MypyError] = []
    for line in output.splitlines():
        match = _ERROR_RE.match(line.strip())
        if match is None:
            continue
        errors.append(
            MypyError(
                path=match.group("path"),
                line=int(match.group("line")),
                code=match.group("code"),
                message=match.group("message").strip(),
            ),
        )
    return sorted(errors, key=lambda e: (e.path, e.line, e.code))


def _error_key(entry: MypyError | BaselineEntry) -> tuple[str, str, str]:
    """Derive the comparison identity for a parsed/baseline record.

    Deliberately excludes ``line`` — see module docstring.
    """
    return (entry.path, entry.code, entry.message)


def _diff_errors(
    current: Sequence[MypyError],
    baseline: Sequence[BaselineEntry],
) -> tuple[list[tuple[str, str, str]], list[tuple[str, str, str]]]:
    """Pure multiset (Counter) difference of current vs. baseline keys.

    Returns ``(new_keys, fixed_keys)`` as raw ``(path, code, message)``
    key-tuples, one entry per surplus/deficit *instance* — a key with 3 new
    instances appears three times. Uses ``collections.Counter`` subtraction
    (not set difference) so that duplicate-key counts are tracked correctly:
    fixing 1 of 3 duplicate-key instances reports as 1 fixed, not 0 (which a
    set difference would report, since the key is still present on both
    sides). No string formatting happens here — that is entirely `main()`'s
    responsibility.
    """
    current_counts = Counter(_error_key(e) for e in current)
    baseline_counts = Counter(_error_key(e) for e in baseline)

    new_counts = current_counts - baseline_counts
    fixed_counts = baseline_counts - current_counts

    return list(new_counts.elements()), list(fixed_counts.elements())


def _load_baseline() -> list[BaselineEntry]:
    data = json.loads(BASELINE_PATH.read_text(encoding="utf-8"))
    if not isinstance(data, dict) or data.get("version") != BASELINE_VERSION:
        raise ValueError(
            f"{BASELINE_PATH.name} is in a legacy/unrecognized format "
            f'(expected "version": {BASELINE_VERSION}). Regenerate it with '
            "`python scripts/check_mypy_baseline.py --update-baseline`.",
        )
    raw_entries = data.get("errors", [])
    baseline: list[BaselineEntry] = []
    for raw_entry in raw_entries:
        if not isinstance(raw_entry, dict) or not all(
            key in raw_entry for key in ("path", "code", "message")
        ):
            raise ValueError(
                f"{BASELINE_PATH.name} contains a malformed entry: {raw_entry!r}. "
                "Regenerate it with "
                "`python scripts/check_mypy_baseline.py --update-baseline`.",
            )
        baseline.append(
            BaselineEntry(
                path=raw_entry["path"],
                code=raw_entry["code"],
                message=raw_entry["message"],
            ),
        )
    return baseline


def _write_baseline(errors: Sequence[MypyError]) -> None:
    # Duplicate (path, code, message) instances are preserved as repeated
    # objects, never deduplicated: the multiset diff depends on the
    # baseline list's length reflecting the true per-key instance count.
    sorted_errors = sorted(errors, key=lambda e: (e.path, e.code, e.message))
    entries = [
        {"path": e.path, "code": e.code, "message": e.message} for e in sorted_errors
    ]
    payload = {
        "version": BASELINE_VERSION,
        "scope": list(MYPY_PATHS),
        "error_count": len(entries),
        "errors": entries,
    }
    BASELINE_PATH.write_text(
        json.dumps(payload, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )


def _format_new_report(
    new_keys: list[tuple[str, str, str]],
    current: Sequence[MypyError],
) -> list[str]:
    total_by_key = Counter(_error_key(e) for e in current)
    new_count_by_key = Counter(new_keys)
    lines_by_key: dict[tuple[str, str, str], list[int]] = {}
    for error in current:
        lines_by_key.setdefault(_error_key(error), []).append(error.line)

    report: list[str] = ["New mypy errors (not in baseline):"]
    for key in sorted(new_count_by_key):
        path, code, message = key
        lines = sorted(lines_by_key.get(key, []))
        total = total_by_key[key]
        new_count = new_count_by_key[key]
        line_list = ", ".join(str(line) for line in lines)
        suffix = f"  ({new_count} new of {total} total)" if new_count != total else ""
        report.append(f"  + {path}: {message} [{code}]")
        report.append(f"    lines: {line_list}{suffix}")
    return report


def _format_fixed_report(
    fixed_keys: list[tuple[str, str, str]],
    baseline: Sequence[BaselineEntry],
) -> list[str]:
    total_by_key = Counter(_error_key(e) for e in baseline)
    fixed_count_by_key = Counter(fixed_keys)

    report: list[str] = ["Resolved baseline errors (update baseline):"]
    for key in sorted(fixed_count_by_key):
        path, code, message = key
        total = total_by_key[key]
        fixed_count = fixed_count_by_key[key]
        suffix = f"  ({fixed_count} of {total} baselined)" if fixed_count != total else ""
        report.append(f"  - {path}: {message} [{code}]{suffix}")
    return report


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

    try:
        baseline = _load_baseline()
    except ValueError as exc:
        print(str(exc), file=sys.stderr)
        return 1

    new_keys, fixed_keys = _diff_errors(current, baseline)

    if new_keys or fixed_keys:
        if new_keys:
            for line in _format_new_report(new_keys, current):
                print(line, file=sys.stderr)
        if fixed_keys:
            for line in _format_fixed_report(fixed_keys, baseline):
                print(line, file=sys.stderr)
        print(
            f"Baseline: {len(baseline)} errors; current: {len(current)} errors",
            file=sys.stderr,
        )
        return 1

    print(f"mypy baseline OK ({len(current)} known errors in {', '.join(MYPY_PATHS)})")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
