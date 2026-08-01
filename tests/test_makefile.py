"""Integration tests for root Makefile automation (PYPOST-274, PYPOST-277)."""

from __future__ import annotations

import os
import shutil
import subprocess
import sys
import time
from pathlib import Path

import pytest

pytestmark = pytest.mark.timeout(120)

REPO_ROOT = Path(__file__).resolve().parents[1]
MAKEFILE = REPO_ROOT / "Makefile"
PYPROJECT = REPO_ROOT / "pyproject.toml"
README = REPO_ROOT / "README.md"
VERSION_PY = REPO_ROOT / "pypost" / "version.py"
REQUIREMENTS = REPO_ROOT / "requirements.txt"
REQUIREMENTS_IN = REPO_ROOT / "requirements.in"
REQUIREMENTS_DEV = REPO_ROOT / "requirements-dev.txt"
REQUIREMENTS_DEV_IN = REPO_ROOT / "requirements-dev.in"
REQUIREMENTS_OTEL = REPO_ROOT / "requirements-otel.txt"
REQUIREMENTS_OTEL_IN = REPO_ROOT / "requirements-otel.in"
PYTHON_VERSION = f"{sys.version_info.major}.{sys.version_info.minor}"
MARKER_NAME = f".initialized-{PYTHON_VERSION}"
MARKER_REL = f".venv/{MARKER_NAME}"
VENV_TEST_STAMP_NAME = f".venv-test-{PYTHON_VERSION}"
VENV_OTEL_STAMP_NAME = f".venv-otel-{PYTHON_VERSION}"
VENV_TEST_STAMP_REL = f".venv/{VENV_TEST_STAMP_NAME}"
VENV_OTEL_STAMP_REL = f".venv/{VENV_OTEL_STAMP_NAME}"


def _combined_output(proc: subprocess.CompletedProcess[str]) -> str:
    return f"{proc.stdout}\n{proc.stderr}"


def _assert_pip_install_extra(output: str, extra: str) -> None:
    assert "pip install" in output, (
        f"expected pip install of {extra!r} in make output; got:\n{output}"
    )
    assert extra in output, (
        f"expected extra {extra!r} in make output; got:\n{output}"
    )


def _assert_no_pip_install(output: str) -> None:
    assert "pip install" not in output, (
        "second visit must skip pip when extras are current; "
        f"got:\n{output}"
    )


def _make_stamp_stale(workspace: Path, stamp_name: str) -> None:
    """Ensure stamp exists and is older than pyproject.toml (FR3 invalidation)."""
    stamp = workspace / ".venv" / stamp_name
    stamp.parent.mkdir(parents=True, exist_ok=True)
    if not stamp.exists():
        stamp.touch()
    older = time.time() - 120
    os.utime(stamp, (older, older))
    pyproject = workspace / "pyproject.toml"
    newer = time.time()
    os.utime(pyproject, (newer, newer))


def _run_make(
    workspace: Path,
    *targets: str,
    check: bool = False,
    timeout: int = 110,
    pytest_args: str | None = "",
) -> subprocess.CompletedProcess[str]:
    env = os.environ.copy()
    env.pop("PYTEST_ARGS", None)
    cmd = ["make", f"PYTHON={sys.executable}"]
    if pytest_args is not None:
        cmd.append(f"PYTEST_ARGS={pytest_args}")
    cmd.extend(targets)
    return subprocess.run(
        cmd,
        cwd=workspace,
        capture_output=True,
        text=True,
        check=check,
        timeout=timeout,
        env=env,
    )


def _prerequisites(workspace: Path, target: str) -> list[str]:
    proc = subprocess.run(
        [
            "make",
            f"PYTHON={sys.executable}",
            "-p",
            "-f",
            "Makefile",
            "-C",
            str(workspace),
        ],
        capture_output=True,
        text=True,
        timeout=60,
        check=True,
    )
    prereqs: list[str] = []
    collecting = False
    prefix = f"{target}:"
    for line in proc.stdout.splitlines():
        if line.startswith(prefix):
            collecting = True
            tail = line[len(prefix):].strip()
            if tail:
                prereqs.extend(tail.split())
            continue
        if collecting:
            if not line or line[0] in {"\t", "#"}:
                break
            if line[0] == " ":
                prereqs.extend(line.strip().split())
            else:
                break
    return prereqs


