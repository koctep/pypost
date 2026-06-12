#!/usr/bin/env python3
"""Normalize follow-up tables in ai-tasks debt markdown (PYPOST-582)."""

from __future__ import annotations

import argparse
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
AI_TASKS = ROOT / "ai-tasks"
JIRA_LINK = re.compile(
    r"\[PYPOST-(\d+)\]\(https://pypost\.atlassian\.net/browse/PYPOST-\d+\)",
)
EXTRA_JIRA_COL = re.compile(
    r"\|\s*PYPOST-\d+\s*\|\s*Jira:\s*(\[PYPOST-\d+\]\([^)]+\))",
)
EM_DASH_JIRA = re.compile(
    r"^\|\s*(\w+)\s*\|\s*—\s*\|\s*(.+?)\s*\|\s*Jira:\s*(\[PYPOST-\d+\]\([^)]+\))\s*\|?\s*$",
)
TRAILING_JIRA = re.compile(
    r"\|\s*Jira:\s*(\[PYPOST-\d+\]\([^)]+\))",
)


def _fix_table_line(line: str, header: str | None) -> str:
    if "| Jira: [PYPOST-" not in line and "Jira: [PYPOST-" not in line:
        return line
    m = EXTRA_JIRA_COL.search(line)
    if m:
        return EXTRA_JIRA_COL.sub(f"| {m.group(1)}", line)
    m = EM_DASH_JIRA.match(line.strip())
    if m and header and "| Priority | Jira | Item |" in header:
        priority, item, link = m.group(1), m.group(2), m.group(3)
        return f"| {priority} | {link} | {item} |"
    m = TRAILING_JIRA.search(line)
    if m:
        return TRAILING_JIRA.sub(f"| {m.group(1)}", line)
    return line


def _fix_bullet_line(line: str, continuation: str | None) -> str:
    if "Jira: [PYPOST-" not in line:
        return line
    link_m = JIRA_LINK.search(line)
    if not link_m:
        return line
    link = link_m.group(0)
    if line.strip().startswith("|"):
        return line
    text = line.split("Jira:")[0].strip().rstrip("-—").strip()
    if continuation and len(text) < 15:
        text = continuation.strip().lstrip("- ").rstrip("-—").strip()
    if not text:
        return line
    return f"- {text} — {link}"


def standardize_file(path: Path) -> bool:
    lines = path.read_text(encoding="utf-8").splitlines()
    changed = False
    out: list[str] = []
    header: str | None = None
    for i, line in enumerate(lines):
        if line.startswith("|") and "Priority" in line and "---" not in line:
            header = line
        new_line = _fix_table_line(line, header)
        if new_line != line:
            changed = True
        elif "Jira: [PYPOST-" in line and not line.strip().startswith("|"):
            prev = lines[i - 1] if i > 0 else None
            fixed = _fix_bullet_line(line, prev)
            if fixed != line:
                new_line = fixed
                changed = True
        out.append(new_line)
    if changed:
        path.write_text("\n".join(out) + "\n", encoding="utf-8")
    return changed


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Report files that would change without writing",
    )
    args = parser.parse_args()
    changed_files: list[str] = []
    for path in sorted(AI_TASKS.rglob("60-tech-debt.md")):
        if args.dry_run:
            text = path.read_text(encoding="utf-8")
            if "| Jira: [PYPOST-" in text or re.search(
                r"^\|[^|]+\| — \|", text, re.M
            ):
                changed_files.append(str(path.relative_to(ROOT)))
        elif standardize_file(path):
            changed_files.append(str(path.relative_to(ROOT)))
    print(f"{'Would change' if args.dry_run else 'Changed'} {len(changed_files)} files")
    for rel in changed_files[:20]:
        print(f"  {rel}")
    if len(changed_files) > 20:
        print(f"  … and {len(changed_files) - 20} more")


if __name__ == "__main__":
    main()
