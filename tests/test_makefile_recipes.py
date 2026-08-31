"""Integration tests for Makefile recipe contracts, dependency chains, and help target."""

from __future__ import annotations

from pathlib import Path

import pytest

from tests.makefile_contract_helpers import (
    makefile_target_help_comment,
    makefile_target_recipe_body,
)
from tests.makefile_test_helpers import (
    MAKEFILE,
    MARKER_REL,
    REQUIREMENTS,
    REQUIREMENTS_DEV,
    REQUIREMENTS_DEV_IN,
    REQUIREMENTS_IN,
    REQUIREMENTS_OTEL,
    REQUIREMENTS_OTEL_IN,
    VENV_OTEL_STAMP_REL,
    VENV_TEST_STAMP_REL,
    _prerequisites,
    _run_make,
    make_workspace,
)

pytestmark = pytest.mark.timeout(30)

_TEST_AGENT_E2E = "test-agent-e2e"
_TEST = "test"


class TestDependencyChain:
    def test_install_depends_on_marker_only(self, make_workspace: Path) -> None:
        prereqs = _prerequisites(make_workspace, "install")
        assert MARKER_REL in prereqs
        assert "venv-test" not in prereqs
        assert "venv-otel" not in prereqs

    def test_test_depends_on_venv_test_venv_otel_and_marker(
        self,
        make_workspace: Path,
    ) -> None:
        """PYPOST-872: pytest targets must pull [dev] via venv-test."""
        prereqs = _prerequisites(make_workspace, "test")
        assert "venv-test" in prereqs
        assert "venv-otel" in prereqs
        assert MARKER_REL in prereqs

    def test_test_cov_depends_on_venv_test_venv_otel_and_marker(
        self,
        make_workspace: Path,
    ) -> None:
        prereqs = _prerequisites(make_workspace, "test-cov")
        assert "venv-test" in prereqs
        assert "venv-otel" in prereqs
        assert MARKER_REL in prereqs

    def test_venv_test_stamp_depends_on_marker_and_pyproject(
        self,
        make_workspace: Path,
    ) -> None:
        """Option B: marker + pyproject.toml gate the stamp, not the alias."""
        prereqs = _prerequisites(make_workspace, VENV_TEST_STAMP_REL)
        assert MARKER_REL in prereqs
        assert "pyproject.toml" in prereqs

    def test_venv_otel_stamp_depends_on_marker_and_pyproject(
        self,
        make_workspace: Path,
    ) -> None:
        prereqs = _prerequisites(make_workspace, VENV_OTEL_STAMP_REL)
        assert MARKER_REL in prereqs
        assert "pyproject.toml" in prereqs

    def test_security_audit_depends_on_install(self, make_workspace: Path) -> None:
        prereqs = _prerequisites(make_workspace, "security-audit")
        assert "install" in prereqs

    def test_lock_target_has_no_venv_prerequisites(self, make_workspace: Path) -> None:
        prereqs = _prerequisites(make_workspace, "lock")
        assert prereqs == []

    def test_lock_dev_target_has_no_venv_prerequisites(self, make_workspace: Path) -> None:
        prereqs = _prerequisites(make_workspace, "lock-dev")
        assert prereqs == []

    def test_lock_otel_target_has_no_venv_prerequisites(self, make_workspace: Path) -> None:
        prereqs = _prerequisites(make_workspace, "lock-otel")
        assert prereqs == []

    def test_generate_mcp_fixtures_depends_on_marker(self, make_workspace: Path) -> None:
        prereqs = _prerequisites(make_workspace, "generate-mcp-fixtures")
        assert MARKER_REL in prereqs

    def test_check_mcp_fixtures_depends_on_marker(self, make_workspace: Path) -> None:
        prereqs = _prerequisites(make_workspace, "check-mcp-fixtures")
        assert MARKER_REL in prereqs

    def test_generate_license_inventory_depends_on_install(self, make_workspace: Path) -> None:
        prereqs = _prerequisites(make_workspace, "generate-license-inventory")
        assert "install" in prereqs

    def test_check_license_inventory_depends_on_install(self, make_workspace: Path) -> None:
        prereqs = _prerequisites(make_workspace, "check-license-inventory")
        assert "install" in prereqs

    def test_run_depends_on_marker_only(self, make_workspace: Path) -> None:
        """run stays marker-only; lint ensure is PYPOST-906."""
        prereqs = _prerequisites(make_workspace, "run")
        assert MARKER_REL in prereqs
        assert "install" not in prereqs
        assert "venv-test" not in prereqs

    def test_lint_depends_on_marker_and_venv_test(
        self,
        make_workspace: Path,
    ) -> None:
        """PYPOST-906: lint must pull [dev] via venv-test (like typecheck)."""
        prereqs = _prerequisites(make_workspace, "lint")
        assert MARKER_REL in prereqs
        assert "venv-test" in prereqs
        assert "install" not in prereqs

    def test_typecheck_depends_on_marker_and_venv_test(
        self,
        make_workspace: Path,
    ) -> None:
        """PYPOST-932: typecheck must pull [dev] via venv-test (peer lock)."""
        prereqs = _prerequisites(make_workspace, "typecheck")
        assert MARKER_REL in prereqs
        assert "venv-test" in prereqs
        assert "install" not in prereqs

    def test_test_slow_depends_on_venv_test_venv_otel_and_marker(
        self,
        make_workspace: Path,
    ) -> None:
        """PYPOST-872: slow pytest target also pulls [dev] via venv-test."""
        prereqs = _prerequisites(make_workspace, "test-slow")
        assert "venv-test" in prereqs
        assert "venv-otel" in prereqs
        assert MARKER_REL in prereqs

    def test_test_agent_e2e_depends_on_venv_test_venv_otel_and_marker(
        self,
        make_workspace: Path,
    ) -> None:
        """PYPOST-861 / PYPOST-872: agent e2e make entry deps include venv-test."""
        prereqs = _prerequisites(make_workspace, "test-agent-e2e")
        assert "venv-test" in prereqs
        assert "venv-otel" in prereqs
        assert MARKER_REL in prereqs


