"""Integration tests for Makefile test filtering, marker selection, and PYTEST_ARGS.

Covers PYPOST-791, PYPOST-861, PYPOST-1262.
"""

from __future__ import annotations

from pathlib import Path

import pytest

from tests.makefile_test_helpers import _run_make, make_workspace

pytestmark = pytest.mark.timeout(60)


class TestTargetFiltering:
    @pytest.mark.timeout(60)
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

    @pytest.mark.timeout(60)
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

    @pytest.mark.timeout(60)
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

    @pytest.mark.timeout(60)
    def test_lint_succeeds_after_install(self, make_workspace: Path) -> None:
        install_result = _run_make(make_workspace, "install")
        assert install_result.returncode == 0, install_result.stderr
        lint_result = _run_make(make_workspace, "lint")
        assert lint_result.returncode == 0, lint_result.stderr
