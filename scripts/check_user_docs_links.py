#!/usr/bin/env python3
"""Relative link checker for User Guide, doc/README.md, and root README.md (PYPOST-1021).

Checks that:
1. Relative file targets exist on disk.
2. Section anchor references (#anchor-name) resolve to headings or explicit HTML anchors.
"""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parents[1]
_DEFAULT_TARGETS = tuple(
    sorted((_REPO_ROOT / "doc" / "user").glob("*.md"))
    + [
        _REPO_ROOT / "doc" / "README.md",
        _REPO_ROOT / "README.md",
        _REPO_ROOT / "examples" / "README.md",
    ]
)

_LINK_PATTERN = re.compile(r"\[([^\]]*)\]\(([^)\s]+)(?:\s+[\"'][^\"']*[\"'])?\)")
_EXTERNAL_SCHEMES = ("http://", "https://", "mailto:", "conversation:", "file:")


def slugify(text: str) -> str:
    """Convert heading text to GitHub Markdown anchor slug."""
    # Strip markdown links inside heading: [text](url) -> text
    text = re.sub(r"\[([^\]]+)\]\([^\)]+\)", r"\1", text)
    # Strip code backticks, punctuation
    text = re.sub(r"[^\w\s-]", "", text.lower())
    # Replace whitespace/underscores with hyphens
    slug = re.sub(r"[\s_]+", "-", text.strip())
    return slug


def extract_anchors(path: Path) -> set[str]:
    """Extract heading slugs and HTML name/id attributes from a markdown file."""
    text = path.read_text(encoding="utf-8")
    anchors: set[str] = set()
    for line in text.splitlines():
        # Match ATX heading: # Heading
        m = re.match(r"^#+\s+(.*)", line)
        if m:
            heading = m.group(1).strip()
            anchors.add(slugify(heading))
        # Match HTML anchors: <a id="..." name="...">
        for tag_match in re.finditer(r'<[a-zA-Z0-9_-]+\s+[^>]*?(?:id|name)=["\']([^"\']+)["\']', line):
            anchors.add(tag_match.group(1))
    return anchors


def check_file_links(file_path: Path) -> list[str]:
    """Check all relative links in a single markdown file."""
    errors: list[str] = []
    text = file_path.read_text(encoding="utf-8")

    # Cache target anchors
    anchor_cache: dict[Path, set[str]] = {}

    for line_no, line in enumerate(text.splitlines(), start=1):
        for m in _LINK_PATTERN.finditer(line):
            target = m.group(2).strip()
            if target.startswith(_EXTERNAL_SCHEMES):
                continue

            if "#" in target:
                file_part, anchor_part = target.split("#", 1)
            else:
                file_part, anchor_part = target, ""

            if file_part:
                dest_path = (file_path.parent / file_part).resolve()
            else:
                dest_path = file_path.resolve()

            if not dest_path.exists():
                errors.append(
                    f"{file_path}:{line_no}: broken relative link target '{target}' "
                    f"(file not found: {dest_path})"
                )
                continue

            if anchor_part:
                if dest_path not in anchor_cache:
                    anchor_cache[dest_path] = extract_anchors(dest_path)
                valid_anchors = anchor_cache[dest_path]
                if anchor_part not in valid_anchors:
                    errors.append(
                        f"{file_path}:{line_no}: broken anchor '#{anchor_part}' in '{target}' "
                        f"(valid anchors in {dest_path.name}: {sorted(valid_anchors)})"
                    )

    return errors


def main() -> int:
    parser = argparse.ArgumentParser(description="Check relative markdown links.")
    parser.add_argument(
        "files",
        nargs="*",
        type=Path,
        help="Optional markdown files to check (defaults to doc/user/*.md, doc/README.md, README.md).",
    )
    args = parser.parse_args()

    targets = [p.resolve() for p in args.files] if args.files else _DEFAULT_TARGETS
    all_errors: list[str] = []

    for target in targets:
        if not target.is_file():
            all_errors.append(f"File not found: {target}")
            continue
        all_errors.extend(check_file_links(target))

    if all_errors:
        for err in all_errors:
            sys.stderr.write(f"{err}\n")
        return 1

    print(f"Relative link check OK ({len(targets)} files checked).")
    return 0


if __name__ == "__main__":
    sys.exit(main())