def _seed_minimal_project(workspace: Path) -> None:
    tests_dir = workspace / "tests"
    tests_dir.mkdir(exist_ok=True)
    (tests_dir / "test_noop.py").write_text(
        "import pytest\n\npytestmark = pytest.mark.timeout(10)\n\n"
        "def test_noop() -> None:\n    assert True\n",
        encoding="utf-8",
    )
    pypost_dir = workspace / "pypost"
    pypost_dir.mkdir(exist_ok=True)
    (pypost_dir / "__init__.py").write_text("", encoding="utf-8")


def _seed_installable_package(workspace: Path) -> None:
    """Seed pypost/ and packaging files required by committed pyproject.toml."""
    _seed_minimal_project(workspace)
    shutil.copy(VERSION_PY, workspace / "pypost" / "version.py")
    shutil.copy(README, workspace / "README.md")


_MINIMAL_PYPROJECT = """\
[build-system]
requires = ["setuptools>=61.0"]
build-backend = "setuptools.build_meta"

[project]
name = "pypost"
version = "0.0.0"
dependencies = []

[project.optional-dependencies]
dev = [
    "pytest>=8,<9",
    "flake8>=7,<8",
]
otel = []

[tool.setuptools.packages.find]
where = ["."]
include = ["pypost*"]
"""


def _write_minimal_pyproject(workspace: Path) -> None:
    (workspace / "pyproject.toml").write_text(_MINIMAL_PYPROJECT, encoding="utf-8")


def _copy_pyproject(workspace: Path) -> None:
    shutil.copy(PYPROJECT, workspace / "pyproject.toml")


def _copy_dev_requirements(workspace: Path) -> None:
    shutil.copy(REQUIREMENTS_DEV, workspace / "requirements-dev.txt")


def _copy_otel_requirements(workspace: Path) -> None:
    shutil.copy(REQUIREMENTS_OTEL, workspace / "requirements-otel.txt")


@pytest.fixture
def make_workspace(tmp_path: Path) -> Path:
    shutil.copy(MAKEFILE, tmp_path / "Makefile")
    _write_minimal_pyproject(tmp_path)
    _seed_minimal_project(tmp_path)
    return tmp_path


@pytest.fixture
def make_workspace_full_deps(tmp_path: Path) -> Path:
    shutil.copy(MAKEFILE, tmp_path / "Makefile")
    _copy_pyproject(tmp_path)
    _seed_installable_package(tmp_path)
    return tmp_path


class TestMarkerLifecycle:
    def test_venv_creates_version_marker(self, make_workspace: Path) -> None:
        result = _run_make(make_workspace, "venv")
        assert result.returncode == 0, result.stderr
        marker = make_workspace / ".venv" / MARKER_NAME
        assert marker.is_file()

    def test_clean_removes_venv_and_marker(self, make_workspace: Path) -> None:
        _run_make(make_workspace, "venv", check=False)
        result = _run_make(make_workspace, "clean")
        assert result.returncode == 0, result.stderr
        assert not (make_workspace / ".venv").exists()

    def test_venv_is_idempotent(self, make_workspace: Path) -> None:
        first = _run_make(make_workspace, "venv")
        second = _run_make(make_workspace, "venv")
        assert first.returncode == 0, first.stderr
        assert second.returncode == 0, second.stderr
        assert (make_workspace / ".venv" / MARKER_NAME).is_file()


