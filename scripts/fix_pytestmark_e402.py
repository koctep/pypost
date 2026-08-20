#!/usr/bin/env python3
"""One-shot mechanical fix for PYPOST-1070: relocate module-level ``pytestmark``
assignments to immediately after the last top-level import, eliminating the
flake8 E402 findings this causes across ``tests/*.py``.

Design: see ai-tasks/PYPOST-1070/20-architecture.md ("The mechanical fix
script" section) for the full algorithm rationale (AST-located, line-slice
edited — not ``ast.unparse``, not pure regex).

Usage:
    .venv/bin/python scripts/fix_pytestmark_e402.py --dry-run
    .venv/bin/python scripts/fix_pytestmark_e402.py

``--dry-run`` reports per-file skip/fixed/error without writing any files.
A real (non-dry-run) invocation writes the fixes and then self-verifies by
shelling out to ``flake8 --jobs=1 --select=E402 tests/``, exiting non-zero
(and printing the remaining findings) if the count isn't zero.
"""

from __future__ import annotations

import argparse
import ast
import subprocess
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
TESTS_DIR = REPO_ROOT / "tests"


def get_flagged_files() -> list[Path]:
    """Return the tests/*.py files flake8 currently flags for E402, freshly
    computed (not hardcoded), per the architecture doc's driver-behavior spec.
    """
    result = subprocess.run(
        [sys.executable, "-m", "flake8", "--jobs=1", "--select=E402", "tests/"],
        cwd=REPO_ROOT,
        capture_output=True,
        text=True,
        timeout=60,
    )
    lines = [line for line in result.stdout.splitlines() if line.strip()]
    files = sorted({line.split(":", 1)[0] for line in lines})
    return [REPO_ROOT / f for f in files]


def fix_file(path: Path, dry_run: bool) -> str:
    """Apply the relocation algorithm to a single file.

    Returns a short status string: "fixed", "skip: <reason>", or
    "error: <reason>".
    """
    src = path.read_text(encoding="utf-8")
    lines = src.splitlines(keepends=True)
    try:
        tree = ast.parse(src)
    except SyntaxError as exc:
        return f"error: pre-edit ast.parse failed: {exc}"

    # 1. Locate the single module-level `pytestmark = ...` assignment.
    mark_nodes = [
        node
        for node in tree.body
        if (
            isinstance(node, ast.Assign)
            and len(node.targets) == 1
            and isinstance(node.targets[0], ast.Name)
            and node.targets[0].id == "pytestmark"
        )
    ]
    if not mark_nodes:
        return "skip: no module-level pytestmark assignment found"
    if len(mark_nodes) > 1:
        return "skip: multiple module-level pytestmark assignments found"
    mark_node = mark_nodes[0]

    # 2. Find the last top-level import that currently sits AFTER pytestmark.
    top_level_imports = [n for n in tree.body if isinstance(n, (ast.Import, ast.ImportFrom))]
    if not top_level_imports:
        return "skip: no top-level imports found"

    imports_after = [n for n in top_level_imports if n.lineno > mark_node.lineno]
    if not imports_after:
        return "skip: already E402-clean (no imports after pytestmark)"

    last_import_end = max(n.end_lineno for n in top_level_imports)

    # 2b. Fourth trigger condition: a non-import, non-pytestmark top-level
    # statement sitting between imports. Relocating pytestmark alone cannot
    # fix E402 in this shape (see architecture doc's "Known exception").
    first_import_start = min(n.lineno for n in top_level_imports)
    stray_nodes = [
        n
        for n in tree.body
        if n is not mark_node
        and not isinstance(n, (ast.Import, ast.ImportFrom))
        and first_import_start <= n.lineno <= last_import_end
    ]
    if stray_nodes:
        return "skip: manual review — non-import, non-pytestmark statement between imports"

    # 3. Slice by line number (1-indexed lineno/end_lineno -> 0-indexed list slots).
    mark_lines = lines[mark_node.lineno - 1:mark_node.end_lineno]
    before_mark = lines[: mark_node.lineno - 1]
    between = lines[mark_node.end_lineno:last_import_end]  # imports (+ blanks/comments)
    after_imports = lines[last_import_end:]

    # 4. Trim a single blank line that used to directly follow pytestmark
    # (avoid a double blank at the old removal point); trim leading blanks
    # off after_imports (we insert our own canonical spacing instead).
    if between and between[0].strip() == "":
        between = between[1:]
    while after_imports and after_imports[0].strip() == "":
        after_imports = after_imports[1:]

    # 5. Reassemble: imports first, one blank line, pytestmark, two blank
    # lines, rest of file (matches the dominant already-clean-file shape).
    new_lines = before_mark + between + ["\n"] + mark_lines + ["\n", "\n"] + after_imports
    new_src = "".join(new_lines)

    # 6. Safety check: the rewritten file must still parse before it's accepted.
    try:
        ast.parse(new_src)
    except SyntaxError as exc:
        return f"error: post-edit ast.parse failed: {exc}"

    if not dry_run:
        path.write_text(new_src, encoding="utf-8")
    return "fixed"


def main() -> int:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
        sys.stderr.reconfigure(encoding="utf-8")

    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Report per-file status without writing any files.",
    )
    args = parser.parse_args()

    targets = get_flagged_files()
    print(f"Found {len(targets)} currently-E402-flagged file(s) under tests/.")

    counts: dict[str, int] = {"fixed": 0, "skip": 0, "error": 0}
    for path in targets:
        rel = path.relative_to(REPO_ROOT)
        status = fix_file(path, dry_run=args.dry_run)
        bucket = status.split(":", 1)[0]
        counts[bucket] = counts.get(bucket, 0) + 1
        print(f"{rel}: {status}")

    print(
        f"\nSummary: {counts.get('fixed', 0)} fixed, {counts.get('skip', 0)} skipped, "
        f"{counts.get('error', 0)} errors "
        f"({'dry run, nothing written' if args.dry_run else 'files written'})."
    )

    if args.dry_run:
        return 0

    # Built-in self-verification: re-run flake8 --select=E402 over tests/.
    result = subprocess.run(
        [sys.executable, "-m", "flake8", "--jobs=1", "--select=E402", "tests/"],
        cwd=REPO_ROOT,
        capture_output=True,
        text=True,
        timeout=60,
    )
    remaining = [line for line in result.stdout.splitlines() if line.strip()]
    if result.returncode == 0 and not remaining:
        print("\nVerification: flake8 --jobs=1 --select=E402 tests/ reports zero findings.")
        return 0

    print(
        f"\nVerification FAILED: {len(remaining)} E402 finding(s) remain:",
        file=sys.stderr,
    )
    for line in remaining:
        print(line, file=sys.stderr)
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
