#!/usr/bin/env python3
"""Markdown linter for User Guide docs and doc/README.md (PYPOST-1020).

Enforces:
- Line length <= 100 characters (excluding code blocks and table rows where wrapping breaks structure).
- No trailing whitespace.
- ATX-style headers (# Heading) with required space after '#' and no Setext underlines.
- List bullet consistency (uses '-' for bullet lists).
"""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parents[1]
_DEFAULT_TARGETS = tuple(
    sorted((_REPO_ROOT / "doc" / "user").glob("*.md"))
    + [_REPO_ROOT / "doc" / "README.md"]
)

_ATX_HEADER_NO_SPACE = re.compile(r"^#+[^ \t\n#]")
_SETEXT_UNDERLINE = re.compile(r"^[=\-]{3,}\s*$")
_UNORDERED_LIST_ASTERISK = re.compile(r"^(\s*)\*\s+")
_UNORDERED_LIST_PLUS = re.compile(r"^(\s*)\+\s+")


def lint_markdown_file(path: Path) -> list[str]:
    """Lint a markdown file and return a list of error strings."""
    errors: list[str] = []
    text = path.read_text(encoding="utf-8")
    lines = text.splitlines()
    in_code_block = False

    for line_no, line in enumerate(lines, start=1):
        # Code fence tracking
        stripped = line.strip()
        if stripped.startswith("```") or stripped.startswith("~~~"):
            in_code_block = not in_code_block

        # Trailing whitespace check (applies everywhere)
        if line.endswith(" ") or line.endswith("\t"):
            errors.append(f"{path}:{line_no}: trailing whitespace")

        if in_code_block:
            continue

        # Line length check (<= 100)
        if len(line) > 100:
            errors.append(
                f"{path}:{line_no}: line length {len(line)} exceeds 100 characters"
            )

        # ATX header checks
        if _ATX_HEADER_NO_SPACE.match(line):
            errors.append(
                f"{path}:{line_no}: invalid header (missing space after '#' in ATX header)"
            )
        if _SETEXT_UNDERLINE.match(line) and line_no > 1 and lines[line_no - 2].strip():
            errors.append(
                f"{path}:{line_no}: Setext header style forbidden; use ATX headers (# ...)"
            )

        # Bullet list consistency check (enforce '-' in doc/user/ and doc/README.md)
        if _UNORDERED_LIST_ASTERISK.match(line) or _UNORDERED_LIST_PLUS.match(line):
            errors.append(
                f"{path}:{line_no}: inconsistent bullet marker; use '-' for unordered list items"
            )

    return errors


def main() -> int:
    parser = argparse.ArgumentParser(description="Lint User Guide Markdown files.")
    parser.add_argument(
        "files",
        nargs="*",
        type=Path,
        help="Optional markdown files to lint (defaults to doc/user/*.md and doc/README.md).",
    )
    args = parser.parse_args()

    targets = [p.resolve() for p in args.files] if args.files else _DEFAULT_TARGETS
    all_errors: list[str] = []

    for target in targets:
        if not target.is_file():
            all_errors.append(f"File not found: {target}")
            continue
        all_errors.extend(lint_markdown_file(target))

    if all_errors:
        for error in all_errors:
            sys.stderr.write(f"{error}\n")
        return 1

    print(f"Markdown lint OK ({len(targets)} files checked).")
    return 0


if __name__ == "__main__":
    sys.exit(main())