class TestVenvExtraStampIdempotency:
    """PYPOST-905: skip pip when stamp current; install when missing/stale."""

    def test_venv_test_skips_pip_when_current(self, make_workspace: Path) -> None:
        venv = _run_make(make_workspace, "venv")
        assert venv.returncode == 0, venv.stderr
        first = _run_make(make_workspace, "venv-test")
        assert first.returncode == 0, first.stderr
        second = _run_make(make_workspace, "venv-test")
        assert second.returncode == 0, second.stderr
        _assert_no_pip_install(_combined_output(second))

    def test_venv_otel_skips_pip_when_current(self, make_workspace: Path) -> None:
        venv = _run_make(make_workspace, "venv")
        assert venv.returncode == 0, venv.stderr
        first = _run_make(make_workspace, "venv-otel")
        assert first.returncode == 0, first.stderr
        second = _run_make(make_workspace, "venv-otel")
        assert second.returncode == 0, second.stderr
        _assert_no_pip_install(_combined_output(second))

    def test_venv_test_installs_when_stamp_missing(
        self,
        make_workspace: Path,
    ) -> None:
        stamp = make_workspace / ".venv" / VENV_TEST_STAMP_NAME
        venv = _run_make(make_workspace, "venv")
        assert venv.returncode == 0, venv.stderr
        if stamp.exists():
            stamp.unlink()
        result = _run_make(make_workspace, "venv-test")
        assert result.returncode == 0, result.stderr
        _assert_pip_install_extra(_combined_output(result), ".[dev]")

    def test_venv_otel_installs_when_stamp_missing(
        self,
        make_workspace: Path,
    ) -> None:
        stamp = make_workspace / ".venv" / VENV_OTEL_STAMP_NAME
        venv = _run_make(make_workspace, "venv")
        assert venv.returncode == 0, venv.stderr
        if stamp.exists():
            stamp.unlink()
        result = _run_make(make_workspace, "venv-otel")
        assert result.returncode == 0, result.stderr
        _assert_pip_install_extra(_combined_output(result), ".[otel]")

    def test_venv_test_installs_when_stamp_stale(
        self,
        make_workspace: Path,
    ) -> None:
        venv = _run_make(make_workspace, "venv")
        assert venv.returncode == 0, venv.stderr
        first = _run_make(make_workspace, "venv-test")
        assert first.returncode == 0, first.stderr
        _make_stamp_stale(make_workspace, VENV_TEST_STAMP_NAME)
        result = _run_make(make_workspace, "venv-test")
        assert result.returncode == 0, result.stderr
        _assert_pip_install_extra(_combined_output(result), ".[dev]")

    def test_venv_otel_installs_when_stamp_stale(
        self,
        make_workspace: Path,
    ) -> None:
        venv = _run_make(make_workspace, "venv")
        assert venv.returncode == 0, venv.stderr
        first = _run_make(make_workspace, "venv-otel")
        assert first.returncode == 0, first.stderr
        _make_stamp_stale(make_workspace, VENV_OTEL_STAMP_NAME)
        result = _run_make(make_workspace, "venv-otel")
        assert result.returncode == 0, result.stderr
        _assert_pip_install_extra(_combined_output(result), ".[otel]")

    def test_venv_test_depends_on_stamp(self, make_workspace: Path) -> None:
        prereqs = _prerequisites(make_workspace, "venv-test")
        assert VENV_TEST_STAMP_REL in prereqs

    def test_venv_otel_depends_on_stamp(self, make_workspace: Path) -> None:
        prereqs = _prerequisites(make_workspace, "venv-otel")
        assert VENV_OTEL_STAMP_REL in prereqs


