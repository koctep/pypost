"""PYPOST-1021: User Guide and documentation relative link contract."""

from __future__ import annotations

from pathlib import Path

import pytest

from scripts.check_user_docs_links import check_file_links

pytestmark = pytest.mark.timeout(10)

_REPO_ROOT = Path(__file__).resolve().parents[1]
_USER_DOCS = tuple(sorted((_REPO_ROOT / "doc" / "user").glob("*.md")))
_ROOT_DOC_README = _REPO_ROOT / "doc" / "README.md"
_ROOT_README = _REPO_ROOT / "README.md"
_ALL_TARGETS = _USER_DOCS + (_ROOT_DOC_README, _ROOT_README)


def test_documentation_files_exist() -> None:
    """User guide files and READMEs must exist."""
    assert len(_USER_DOCS) >= 13
    assert _ROOT_DOC_README.is_file()
    assert _ROOT_README.is_file()


@pytest.mark.parametrize("target", _ALL_TARGETS, ids=lambda p: str(p.relative_to(_REPO_ROOT)))
def test_documentation_relative_links_resolve(target: Path) -> None:
    """Every relative file link and section anchor in docs must resolve to an existing target."""
    errors = check_file_links(target)
    assert not errors, f"Broken relative links in {target}:\n" + "\n".join(errors)


def test_link_checker_detects_broken_links_and_anchors(tmp_path: Path) -> None:
    """Checker must catch missing target files and invalid anchor references."""
    target_md = tmp_path / "target.md"
    target_md.write_text("# Target Heading\n\nContent here.\n", encoding="utf-8")

    source_md = tmp_path / "source.md"
    source_md.write_text(
        "[Valid Link](target.md#target-heading)\n"
        "[Broken File](nonexistent.md)\n"
        "[Broken Anchor](target.md#nonexistent-heading)\n"
        "[Broken Self Anchor](#nonexistent-local-heading)\n",
        encoding="utf-8",
    )

    errors = check_file_links(source_md)
    assert len(errors) == 3
    assert any("nonexistent.md" in e for e in errors)
    assert any("#nonexistent-heading" in e for e in errors)
    assert any("#nonexistent-local-heading" in e for e in errors)
