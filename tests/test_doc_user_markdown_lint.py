"""PYPOST-1020: User Guide Markdown formatting and style contract."""

from __future__ import annotations

from pathlib import Path

import pytest

from scripts.lint_user_docs import lint_markdown_file

pytestmark = pytest.mark.timeout(10)

_REPO_ROOT = Path(__file__).resolve().parents[1]
_USER_DOCS = tuple(sorted((_REPO_ROOT / "doc" / "user").glob("*.md")))
_ROOT_DOC_README = _REPO_ROOT / "doc" / "README.md"
_ALL_TARGETS = _USER_DOCS + (_ROOT_DOC_README,)


def test_user_guide_markdown_files_exist() -> None:
    """At least twelve user guide topic pages, index, and doc/README must exist."""
    assert len(_USER_DOCS) >= 13, f"Expected >=13 user doc files; found {len(_USER_DOCS)}"
    assert _ROOT_DOC_README.is_file(), "doc/README.md must exist"


@pytest.mark.parametrize("target", _ALL_TARGETS, ids=lambda p: str(p.relative_to(_REPO_ROOT)))
def test_user_guide_markdown_adheres_to_style_contract(target: Path) -> None:
    """Markdown files must have line length <=100, no trailing whitespace, ATX headers, and '-' bullets."""
    errors = lint_markdown_file(target)
    assert not errors, f"Markdown style violations in {target}:\n" + "\n".join(errors)


def test_linter_detects_style_violations(tmp_path: Path) -> None:
    """Linter helper must catch length, trailing whitespace, invalid headers, and bad bullets."""
    bad_md = tmp_path / "bad.md"
    bad_md.write_text(
        "#BadHeader\n"
        "Line with trailing whitespace.   \n"
        f"{'x' * 105}\n"
        "* Asterisk bullet item\n"
        "+ Plus bullet item\n"
        "Setext Header\n"
        "---\n",
        encoding="utf-8",
    )
    errors = lint_markdown_file(bad_md)
    assert len(errors) >= 5
    assert any("missing space after '#'" in e for e in errors)
    assert any("trailing whitespace" in e for e in errors)
    assert any("exceeds 100 characters" in e for e in errors)
    assert any("inconsistent bullet marker" in e for e in errors)
    assert any("Setext header style forbidden" in e for e in errors)