class TestInstallExtraStampContract:
    """PYPOST-929: make install must touch both extra stamps."""

    def test_install_touches_both_extra_stamps(
        self,
        make_workspace: Path,
    ) -> None:
        venv = _run_make(make_workspace, "venv")
        assert venv.returncode == 0, venv.stderr
        test_stamp = make_workspace / ".venv" / VENV_TEST_STAMP_NAME
        otel_stamp = make_workspace / ".venv" / VENV_OTEL_STAMP_NAME
        assert not test_stamp.exists()
        assert not otel_stamp.exists()

        install = _run_make(make_workspace, "install")
        assert install.returncode == 0, install.stderr
        assert test_stamp.is_file(), (
            "make install must touch VENV_TEST_STAMP so venv-test skips pip"
        )
        assert otel_stamp.is_file(), (
            "make install must touch VENV_OTEL_STAMP so venv-otel skips pip"
        )

    def test_install_stamps_allow_skip_pip_on_venv_test_otel(
        self,
        make_workspace: Path,
    ) -> None:
        venv = _run_make(make_workspace, "venv")
        assert venv.returncode == 0, venv.stderr
        install = _run_make(make_workspace, "install")
        assert install.returncode == 0, install.stderr

        test_second = _run_make(make_workspace, "venv-test")
        assert test_second.returncode == 0, test_second.stderr
        _assert_no_pip_install(_combined_output(test_second))

        otel_second = _run_make(make_workspace, "venv-otel")
        assert otel_second.returncode == 0, otel_second.stderr
        _assert_no_pip_install(_combined_output(otel_second))


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


def _test_agent_e2e_help_comment(makefile_text: str) -> str:
    """Return the ## help description for the test-agent-e2e target."""
    for line in makefile_text.splitlines():
        if line.startswith("test-agent-e2e:") and "##" in line:
            return line.split("##", 1)[1].strip()
    raise AssertionError("Makefile missing test-agent-e2e ## help annotation")


def _test_agent_e2e_default_recipe_body(makefile_text: str) -> str:
    """Return recipe lines under test-agent-e2e until the next target."""
    lines = makefile_text.splitlines()
    collecting = False
    body: list[str] = []
    for line in lines:
        if line.startswith("test-agent-e2e:"):
            collecting = True
            continue
        if collecting:
            if line and not line[0].isspace() and not line.startswith("\t"):
                break
            body.append(line)
    assert body, "Makefile test-agent-e2e has an empty recipe body"
    return "\n".join(body)


class TestAgentE2eTargetRecipe:
    """PYPOST-861 / PYPOST-922: static contract for the env-pack make entry."""

    def test_makefile_default_selects_agent_e2e_marker(self) -> None:
        text = MAKEFILE.read_text(encoding="utf-8")
        assert "test-agent-e2e:" in text
        assert '-m "agent_e2e and not slow"' in text
        assert "QT_QPA_PLATFORM=offscreen" in text

    def test_makefile_default_is_broader_than_golden_file(self) -> None:
        """PYPOST-922: default must be marker pack, not golden-only path."""
        text = MAKEFILE.read_text(encoding="utf-8")
        recipe = _test_agent_e2e_default_recipe_body(text)
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
        help_text = _test_agent_e2e_help_comment(text)
        lower = help_text.lower()
        assert "broader" in lower, (
            "test-agent-e2e ## help must include 'broader'; got: "
            f"{help_text!r}"
        )
        assert "beyond golden" in lower, (
            "test-agent-e2e ## help must include 'beyond golden'; got: "
            f"{help_text!r}"
        )


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
        result = _run_make(make_workspace, "help")
        assert result.returncode == 0, result.stderr
        # Isolate the test-agent-e2e help line (ANSI codes may wrap the name).
        matching = [
            line
            for line in result.stdout.splitlines()
            if "test-agent-e2e" in line
        ]
        assert matching, "make help must list test-agent-e2e"
        line_lower = matching[0].lower()
        assert "broader" in line_lower, (
            "make help test-agent-e2e line must include 'broader'; got: "
            f"{matching[0]!r}"
        )
        assert "beyond golden" in line_lower, (
            "make help test-agent-e2e line must include 'beyond golden'; "
            f"got: {matching[0]!r}"
        )


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


@pytest.mark.slow
@pytest.mark.timeout(180)
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
        assert bin_python.is_file()
        proc = subprocess.run(
            [str(bin_python), "-c", "import pydantic"],
            capture_output=True,
            text=True,
            timeout=30,
            check=False,
        )
        assert proc.returncode == 0, proc.stderr
