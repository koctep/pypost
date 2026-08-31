"""Slow install smoke test verifying full packaging dependencies (PYPOST-559, PYPOST-963)."""

from __future__ import annotations

from pathlib import Path

import pytest

from tests.makefile_test_helpers import (
    _assert_post_install_sanity,
    _run_make,
    make_workspace_full_deps,
)

pytestmark = pytest.mark.timeout(180)


@pytest.mark.slow
class TestSlowInstallSmoke:
    def test_install_succeeds_with_project_pyproject(
        self,
        make_workspace_full_deps: Path,
    ) -> None:
        result = _run_make(
            make_workspace_full_deps,
            "install",
            timeout=170,
        )
        assert result.returncode == 0, result.stderr
        bin_python = make_workspace_full_deps / ".venv" / "bin" / "python"
        _assert_post_install_sanity(bin_python)
