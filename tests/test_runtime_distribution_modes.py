"""Failing repro tests for dual runtime distribution modes (PYPOST-1269).

Asserts requirements for GUI desktop and headless daemon distribution modes:
1. pyproject.toml declares console script pypost = "pypost.main:main"
2. Package module execution via python -m pypost (pypost/__main__.py)
3. Headless daemon and core storage runtime isolation from PySide6.QtWidgets
4. Core domain architecture invariant (no PySide6.QtWidgets imports in core/models)
5. Distribution packaging entry points metadata containing both console scripts
"""

from __future__ import annotations

import ast
import os
import subprocess
import sys
import tomllib
from pathlib import Path

import pytest

pytestmark = pytest.mark.timeout(30)

REPO_ROOT = Path(__file__).resolve().parents[1]


def test_pyproject_declares_gui_console_script() -> None:
    """Verify pyproject.toml defines pypost = 'pypost.main:main' in [project.scripts]."""
    pyproject_path = REPO_ROOT / "pyproject.toml"
    assert pyproject_path.is_file(), "pyproject.toml missing"
    with pyproject_path.open("rb") as f:
        data = tomllib.load(f)

    scripts = data.get("project", {}).get("scripts", {})
    assert "pypost" in scripts, (
        "pyproject.toml missing 'pypost' console script under [project.scripts]"
    )
    assert scripts["pypost"] == "pypost.main:main", (
        f"Expected pypost='pypost.main:main', got {scripts['pypost']!r}"
    )
    assert scripts.get("pypost-daemon") == "pypost.daemon:main", (
        f"Expected pypost-daemon='pypost.daemon:main', got {scripts.get('pypost-daemon')!r}"
    )


def test_package_module_execution_main_entrypoint_exists() -> None:
    """Verify python -m pypost entrypoint exists at pypost/__main__.py and can be executed."""
    main_module = REPO_ROOT / "pypost" / "__main__.py"
    assert main_module.is_file(), "pypost/__main__.py entry point does not exist"

    env = os.environ.copy()
    env["PYTHONPATH"] = str(REPO_ROOT)
    res = subprocess.run(
        [sys.executable, "-m", "pypost", "--help"],
        capture_output=True,
        text=True,
        env=env,
        timeout=10,
    )
    assert "No module named pypost.__main__" not in res.stderr
    assert res.returncode == 0


def test_headless_daemon_import_isolation_without_qtwidgets() -> None:
    """Verify headless daemon and core storage do not load PySide6.QtWidgets when display unset."""
    env = os.environ.copy()
    env.pop("DISPLAY", None)
    env.pop("WAYLAND_DISPLAY", None)
    env["QT_QPA_PLATFORM"] = "offscreen"
    env["PYTHONPATH"] = str(REPO_ROOT)

    verification_code = (
        "import sys\n"
        "from unittest.mock import MagicMock\n"
        "import pypost.daemon\n"
        "from pypost.core.qt.environment_storage_gateway import EnvironmentStorageGateway\n"
        "gateway = EnvironmentStorageGateway(MagicMock())\n"
        "gateway.wait_idle(timeout_ms=10)\n"
        "assert 'PySide6.QtWidgets' not in sys.modules, (\n"
        "    f'QtWidgets leaked into headless imports: {sys.modules.get(\"PySide6.QtWidgets\")}'\n"
        ")\n"
        "assert 'pypost.ui' not in sys.modules, (\n"
        "    f'pypost.ui leaked into headless imports: '\n"
        "    f'{[m for m in sys.modules if m.startswith(\"pypost.ui\")]}'\n"
        ")\n"
    )

    res = subprocess.run(
        [sys.executable, "-c", verification_code],
        capture_output=True,
        text=True,
        env=env,
        timeout=15,
    )
    assert res.returncode == 0, (
        f"Headless daemon import isolation failed:\nstdout: {res.stdout}\nstderr: {res.stderr}"
    )


def test_core_and_models_architectural_boundary_no_qtwidgets() -> None:
    """Verify architectural invariant: pypost.core/models do not import PySide6.QtWidgets."""
    violations: list[str] = []
    for package in [REPO_ROOT / "pypost" / "core", REPO_ROOT / "pypost" / "models"]:
        for py_path in package.rglob("*.py"):
            tree = ast.parse(py_path.read_text(encoding="utf-8"), filename=str(py_path))
            for node in ast.walk(tree):
                if isinstance(node, ast.Import):
                    for alias in node.names:
                        if alias.name.startswith("PySide6.QtWidgets") or alias.name.startswith(
                            "pypost.ui"
                        ):
                            rel_path = py_path.relative_to(REPO_ROOT)
                            violations.append(f"{rel_path}:{node.lineno} imports {alias.name}")
                elif isinstance(node, ast.ImportFrom):
                    mod = node.module or ""
                    if mod.startswith("PySide6.QtWidgets") or mod.startswith("pypost.ui"):
                        rel_path = py_path.relative_to(REPO_ROOT)
                        violations.append(f"{rel_path}:{node.lineno} imports from {mod}")

    assert not violations, (
        "Architectural boundary violations found (QtWidgets / pypost.ui imported in core/models):\n"
        + "\n".join(violations)
    )


def test_packaging_distribution_entry_points_metadata() -> None:
    """Verify distribution metadata registers console scripts for pypost and pypost-daemon."""
    from importlib.metadata import entry_points

    console_scripts = {
        ep.name: ep.value
        for ep in entry_points(group="console_scripts")
    }
    assert "pypost" in console_scripts, (
        f"'pypost' missing from registered console_scripts: {console_scripts}"
    )
    assert console_scripts["pypost"] == "pypost.main:main", (
        f"Expected pypost='pypost.main:main', got {console_scripts.get('pypost')!r}"
    )
    assert "pypost-daemon" in console_scripts, (
        f"'pypost-daemon' missing from registered console_scripts: {console_scripts}"
    )
    assert console_scripts["pypost-daemon"] == "pypost.daemon:main", (
        f"Expected pypost-daemon='pypost.daemon:main', got {console_scripts.get('pypost-daemon')!r}"
    )
