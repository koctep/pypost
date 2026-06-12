#!/usr/bin/env python3
"""Build ai-tasks/00-tech-debt-consolidated.md from review and tech-debt artifacts."""

from __future__ import annotations

import re
from collections import defaultdict
from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
AI_TASKS = ROOT / "ai-tasks"
OUTPUT = AI_TASKS / "00-tech-debt-consolidated.md"
DEBT_FILES = frozenset({"60-tech-debt.md", "40-tech-debt.md", "60-review.md"})
JIRA_LINK = re.compile(
    r"\[PYPOST-(\d+)\]\(https://pypost\.atlassian\.net/browse/PYPOST-\d+\)"
)
TITLE_NOISE = re.compile(
    r"^(\*\*)?(\[FIXED\]\s*)?(TD-\d+\s*[—\-]\s*)?"
    r"((HIGH|MEDIUM|LOW|INFO)\s*[—\-]\s*)?",
    re.I,
)


def _clean_title(raw: str) -> str:
    title = TITLE_NOISE.sub("", raw.strip())
    title = re.sub(r"\*+$", "", title).strip(" -*#:")
    title = re.sub(r"\s+", " ", title)
    if len(title) > 100:
        title = title[:97] + "..."
    return title or "Technical debt follow-up"


def _title_for_link(lines: list[str], line_idx: int, link_match: re.Match[str]) -> str:
    line = lines[line_idx]
    before = line[: link_match.start()].strip()
    before = re.sub(r"^[-|*\s]+", "", before)
    before = before.split("—")[0].strip()
    title = _clean_title(before)
    if len(title) >= 10:
        return title
    if line_idx > 0:
        prev = lines[line_idx - 1].strip()
        if prev and not prev.startswith("#"):
            return _clean_title(prev.lstrip("- "))
    return f"Debt item (line {line_idx + 1})"


def collect_entries() -> tuple[dict[int, dict], int, int, list[str]]:
    entries: dict[int, dict] = {}
    files_scanned = 0
    link_count = 0
    no_link_files: list[str] = []

    for path in sorted(AI_TASKS.rglob("*")):
        if path.name not in DEBT_FILES:
            continue
        files_scanned += 1
        rel = str(path.relative_to(AI_TASKS))
        source = path.parent.name
        text = path.read_text(encoding="utf-8")
        lines = text.splitlines()
        file_links = 0

        for i, line in enumerate(lines):
            for m in JIRA_LINK.finditer(line):
                link_count += 1
                file_links += 1
                jira = int(m.group(1))
                title = _title_for_link(lines, i, m)
                if jira not in entries or len(title) > len(entries[jira]["title"]):
                    entries[jira] = {
                        "source": source,
                        "title": title,
                        "file": rel,
                    }

        if file_links == 0:
            no_link_files.append(rel)

    return entries, files_scanned, link_count, no_link_files


def render_markdown(
    entries: dict[int, dict],
    files_scanned: int,
    link_count: int,
    no_link_files: list[str],
) -> str:
    per_source: dict[str, int] = defaultdict(int)
    for entry in entries.values():
        per_source[entry["source"]] += 1

    lines = [
        "# Consolidated Technical Debt Inventory",
        "",
        "Generated for [PYPOST-57](https://pypost.atlassian.net/browse/PYPOST-57) "
        f"on {date.today().isoformat()}.",
        "",
        "Aggregated from `ai-tasks/**/60-review.md`, `ai-tasks/**/40-tech-debt.md`, and",
        "`ai-tasks/**/60-tech-debt.md`. Each row links a source task artifact to its Jira",
        "follow-up issue.",
        "",
        "Regenerate: `python scripts/consolidate_tech_debt.py`",
        "",
        "## Summary",
        "",
        "| Metric | Count |",
        "| --- | ---: |",
        f"| Source files scanned | {files_scanned} |",
        f"| Total Jira link references | {link_count} |",
        f"| Unique linked Jira issues | {len(entries)} |",
        f"| Source tasks with linked debt | {len(per_source)} |",
        f"| Debt files without Jira links | {len(no_link_files)} |",
        "",
        "## Key Source Tasks",
        "",
        "| Source | Linked items | Primary file |",
        "| --- | ---: | --- |",
    ]
    key_files = {
        "PYPOST-41": "PYPOST-41/60-review.md",
        "PYPOST-43": "PYPOST-43/60-review.md",
        "PYPOST-44": "PYPOST-44/60-review.md",
        "PYPOST-45": "PYPOST-45/60-review.md",
        "PYPOST-52": "PYPOST-52/60-review.md",
    }
    for src, fname in key_files.items():
        lines.append(f"| {src} | {per_source.get(src, 0)} | `{fname}` |")

    lines += ["", "## Inventory by Source Task", ""]
    for src in sorted(per_source.keys(), key=lambda s: int(s.split("-")[1])):
        items = sorted(
            [(k, v) for k, v in entries.items() if v["source"] == src],
            key=lambda x: x[0],
        )
        lines.append(f"### {src} ({len(items)} items)")
        lines.append("")
        lines.append("| Jira | Summary (from artifact) | File |")
        lines.append("| --- | --- | --- |")
        for jira, entry in items:
            title = entry["title"].replace("|", "\\|")
            lines.append(
                f"| [PYPOST-{jira}](https://pypost.atlassian.net/browse/PYPOST-{jira}) "
                f"| {title} | `{entry['file']}` |"
            )
        lines.append("")

    if no_link_files:
        lines += ["## Debt Files Without Jira Links", ""]
        lines.append(
            "These files document debt but contain no `PYPOST-*` Jira links yet "
            f"({len(no_link_files)} files):"
        )
        lines.append("")
        for rel in no_link_files[:40]:
            lines.append(f"- `{rel}`")
        if len(no_link_files) > 40:
            lines.append(f"- … and {len(no_link_files) - 40} more")
        lines.append("")

    lines += [
        "## Remediation Notes",
        "",
        "- Markdown/Jira hygiene: see [tech-debt-diff.md](../tech-debt-diff.md).",
        "- Sprint 502 executes linked backlog items (UI polish & cleanup).",
        "- Re-run this script when new `60-tech-debt.md` / `60-review.md` artifacts land.",
        "",
    ]
    return "\n".join(lines)


def main() -> None:
    import argparse
    import json

    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--json",
        type=Path,
        metavar="PATH",
        help="Write unique Jira entries as JSON (key PYPOST-N -> title)",
    )
    args = parser.parse_args()

    entries, files_scanned, link_count, no_link_files = collect_entries()
    if args.json:
        payload = {
            f"PYPOST-{jira}": entry["title"]
            for jira, entry in sorted(entries.items())
        }
        args.json.write_text(json.dumps(payload, indent=2, sort_keys=True), encoding="utf-8")
        print(f"Wrote {args.json.relative_to(ROOT)} ({len(payload)} issues)")
        return

    OUTPUT.write_text(
        render_markdown(entries, files_scanned, link_count, no_link_files),
        encoding="utf-8",
    )
    print(f"Wrote {OUTPUT.relative_to(ROOT)}")
    print(f"  files={files_scanned} links={link_count} unique_jira={len(entries)}")


if __name__ == "__main__":
    main()
