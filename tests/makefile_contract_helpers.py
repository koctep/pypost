"""Shared parsers for Makefile contract tests (PYPOST-937)."""

from __future__ import annotations


def makefile_target_help_comment(makefile_text: str, target: str) -> str:
    """Return the ## help description for a make target line."""
    prefix = f"{target}:"
    for line in makefile_text.splitlines():
        if line.startswith(prefix) and "##" in line:
            return line.split("##", 1)[1].strip()
    raise AssertionError(f"Makefile missing {target} ## help annotation")


def makefile_target_recipe_body(makefile_text: str, target: str) -> str:
    """Return recipe lines under target until the next target."""
    lines = makefile_text.splitlines()
    collecting = False
    body: list[str] = []
    prefix = f"{target}:"
    for line in lines:
        if line.startswith(prefix):
            collecting = True
            continue
        if collecting:
            if line and not line[0].isspace() and not line.startswith("\t"):
                break
            body.append(line)
    assert body, f"Makefile {target} has an empty recipe body"
    return "\n".join(body)
