#!/usr/bin/env python3
"""Verify captured pytest log against ERROR allowlist (PYPOST-572)."""
from __future__ import annotations

import argparse
import sys
from dataclasses import dataclass
from pathlib import Path

import yaml

_SCRIPTS_DIR = Path(__file__).resolve().parent
if str(_SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(_SCRIPTS_DIR))

from parse_test_log_inventory import classify_group, parse_log  # noqa: E402

REPO_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_ALLOWLIST = REPO_ROOT / "tests" / "expected_log_allowlist.yaml"


@dataclass(frozen=True)
class AllowlistRule:
    message_prefix: str
    logger: str | None = None


@dataclass(frozen=True)
class Allowlist:
    baseline_error_count: int
    error_margin: int
    rules: tuple[AllowlistRule, ...]


@dataclass(frozen=True)
class VerifyResult:
    error_count: int
    unknown_errors: tuple[dict[str, str], ...]
    count_exceeded: bool
    max_allowed: int


def load_allowlist(path: Path) -> Allowlist:
    data = yaml.safe_load(path.read_text(encoding="utf-8"))
    rules = tuple(
        AllowlistRule(
            message_prefix=str(rule["message_prefix"]),
            logger=rule.get("logger"),
        )
        for rule in data["rules"]
    )
    return Allowlist(
        baseline_error_count=int(data["baseline_error_count"]),
        error_margin=int(data["error_margin"]),
        rules=rules,
    )


def message_matches_prefix(message: str, prefix: str) -> bool:
    return message.startswith(prefix) or prefix in message


def entry_matches_rule(entry: dict[str, str], rule: AllowlistRule) -> bool:
    if rule.logger is not None and entry["logger"] != rule.logger:
        return False
    return message_matches_prefix(entry["message"], rule.message_prefix)


def is_allowed_error(entry: dict[str, str], allowlist: Allowlist) -> bool:
    return any(entry_matches_rule(entry, rule) for rule in allowlist.rules)


def verify_log_lines(lines: list[str], allowlist: Allowlist) -> VerifyResult:
    entries = parse_log(lines)
    errors = [entry for entry in entries if entry["level"] == "ERROR"]
    unknown = tuple(entry for entry in errors if not is_allowed_error(entry, allowlist))
    max_allowed = allowlist.baseline_error_count + allowlist.error_margin
    count_exceeded = len(errors) > max_allowed
    return VerifyResult(
        error_count=len(errors),
        unknown_errors=unknown,
        count_exceeded=count_exceeded,
        max_allowed=max_allowed,
    )


def format_unknown(entry: dict[str, str]) -> str:
    tag = classify_group(entry["logger"], entry["message"][:80])
    return (
        f"  line {entry['line']}: [{tag}] {entry['logger']}: "
        f"{entry['message'][:120]}"
    )


def report(result: VerifyResult) -> list[str]:
    lines: list[str] = []
    lines.append(
        f"ERROR count: {result.error_count} "
        f"(max allowed: {result.max_allowed})",
    )
    if result.count_exceeded:
        lines.append(
            f"FAIL: ERROR count {result.error_count} exceeds "
            f"baseline + margin ({result.max_allowed})",
        )
    if result.unknown_errors:
        lines.append(f"FAIL: {len(result.unknown_errors)} unlisted ERROR line(s):")
        lines.extend(format_unknown(entry) for entry in result.unknown_errors)
    if not result.count_exceeded and not result.unknown_errors:
        lines.append("PASS: all ERROR lines match allowlist and count within margin")
    return lines


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("log_file", type=Path, help="Captured pytest log")
    parser.add_argument(
        "--allowlist",
        type=Path,
        default=DEFAULT_ALLOWLIST,
        help=f"Allowlist YAML (default: {DEFAULT_ALLOWLIST.relative_to(REPO_ROOT)})",
    )
    args = parser.parse_args()
    allowlist = load_allowlist(args.allowlist)
    lines = args.log_file.read_text(encoding="utf-8").splitlines()
    result = verify_log_lines(lines, allowlist)
    for line in report(result):
        print(line)
    if result.count_exceeded or result.unknown_errors:
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
