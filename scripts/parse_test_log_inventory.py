#!/usr/bin/env python3
"""Parse pytest live-log capture and produce ERROR/WARN inventory (PYPOST-567)."""
from __future__ import annotations

import argparse
import csv
import re
from collections import defaultdict
from pathlib import Path

LOG_RE = re.compile(
    r"^(\d{2}:\d{2}:\d{2}) (ERROR|WARNING)\s+([\w.]+):\s*(.*)$",
)
TEST_RE = re.compile(r"^tests/[\w./]+(?:::|::)[\w.:]+")
OUTCOME_RE = re.compile(r"\b(PASSED|FAILED|ERROR)\s+\[")


def parse_log(lines: list[str]) -> list[dict[str, str]]:
    current_test = "(session)"
    entries: list[dict[str, str]] = []
    for i, raw in enumerate(lines):
        line = raw.strip()
        if TEST_RE.match(line) and not line.startswith("20:"):
            current_test = line.split()[0]
        match = LOG_RE.match(line)
        if match:
            entries.append(
                {
                    "line": str(i + 1),
                    "time": match.group(1),
                    "level": match.group(2),
                    "logger": match.group(3),
                    "message": match.group(4),
                    "test": current_test,
                },
            )
        elif "tests/" in line and OUTCOME_RE.search(line):
            for part in line.split():
                if part.startswith("tests/"):
                    current_test = part
                    break
    return entries


def classify_group(logger: str, message_prefix: str) -> str:
    """Tag inventory group: expected, suspicious, or unknown."""
    expected_loggers = (
        "pypost.core.request_service",
        "pypost.core.qt.worker",
        "pypost.ui.presenters.tabs_presenter",
        "pypost.ui.presenters.collection_tree_actions",
    )
    if logger in expected_loggers:
        return "expected"
    expected_patterns = (
        "RequestWorker unexpected error",
        "request_error category=",
        "request_error error_msg=",
        "collection_item_delete_failed",
        "collection_item_delete_not_found",
        "collection_item_rename_rejected",
        "retryable_",
        "retry_exhausted",
        "request_execution_failed",
        "template_render_fallback",
        "alert_emitted",
        "alert_webhook_failed",
        "alert_manager_stale_handlers",
        "encryption_migration_",
        "load_environments_failed",
        "mcp_operation_failed",
        "encryption_key_source_unsupported",
    )
    if any(p in message_prefix for p in expected_patterns):
        return "expected"
    suspicious_patterns = (
        "key_provider",
        "environment_secrets_codec",
        "storage",
    )
    if logger.endswith(tuple(s.split(".")[-1] for s in suspicious_patterns)):
        return "suspicious"
    if any(p in logger for p in suspicious_patterns):
        return "suspicious"
    return "unknown"


def summarize(entries: list[dict[str, str]]) -> dict[str, object]:
    by_logger: dict[str, list[dict[str, str]]] = defaultdict(list)
    for entry in entries:
        by_logger[entry["logger"]].append(entry)

    groups: dict[str, dict[str, object]] = {}
    for entry in entries:
        prefix = entry["message"][:80]
        key = f"{entry['logger']}|{prefix}"
        if key not in groups:
            groups[key] = {
                "logger": entry["logger"],
                "level": entry["level"],
                "message_prefix": prefix,
                "count": 0,
                "tests": set(),
                "tag": classify_group(entry["logger"], prefix),
            }
        groups[key]["count"] = int(groups[key]["count"]) + 1
        groups[key]["tests"].add(entry["test"])

    return {"by_logger": dict(by_logger), "groups": groups}


def write_markdown(path: Path, entries: list[dict[str, str]], summary: dict) -> None:
    errors = sum(1 for e in entries if e["level"] == "ERROR")
    warnings = sum(1 for e in entries if e["level"] == "WARNING")
    by_logger = summary["by_logger"]
    groups = summary["groups"]

    lines = [
        "# Test log ERROR/WARN inventory",
        "",
        f"- Total entries: **{len(entries)}** (ERROR: {errors}, WARNING: {warnings})",
        "",
        "## Summary by logger",
        "",
        "| Logger | Total | ERROR | WARNING | Suggested tag |",
        "| --- | ---: | ---: | ---: | --- |",
    ]
    for logger, items in sorted(by_logger.items(), key=lambda x: -len(x[1])):
        ec = sum(1 for x in items if x["level"] == "ERROR")
        wc = sum(1 for x in items if x["level"] == "WARNING")
        sample = items[0]["message"][:40]
        tag = classify_group(logger, sample)
        lines.append(f"| `{logger}` | {len(items)} | {ec} | {wc} | {tag} |")

    lines.extend(["", "## Message groups (top 30)", ""])
    sorted_groups = sorted(groups.values(), key=lambda g: -int(g["count"]))[:30]
    for g in sorted_groups:
        tests = ", ".join(sorted(g["tests"]))[:120]
        lines.append(
            f"- **{g['count']}×** `{g['logger']}` [{g['level']}] "
            f"tag={g['tag']}: `{g['message_prefix']}`",
        )
        lines.append(f"  - tests: {tests}")

    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("log_file", type=Path, help="Captured pytest log (tests.txt)")
    parser.add_argument(
        "--markdown",
        type=Path,
        default=None,
        help="Write markdown summary to this path",
    )
    parser.add_argument(
        "--csv",
        type=Path,
        default=None,
        help="Write flat CSV of all entries",
    )
    args = parser.parse_args()
    lines = args.log_file.read_text(encoding="utf-8").splitlines()
    entries = parse_log(lines)
    summary = summarize(entries)

    if args.csv:
        with args.csv.open("w", newline="", encoding="utf-8") as fh:
            writer = csv.DictWriter(
                fh,
                fieldnames=["line", "time", "level", "logger", "message", "test"],
            )
            writer.writeheader()
            writer.writerows(entries)

    if args.markdown:
        write_markdown(args.markdown, entries, summary)

    errors = sum(1 for e in entries if e["level"] == "ERROR")
    warnings = sum(1 for e in entries if e["level"] == "WARNING")
    print(f"Parsed {len(entries)} entries: ERROR={errors}, WARNING={warnings}")


if __name__ == "__main__":
    main()
