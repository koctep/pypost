"""Integration tests for Makefile target execution (install and test targets).

Covers PYPOST-274, PYPOST-872, PYPOST-1262.
"""

from __future__ import annotations

import subprocess
from pathlib import Path

import pytest

from tests.makefile_test_helpers import _run_make, make_workspace

pytestmark = pytest.mark.timeout(60)


class TestTargetInstallTest:
    @pytest.mark.timeout(60)
    def test_venv_test_installs_pytest_and_flake8(self, make_workspace: Path) -> None:
        venv_result = _run_make(make_workspace, "venv")
        assert venv_result.returncode == 0, venv_result.stderr
        venv_test_result = _run_make(make_workspace, "venv-test")
        assert venv_test_result.returncode == 0, venv_test_result.stderr
        bin_python = make_workspace / ".venv" / "bin" / "python"
        proc = subprocess.run(
            [str(bin_python), "-c", "import pytest, flake8"],
            capture_output=True,
            text=True,
            timeout=30,
            check=False,
        )
        assert proc.returncode == 0, proc.stderr

    @pytest.mark.timeout(60)
    def test_install_succeeds_with_minimal_pyproject(
        self,
        make_workspace: Path,
    ) -> None:
        result = _run_make(make_workspace, "install")
        assert result.returncode == 0, result.stderr

    @pytest.mark.timeout(60)
    def test_test_succeeds_from_bare_venv_via_venv_test(
        self,
        make_workspace: Path,
    ) -> None:
        """PYPOST-872: make test auto-installs [dev] so bare venv is enough."""
        venv_result = _run_make(make_workspace, "venv")
        assert venv_result.returncode == 0, venv_result.stderr
        test_result = _run_make(make_workspace, "test")
        assert test_result.returncode == 0, test_result.stderr + test_result.stdout

    @pytest.mark.timeout(60)
    def test_test_succeeds_after_install(self, make_workspace: Path) -> None:
        install_result = _run_make(make_workspace, "install")
        assert install_result.returncode == 0, install_result.stderr
        test_result = _run_make(make_workspace, "test")
        assert test_result.returncode == 0, test_result.stderr