class TestLockFiles:
    def test_requirements_in_exists_in_repo(self) -> None:
        assert REQUIREMENTS_IN.is_file(), "requirements.in is the lock source of truth"

    def test_requirements_txt_has_uv_compile_header(self) -> None:
        header = REQUIREMENTS.read_text(encoding="utf-8").splitlines()[0]
        assert "autogenerated" in header.lower()

    def test_requirements_dev_in_exists_in_repo(self) -> None:
        assert REQUIREMENTS_DEV_IN.is_file(), (
            "requirements-dev.in is the dev lock source of truth"
        )

    def test_requirements_dev_txt_has_uv_compile_header(self) -> None:
        header = REQUIREMENTS_DEV.read_text(encoding="utf-8").splitlines()[0]
        assert "autogenerated" in header.lower()

    def test_requirements_otel_in_exists_in_repo(self) -> None:
        assert REQUIREMENTS_OTEL_IN.is_file(), (
            "requirements-otel.in is the OTel lock source of truth"
        )

    def test_requirements_otel_txt_has_uv_compile_header(self) -> None:
        header = REQUIREMENTS_OTEL.read_text(encoding="utf-8").splitlines()[0]
        assert "autogenerated" in header.lower()


class TestAgentE2eTargetRecipe:
    """PYPOST-861 / PYPOST-922: static contract for the env-pack make entry."""

    def test_makefile_default_selects_agent_e2e_marker(self) -> None:
        text = MAKEFILE.read_text(encoding="utf-8")
        recipe = makefile_target_recipe_body(text, _TEST_AGENT_E2E)
        assert '-m "agent_e2e and not slow"' in recipe
        assert "QT_QPA_PLATFORM=offscreen" in recipe

    def test_makefile_default_is_broader_than_golden_file(self) -> None:
        """PYPOST-922: default must be marker pack, not golden-only path."""
        text = MAKEFILE.read_text(encoding="utf-8")
        recipe = makefile_target_recipe_body(text, _TEST_AGENT_E2E)
        assert '-m "agent_e2e and not slow"' in recipe, (
            "test-agent-e2e default must select -m \"agent_e2e and not slow\""
        )
        # Default branch of $(if PYTEST_ARGS,...) must not hardcode golden.
        default_branch = recipe
        if "PYTEST_ARGS" in recipe:
            # Extract the false branch of $(if $(PYTEST_ARGS),then,else)
            marker = ",-m "
            idx = recipe.find(marker)
            assert idx != -1, (
                "expected $(if $(PYTEST_ARGS),...,-m ...) default branch"
            )
            default_branch = recipe[idx + 1:]  # starts with -m ...
        assert "test_agent_golden_e2e.py" not in default_branch, (
            "default test-agent-e2e selection must not hardcode "
            "tests/test_agent_golden_e2e.py as the sole path"
        )

    def test_makefile_help_comment_frames_broader_beyond_golden(self) -> None:
        """PYPOST-922: ## text must frame broader pack beyond golden."""
        text = MAKEFILE.read_text(encoding="utf-8")
        help_text = makefile_target_help_comment(text, _TEST_AGENT_E2E)
        lower = help_text.lower()
        assert "broader" in lower, (
            "test-agent-e2e ## help must include 'broader'; got: "
            f"{help_text!r}"
        )
        assert "beyond golden" in lower, (
            "test-agent-e2e ## help must include 'beyond golden'; got: "
            f"{help_text!r}"
        )


