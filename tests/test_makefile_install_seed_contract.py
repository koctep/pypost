"""PYPOST-943: slow-smoke isolated workspace seed must satisfy pyproject metadata."""

from __future__ import annotations

import shutil
import tomllib
from pathlib import Path

import pytest

from tests.test_makefile import (
    MAKEFILE,
    PYPROJECT,
    SLOW_SMOKE_MINIMUM_PYPPOST_FILES,
    _copy_pyproject,
    _seed_installable_package,
)

pytestmark = pytest.mark.timeout(30)


def _module_path_from_version_attr(attr: str) -> Path:
    """Map setuptools dynamic version attr to a workspace-relative module path."""
    module = attr.rsplit(".", 1)[0]
    return Path(module.replace(".", "/") + ".py")


def _required_seed_paths_from_pyproject(pyproject_path: Path) -> list[Path]:
    """Return workspace-relative paths the slow-smoke seed must materialize."""
    data = tomllib.loads(pyproject_path.read_text(encoding="utf-8"))
    required: list[Path] = []

    project = data.get("project", {})
    dynamic = project.get("dynamic", [])
    setuptools_dynamic = data.get("tool", {}).get("setuptools", {}).get("dynamic", {})

    if "version" in dynamic:
        version_cfg = setuptools_dynamic.get("version", {})
        version_attr = version_cfg.get("attr")
        assert version_attr, (
            "pyproject.toml declares dynamic version but lacks "
            "[tool.setuptools.dynamic] version.attr"
        )
        required.append(_module_path_from_version_attr(version_attr))

    readme = project.get("readme")
    if isinstance(readme, str):
        required.append(Path(readme))
    elif isinstance(readme, dict) and readme.get("file"):
        required.append(Path(readme["file"]))

    return required


def _materialize_slow_smoke_seed(workspace: Path) -> None:
    """Mirror make_workspace_full_deps seed (no network)."""
    shutil.copy(MAKEFILE, workspace / "Makefile")
    _copy_pyproject(workspace)
    _seed_installable_package(workspace)


def _pypost_relative_files(workspace: Path) -> frozenset[str]:
    """Return workspace-relative paths of files under pypost/."""
    pypost_dir = workspace / "pypost"
    return frozenset(
        path.relative_to(pypost_dir).as_posix()
        for path in pypost_dir.rglob("*")
        if path.is_file()
    )


def test_slow_smoke_seed_includes_pyproject_packaging_artifacts(
    tmp_path: Path,
) -> None:
    """Seed for make_workspace_full_deps must match committed pyproject.toml metadata."""
    required = _required_seed_paths_from_pyproject(PYPROJECT)
    assert required, (
        "expected pyproject.toml to declare dynamic version and/or readme paths"
    )

    _materialize_slow_smoke_seed(tmp_path)

    missing = [rel for rel in required if not (tmp_path / rel).is_file()]
    assert not missing, (
        "slow-smoke seed (make_workspace_full_deps) missing install-time artifacts "
        f"required by pyproject.toml: {[str(p) for p in missing]}"
    )


def test_slow_smoke_seed_materializes_minimum_pypost_tree(tmp_path: Path) -> None:
    """Slow-smoke seed uses stub pypost/ tree, not a full repo mirror (PYPOST-963)."""
    _materialize_slow_smoke_seed(tmp_path)

    actual = _pypost_relative_files(tmp_path)
    assert actual == SLOW_SMOKE_MINIMUM_PYPPOST_FILES, (
        "slow-smoke pypost/ tree drifted from SLOW_SMOKE_MINIMUM_PYPPOST_FILES policy: "
        f"expected {sorted(SLOW_SMOKE_MINIMUM_PYPPOST_FILES)!r}, got {sorted(actual)!r}. "
        "Update the policy constant and _seed_installable_package together when "
        "pyproject.toml requires additional install-time modules."
    )
