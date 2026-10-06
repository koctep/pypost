"""Integration tests for Makefile exit behavior and bare venv transitions.

Covers PYPOST-274, PYPOST-906, PYPOST-1262.
"""

from __future__ import annotations

from pathlib import Path

import pytest

from tests.makefile_test_helpers import _run_make, make_workspace

pytestmark = pytest.mark.timeout(60)


class TestExitBehavior:
    @pytest.mark.timeout(60)
    def test_clean_exits_zero_on_empty_tree(self, make_workspace: Path) -> None:
        result = _run_make(make_workspace, "clean")
        assert result.returncode == 0, result.stderr

    @pytest.mark.timeout(60)
    def test_unknown_target_exits_nonzero(self, make_workspace: Path) -> None:
        result = _run_make(make_workspace, "not-a-real-target")
        assert result.returncode != 0

    @pytest.mark.timeout(60)
    def test_lint_succeeds_from_bare_venv_via_venv_test(
        self,
        make_workspace: Path,
    ) -> None:
        """PYPOST-906: make lint auto-installs [dev] so bare venv is enough."""
        venv_result = _run_make(make_workspace, "venv")
        assert venv_result.returncode == 0, venv_result.stderr
        lint_result = _run_make(make_workspace, "lint")
        assert lint_result.returncode == 0, lint_result.stderr + lint_result.stdout