class TestFastTestTargetRecipe:
    """PYPOST-937: shared parser locks for the fast test make entry."""

    def test_makefile_default_excludes_slow_marker(self) -> None:
        text = MAKEFILE.read_text(encoding="utf-8")
        recipe = makefile_target_recipe_body(text, _TEST)
        assert '-m "not slow"' in recipe

    def test_makefile_parallel_runner_passes_workers(self) -> None:
        """PYPOST-1154: test target always forwards WORKERS to orchestrator."""
        text = MAKEFILE.read_text(encoding="utf-8")
        recipe = makefile_target_recipe_body(text, _TEST)
        assert "scripts/run_parallel_tests.py" in recipe
        assert "--workers $(WORKERS)" in recipe

    def test_makefile_workers_default_is_computed(self) -> None:
        """PYPOST-1154: WORKERS default is not empty."""
        text = MAKEFILE.read_text(encoding="utf-8")
        assert "default_worker_count" in text

    def test_makefile_help_comment_frames_fast_suite(self) -> None:
        text = MAKEFILE.read_text(encoding="utf-8")
        help_text = makefile_target_help_comment(text, _TEST)
        assert "fast test suite" in help_text.lower()


def test_collection_e2e_make_target_selects_the_focused_module() -> None:
    """PYPOST-1053: CI-safe collection e2e needs a dedicated discoverable target."""
    text = MAKEFILE.read_text(encoding="utf-8")
    recipe = makefile_target_recipe_body(text, "test-mcp-collection-e2e")
    assert "tests/test_mcp_collection_e2e.py" in recipe


class TestHelpTarget:
    def test_help_prints_non_empty_output(self, make_workspace: Path) -> None:
        """PYPOST-800: catch accidental removal of Makefile ## annotations."""
        result = _run_make(make_workspace, "help")
        assert result.returncode == 0, result.stderr
        assert result.stdout.strip(), (
            "make help produced empty output; check ## target annotations"
        )

    def test_help_lists_test_agent_e2e(self, make_workspace: Path) -> None:
        """PYPOST-861: env-pack make entry must stay discoverable via help."""
        result = _run_make(make_workspace, "help")
        assert result.returncode == 0, result.stderr
        assert "test-agent-e2e" in result.stdout

    def test_help_frames_test_agent_e2e_broader_beyond_golden(
        self,
        make_workspace: Path,
    ) -> None:
        """PYPOST-922: make help must surface broader-beyond-golden framing."""
        makefile_text = MAKEFILE.read_text(encoding="utf-8")
        expected = makefile_target_help_comment(
            makefile_text,
            _TEST_AGENT_E2E,
        ).lower()
        result = _run_make(make_workspace, "help")
        assert result.returncode == 0, result.stderr
        matching = [
            line
            for line in result.stdout.splitlines()
            if "test-agent-e2e" in line
        ]
        assert matching, "make help must list test-agent-e2e"
        line_lower = matching[0].lower()
        for token in ("broader", "beyond golden"):
            assert token in expected, (
                f"Makefile ## for test-agent-e2e must include {token!r}; "
                f"got: {expected!r}"
            )
            assert token in line_lower, (
                f"make help test-agent-e2e line must include {token!r}; "
                f"got: {matching[0]!r}"
            )
