#!/usr/bin/env python3
"""Inventory dialog modules under pypost/ui/dialogs/ (PYPOST-374)."""
from __future__ import annotations

import argparse
import json
import sys
from dataclasses import dataclass
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
DIALOGS_DIR = REPO_ROOT / "pypost" / "ui" / "dialogs"
AUDIT_REPORT = REPO_ROOT / "ai-tasks" / "PYPOST-374" / "30-dialogs-audit-report.md"
AUDIT_ERA_GROUPED_LOC = 400


@dataclass(frozen=True)
class DialogModule:
    filename: str
    path: str
    total_lines: int
    non_empty_lines: int

    @property
    def stem(self) -> str:
        return Path(self.filename).stem


def discover_dialog_modules() -> list[DialogModule]:
    modules: list[DialogModule] = []
    for path in sorted(DIALOGS_DIR.glob("*.py")):
        if path.name == "__init__.py":
            continue
        lines = path.read_text(encoding="utf-8").splitlines()
        modules.append(
            DialogModule(
                filename=path.name,
                path=f"pypost/ui/dialogs/{path.name}",
                total_lines=len(lines),
                non_empty_lines=sum(1 for line in lines if line.strip()),
            ),
        )
    return modules


def total_loc(modules: list[DialogModule]) -> int:
    return sum(module.total_lines for module in modules)


def check_audit_report_covers(modules: list[DialogModule]) -> list[str]:
    if not AUDIT_REPORT.is_file():
        return [f"Missing audit report: {AUDIT_REPORT.relative_to(REPO_ROOT)}"]
    text = AUDIT_REPORT.read_text(encoding="utf-8")
    missing = [module.filename for module in modules if module.filename not in text]
    if missing:
        return [f"Audit report missing dialog module(s): {', '.join(missing)}"]
    return []


def format_markdown(modules: list[DialogModule]) -> str:
    rows = [
        "| Module | LOC | Non-empty |",
        "| --- | ---: | ---: |",
    ]
    for module in modules:
        rows.append(f"| `{module.path}` | {module.total_lines} | {module.non_empty_lines} |")
    rows.append(f"| **Total** | **{total_loc(modules)}** | |")
    rows.append("")
    rows.append(f"Audit-era grouped estimate (PYPOST-40): ~{AUDIT_ERA_GROUPED_LOC} LOC.")
    return "\n".join(rows)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--json",
        action="store_true",
        help="Print inventory as JSON",
    )
    parser.add_argument(
        "--markdown",
        action="store_true",
        help="Print inventory as markdown table",
    )
    parser.add_argument(
        "--check",
        action="store_true",
        help="Exit 1 if audit report does not list all dialog modules",
    )
    args = parser.parse_args(argv)

    modules = discover_dialog_modules()
    if args.check:
        issues = check_audit_report_covers(modules)
        if issues:
            for issue in issues:
                print(issue, file=sys.stderr)
            return 1
        print(f"OK: {len(modules)} dialog module(s) covered by audit report")
        return 0

    if args.json:
        payload = {
            "modules": [
                {
                    "filename": module.filename,
                    "path": module.path,
                    "total_lines": module.total_lines,
                    "non_empty_lines": module.non_empty_lines,
                }
                for module in modules
            ],
            "total_lines": total_loc(modules),
            "audit_era_grouped_loc": AUDIT_ERA_GROUPED_LOC,
        }
        print(json.dumps(payload, indent=2))
        return 0

    if args.markdown:
        print(format_markdown(modules))
        return 0

    for module in modules:
        print(f"{module.path}\t{module.total_lines}")
    print(f"TOTAL\t{total_loc(modules)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
