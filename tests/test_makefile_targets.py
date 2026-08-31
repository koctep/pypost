"""Integration tests for Makefile target execution and exit behavior.

Covers PYPOST-274, PYPOST-791, PYPOST-861, PYPOST-906.
"""

from __future__ import annotations

import subprocess
from pathlib import Path

import pytest

from tests.makefile_test_helpers import _run_make, make_workspace

pytestmark = pytest.mark.timeout(60)


class TestExitBehavior:
    def test_clean_exits_zero_on_empty_tree(self, make_workspace: Path) -> None:
        result = _run_make(make_workspace, "clean")
        assert result.returncode == 0, result.stderr

    def test_unknown_target_exits_nonzero(self, make_workspace: Path) -> None:
        result = _run_make(make_workspace, "not-a-real-target")
        assert result.returncode != 0

    def test_lint_succeeds_from_bare_venv_via_venv_test(
        self,
        make_workspace: Path,
    ) -> None:
        """PYPOST-906: make lint auto-installs [dev] so bare venv is enough."""
        venv_result = _run_make(make_workspace, "venv")
        assert venv_result.returncode == 0, venv_result.stderr
        lint_result = _run_make(make_workspace, "lint")
        assert lint_result.returncode == 0, lint_result.stderr + lint_result.stdout


class TestTargetExecution:
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

    def test_make_test_excludes_slow_marker(self, make_workspace: Path) -> None:
        slow_test = make_workspace / "tests" / "test_slow_fail.py"
        slow_test.write_text(
            "import pytest\n\npytestmark = pytest.mark.timeout(10)\n\n"
            "@pytest.mark.slow\n"
            "def test_would_fail_if_run() -> None:\n"
            "    assert False\n",
            encoding="utf-8",
        )
        install_result = _run_make(make_workspace, "install")
        assert install_result.returncode == 0, install_result.stderr
        test_result = _run_make(make_workspace, "test")
        assert test_result.returncode == 0, test_result.stderr

    def test_make_test_agent_e2e_selects_agent_e2e_marker(
        self,
        make_workspace: Path,
    ) -> None:
        """PYPOST-861 / PYPOST-854: default recipe selects agent_e2e only."""
        pyproject = make_workspace / "pyproject.toml"
        pyproject.write_text(
            pyproject.read_text(encoding="utf-8")
            + "\n[tool.pytest.ini_options]\n"
            "markers = [\n"
            '    "slow: slow tests",\n'
            '    "agent_e2e: agent UI e2e / env pack",\n'
            "]\n",
            encoding="utf-8",
        )
        unmarked = make_workspace / "tests" / "test_unmarked_fail.py"
        unmarked.write_text(
            "import pytest\n\npytestmark = pytest.mark.timeout(10)\n\n"
            "def test_would_fail_if_run() -> None:\n"
            "    assert False\n",
            encoding="utf-8",
        )
        marked = make_workspace / "tests" / "test_agent_marked.py"
        marked.write_text(
            "import pytest\n\n"
            "pytestmark = [pytest.mark.timeout(10), pytest.mark.agent_e2e]\n\n"
            "def test_agent_marked_ok() -> None:\n"
            "    assert True\n",
            encoding="utf-8",
        )
        install_result = _run_make(make_workspace, "install")
        assert install_result.returncode == 0, install_result.stderr
        # Empty PYTEST_ARGS → use default -m "agent_e2e and not slow"
        result = _run_make(make_workspace, "test-agent-e2e", pytest_args="")
        assert result.returncode == 0, result.stderr + result.stdout

    def test_install_succeeds_with_minimal_pyproject(self, make_workspace: Path) -> None:
        result = _run_make(make_workspace, "install")
        assert result.returncode == 0, result.stderr

    def test_test_succeeds_from_bare_venv_via_venv_test(
        self,
        make_workspace: Path,
    ) -> None:
        """PYPOST-872: make test auto-installs [dev] so bare venv is enough."""
        venv_result = _run_make(make_workspace, "venv")
        assert venv_result.returncode == 0, venv_result.stderr
        test_result = _run_make(make_workspace, "test")
        assert test_result.returncode == 0, test_result.stderr + test_result.stdout

    def test_test_succeeds_after_install(self, make_workspace: Path) -> None:
        install_result = _run_make(make_workspace, "install")
        assert install_result.returncode == 0, install_result.stderr
        test_result = _run_make(make_workspace, "test")
        assert test_result.returncode == 0, test_result.stderr

    def test_pytest_args_narrows_test_run(self, make_workspace: Path) -> None:
        """PYPOST-791: PYTEST_ARGS must be forwarded to pytest (not silently ignored)."""
        failing = make_workspace / "tests" / "test_failing.py"
        failing.write_text(
            "import pytest\n\npytestmark = pytest.mark.timeout(10)\n\n"
            "def test_always_fails() -> None:\n"
            "    assert False\n",
            encoding="utf-8",
        )
        install_result = _run_make(make_workspace, "install")
        assert install_result.returncode == 0, install_result.stderr
        narrow = _run_make(
            make_workspace,
            "test",
            pytest_args="tests/test_noop.py -q",
        )
        assert narrow.returncode == 0, narrow.stderr + narrow.stdout

    def test_lint_succeeds_after_install(self, make_workspace: Path) -> None:
        install_result = _run_make(make_workspace, "install")
        assert install_result.returncode == 0, install_result.stderr
        lint_result = _run_make(make_workspace, "lint")
        assert lint_result.returncode == 0, lint_result.stderr
