#!/usr/bin/env python3
"""Extract corrected Jira summaries from ai-tasks debt artifacts (PYPOST-581)."""

from __future__ import annotations

import argparse
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
AI_TASKS = ROOT / "ai-tasks"
JIRA_KEY = re.compile(r"\[PYPOST-(\d+)\]\(https://pypost\.atlassian\.net/browse/PYPOST-\d+\)")
MAX_SUMMARY = 255


def _parent_key(path: Path) -> str:
    return path.parent.name


def _clean_description(raw: str) -> str:
    text = raw.strip()
    text = re.sub(r"^[-|*\s]+", "", text)
    text = re.sub(r"\s*\|\s*Jira:\s*$", "", text, flags=re.I)
    text = re.sub(r"\s*—\s*Jira:\s*$", "", text, flags=re.I)
    text = text.replace("\\|", "|")
    text = re.sub(r"\s+", " ", text).strip(" -|")
    text = re.sub(r"\s*\(non-blocker[^)]*\)\s*$", "", text, flags=re.I)
    return text


def _description_from_line(line: str, match: re.Match[str]) -> str:
    before = line[: match.start()].strip()
    if "|" in before:
        cells = [c.strip() for c in before.split("|")]
        cells = [c for c in cells if c and c != "—"]
        for cell in reversed(cells):
            if cell.lower() in {"low", "medium", "high", "info"}:
                continue
            if re.match(r"^TD-\d+", cell):
                continue
            if len(cell) >= 8:
                return _clean_description(cell)
    if "—" in before:
        parts = before.split("—")
        candidate = _clean_description(parts[0])
        if len(candidate) >= 10:
            return candidate
    if " - " in before:
        return _clean_description(before.split(" - ", 1)[-1])
    return _clean_description(before)


def _description_from_context(lines: list[str], line_idx: int, match: re.Match[str]) -> str:
    direct = _description_from_line(lines[line_idx], match)
    if len(direct) >= 12 and not direct.lower().startswith("jira:"):
        return direct
    if line_idx > 0:
        prev = lines[line_idx - 1].strip()
        if prev.startswith("- ") and "Jira:" not in prev:
            return _clean_description(prev[2:])
    return direct or "Technical debt follow-up"


def _build_summary(parent: str, description: str) -> str:
    prefix = f"[{parent}] "
    body = description
    if body.lower().startswith(prefix.lower().strip()):
        body = body[len(prefix) :].strip()
    summary = f"{prefix}{body}"
    if len(summary) > MAX_SUMMARY:
        summary = summary[: MAX_SUMMARY - 3].rstrip() + "..."
    return summary


def collect_summaries() -> dict[str, str]:
    fixes: dict[str, str] = {}
    for path in sorted(AI_TASKS.rglob("60-tech-debt.md")):
        parent = _parent_key(path)
        lines = path.read_text(encoding="utf-8").splitlines()
        for i, line in enumerate(lines):
            for match in JIRA_KEY.finditer(line):
                jira_num = int(match.group(1))
                key = f"PYPOST-{jira_num}"
                description = _description_from_context(lines, i, match)
                summary = _build_summary(parent, description)
                if key not in fixes or len(summary) > len(fixes[key]):
                    fixes[key] = summary
    return fixes


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--output",
        type=Path,
        default=ROOT / "scripts" / "debt_summary_fixes.json",
        help="Write key -> summary JSON",
    )
    parser.add_argument(
        "--keys",
        nargs="*",
        help="Only emit these issue keys (e.g. PYPOST-581)",
    )
    args = parser.parse_args()
    fixes = collect_summaries()
    if args.keys:
        fixes = {k: v for k, v in fixes.items() if k in args.keys}
    args.output.write_text(json.dumps(fixes, indent=2, sort_keys=True), encoding="utf-8")
    print(f"Wrote {len(fixes)} summaries to {args.output.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
