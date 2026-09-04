"""Shared test helpers and fixtures for Makefile integration test suites."""

from __future__ import annotations

import os
import shutil
import subprocess
import sys
import time
import tomllib
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[1]
MAKEFILE = REPO_ROOT / "Makefile"
PYPROJECT = REPO_ROOT / "pyproject.toml"
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


# Minimum pypost/ tree for slow-smoke isolated workspace (PYPOST-963, PYPOST-964).
# Stub package only — not a full repo mirror. Widen when pyproject.toml requires more
# install-time modules; keep in sync with _seed_installable_package and the seed contract
# test in tests/test_makefile_install_seed_contract.py.
SLOW_SMOKE_MINIMUM_PYPPOST_FILES = frozenset(
    {
        "__init__.py",
        "version.py",
        "agent/__init__.py",
        "agent/ui_actions_mcp.py",
        "daemon.py",
    }
)

_SCRIPT_MODULE_STUB = (
    '"""Slow-smoke seed stub for console script entry point."""\n\n'
    "def main() -> None:\n"
    "    pass\n"
)


def _module_path_from_dotted_name(module: str) -> Path:
    """Map a dotted module name to a workspace-relative ``.py`` path."""
    return Path(module.replace(".", "/") + ".py")


def _package_init_paths_for_module(module_path: Path) -> list[Path]:
    """Return ``__init__.py`` paths for parent packages of a module file."""
    package_parts = module_path.parts[:-1]
    return [
        Path(*package_parts[:index]) / "__init__.py"
        for index in range(1, len(package_parts) + 1)
    ]


def _script_target_modules(pyproject_path: Path) -> frozenset[Path]:
    """Return module file paths referenced by ``[project.scripts]`` entry points."""
    data = tomllib.loads(pyproject_path.read_text(encoding="utf-8"))
    scripts = data.get("project", {}).get("scripts", {})
    return frozenset(
        _module_path_from_dotted_name(target.split(":")[0]) for target in scripts.values()
    )


def _paths_from_package_data(package_data: dict[str, list[str]], repo_root: Path) -> list[Path]:
    """Resolve ``[tool.setuptools.package-data]`` globs to repo-relative file paths."""
    resolved: list[Path] = []
    for package, patterns in package_data.items():
        package_dir = repo_root / package.replace(".", "/")
        if not package_dir.is_dir():
            continue
        for pattern in patterns:
            for match in package_dir.glob(pattern):
                if match.is_file():
                    resolved.append(match.relative_to(repo_root))
    return resolved


def _required_seed_paths_from_pyproject(
    pyproject_path: Path,
    *,
    repo_root: Path | None = None,
) -> list[Path]:
    """Return workspace-relative paths the slow-smoke seed must materialize."""
    root = repo_root or pyproject_path.parent
    data = tomllib.loads(pyproject_path.read_text(encoding="utf-8"))
    required: set[Path] = set()

    project = data.get("project", {})
    dynamic = project.get("dynamic", [])
    setuptools_cfg = data.get("tool", {}).get("setuptools", {})
    setuptools_dynamic = setuptools_cfg.get("dynamic", {})

    if "version" in dynamic:
        version_cfg = setuptools_dynamic.get("version", {})
        version_attr = version_cfg.get("attr")
        assert version_attr, (
            "pyproject.toml declares dynamic version but lacks "
            "[tool.setuptools.dynamic] version.attr"
        )
        version_module = _module_path_from_dotted_name(version_attr.rsplit(".", 1)[0])
        required.add(version_module)
        required.update(_package_init_paths_for_module(version_module))

    readme = project.get("readme")
    if isinstance(readme, str):
        required.add(Path(readme))
    elif isinstance(readme, dict) and readme.get("file"):
        required.add(Path(readme["file"]))

    license_files = list(project.get("license-files", []))
    if "license-files" in dynamic:
        dynamic_license = setuptools_dynamic.get("license-files")
        if isinstance(dynamic_license, list):
            license_files = dynamic_license
    license_files.extend(setuptools_cfg.get("license-files", []))
    required.update(Path(path) for path in license_files)

    scripts = project.get("scripts", {})
    for target in scripts.values():
        module_path = _module_path_from_dotted_name(target.split(":")[0])
        required.add(module_path)
        required.update(_package_init_paths_for_module(module_path))

    package_data = setuptools_cfg.get("package-data", {})
    required.update(_paths_from_package_data(package_data, root))

    return sorted(required)


def _materialize_seed_path(
    workspace: Path,
    rel: Path,
    *,
    repo_root: Path,
    script_modules: frozenset[Path],
) -> None:
    """Create one required seed path, copying from repo or writing a minimal stub."""
    dest = workspace / rel
    if dest.is_file():
        return
    dest.parent.mkdir(parents=True, exist_ok=True)
    src = repo_root / rel
    if src.is_file():
        shutil.copy(src, dest)
        return
    if rel.name == "__init__.py":
        dest.write_text("", encoding="utf-8")
        return
    if rel in script_modules:
        dest.write_text(_SCRIPT_MODULE_STUB, encoding="utf-8")
        return
    dest.write_text("", encoding="utf-8")


def _seed_installable_package(workspace: Path) -> None:
    """Seed minimum pypost/ tree and packaging files for committed pyproject.toml."""
    _seed_minimal_project(workspace)
    script_modules = _script_target_modules(PYPROJECT)
    for rel in _required_seed_paths_from_pyproject(PYPROJECT, repo_root=REPO_ROOT):
        _materialize_seed_path(
            workspace,
            rel,
            repo_root=REPO_ROOT,
            script_modules=script_modules,
        )


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


def _materialize_slow_smoke_workspace(workspace: Path) -> None:
    """Assemble slow-smoke isolated workspace (Makefile, pyproject, installable seed)."""
    shutil.copy(MAKEFILE, workspace / "Makefile")
    _copy_pyproject(workspace)
    _seed_installable_package(workspace)


# Post-install sanity snippets for slow-smoke venv (PYPOST-559, PYPOST-966).
# Version-module read avoids importing UI/Qt subpackages via package __init__.
POST_INSTALL_SANITY_SNIPPETS: tuple[str, ...] = (
    "import pydantic",
    "import pypost.version as v; assert v.__version__",
)


def _run_venv_python_snippet(
    bin_python: Path,
    snippet: str,
    *,
    timeout: float = 30,
) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [str(bin_python), "-c", snippet],
        capture_output=True,
        text=True,
        timeout=timeout,
        check=False,
    )


def _assert_post_install_sanity(bin_python: Path) -> None:
    """Run post-install import checks in the slow-smoke isolated venv."""
    assert bin_python.is_file()
    for snippet in POST_INSTALL_SANITY_SNIPPETS:
        proc = _run_venv_python_snippet(bin_python, snippet)
        assert proc.returncode == 0, proc.stderr or proc.stdout


@pytest.fixture
def make_workspace(tmp_path: Path) -> Path:
    shutil.copy(MAKEFILE, tmp_path / "Makefile")
    scripts_dir = tmp_path / "scripts"
    scripts_dir.mkdir()
    shutil.copy(REPO_ROOT / "scripts" / "run_parallel_tests.py", scripts_dir)
    _write_minimal_pyproject(tmp_path)
    _seed_minimal_project(tmp_path)
    return tmp_path


@pytest.fixture
def make_workspace_full_deps(tmp_path: Path) -> Path:
    _materialize_slow_smoke_workspace(tmp_path)
    return tmp_path
