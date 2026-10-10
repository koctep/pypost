"""PYPOST-943 / PYPOST-964: slow-smoke seed must satisfy pyproject metadata."""

from __future__ import annotations

from pathlib import Path

import pytest
import yaml

from tests.makefile_test_helpers import (
    POST_INSTALL_SANITY_SNIPPETS,
    PYPROJECT,
    REPO_ROOT,
    SLOW_SMOKE_MINIMUM_PYPPOST_FILES,
    _materialize_slow_smoke_workspace,
    _required_seed_paths_from_pyproject,
    _script_target_modules,
)

pytestmark = pytest.mark.timeout(30)


def _pypost_relative_files(workspace: Path) -> frozenset[str]:
    """Return workspace-relative paths of files under pypost/."""
    pypost_dir = workspace / "pypost"
    return frozenset(
        path.relative_to(pypost_dir).as_posix()
        for path in pypost_dir.rglob("*")
        if path.is_file()
    )


def test_required_seed_paths_include_script_entry_modules() -> None:
    """Parser must cover [project.scripts] module paths (PYPOST-964)."""
    required = _required_seed_paths_from_pyproject(PYPROJECT, repo_root=REPO_ROOT)
    script_modules = _script_target_modules(PYPROJECT)
    assert script_modules, "expected committed pyproject.toml to declare console scripts"
    missing = sorted(path for path in script_modules if path not in required)
    assert not missing, (
        "seed contract parser missing script entry module paths: "
        f"{[str(path) for path in missing]}"
    )


def test_required_seed_paths_support_license_files_and_package_data(
    tmp_path: Path,
) -> None:
    """Parser covers license-files and package-data when declared in pyproject.toml."""
    license_path = tmp_path / "LICENSE"
    license_path.write_text("MIT\n", encoding="utf-8")
    package_dir = tmp_path / "pypost" / "data"
    package_dir.mkdir(parents=True)
    (package_dir / "defaults.json").write_text("{}\n", encoding="utf-8")
    pyproject = tmp_path / "pyproject.toml"
    pyproject.write_text(
        """
[project]
name = "demo"
license-files = ["LICENSE"]

[tool.setuptools.package-data]
pypost = ["data/*.json"]
""".strip()
        + "\n",
        encoding="utf-8",
    )

    required = _required_seed_paths_from_pyproject(pyproject, repo_root=tmp_path)
    assert Path("LICENSE") in required
    assert Path("pypost/data/defaults.json") in required


def test_slow_smoke_seed_includes_pyproject_packaging_artifacts(
    tmp_path: Path,
) -> None:
    """Seed for make_workspace_full_deps must match committed pyproject.toml metadata."""
    required = _required_seed_paths_from_pyproject(PYPROJECT, repo_root=REPO_ROOT)
    assert required, (
        "expected pyproject.toml to declare install-time paths for the slow-smoke seed"
    )

    _materialize_slow_smoke_workspace(tmp_path)

    missing = [rel for rel in required if not (tmp_path / rel).is_file()]
    assert not missing, (
        "slow-smoke seed (make_workspace_full_deps) missing install-time artifacts "
        f"required by pyproject.toml: {[str(p) for p in missing]}"
    )


def test_post_install_sanity_includes_pypost_version_read() -> None:
    """Slow smoke must assert post-install pypost importability (PYPOST-966)."""
    assert any("pypost" in snippet for snippet in POST_INSTALL_SANITY_SNIPPETS), (
        "POST_INSTALL_SANITY_SNIPPETS must include a pypost version read or import "
        "(PYPOST-966); slow smoke only checks core deps otherwise."
    )


def test_slow_smoke_seed_materializes_minimum_pypost_tree(tmp_path: Path) -> None:
    """Slow-smoke seed uses stub pypost/ tree, not a full repo mirror (PYPOST-963)."""
    _materialize_slow_smoke_workspace(tmp_path)

    actual = _pypost_relative_files(tmp_path)
    assert actual == SLOW_SMOKE_MINIMUM_PYPPOST_FILES, (
        "slow-smoke pypost/ tree drifted from SLOW_SMOKE_MINIMUM_PYPPOST_FILES policy: "
        f"expected {sorted(SLOW_SMOKE_MINIMUM_PYPPOST_FILES)!r}, got {sorted(actual)!r}. "
        "Update the policy constant and _seed_installable_package together when "
        "pyproject.toml requires additional install-time modules."
    )


def _write_explicit_seed_project(root: Path) -> Path:
    pyproject = root / "pyproject.toml"
    pyproject.write_text(
        '[project]\nname = "demo"\n'
        '[tool.setuptools]\npackages = ["pypost", "pypost.core", '
        '"pypost.bundled_examples"]\n'
        '[tool.setuptools.package-dir]\n"pypost.bundled_examples" = "examples"\n'
        '[tool.setuptools.package-data]\n'
        '"pypost.bundled_examples" = ["collections/*.json", "environments/*.json"]\n',
        encoding="utf-8",
    )
    for relative in ("pypost", "pypost/core", "examples"):
        directory = root / relative
        directory.mkdir(parents=True, exist_ok=True)
        (directory / "__init__.py").write_text("", encoding="utf-8")
    return pyproject


def test_seed_resolves_mapped_package_data(tmp_path: Path) -> None:
    pyproject = _write_explicit_seed_project(tmp_path)
    expected = {Path("examples/collections/demo.json"), Path("examples/environments/dev.json")}
    for relative in expected:
        target = tmp_path / relative
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text("{}\n", encoding="utf-8")
    actual = set(_required_seed_paths_from_pyproject(pyproject, repo_root=tmp_path))
    assert expected <= actual, f"missing mapped package data: {expected - actual}"


def test_seed_includes_every_explicit_package_initializer(tmp_path: Path) -> None:
    pyproject = _write_explicit_seed_project(tmp_path)
    expected = {
        Path("pypost/__init__.py"), Path("pypost/core/__init__.py"),
        Path("examples/__init__.py"),
    }
    actual = set(_required_seed_paths_from_pyproject(pyproject, repo_root=tmp_path))
    assert expected <= actual, f"missing explicit package initializers: {expected - actual}"


@pytest.mark.parametrize(
    ("package", "source"), [("pypost.core", "pypost/core"), ("pypost.bundled_examples", "examples")]
)
def test_seed_rejects_missing_declared_package_source(
    tmp_path: Path, package: str, source: str,
) -> None:
    pyproject = _write_explicit_seed_project(tmp_path)
    directory = tmp_path / source
    (directory / "__init__.py").unlink()
    directory.rmdir()
    with pytest.raises((AssertionError, ValueError, FileNotFoundError)) as error:
        _required_seed_paths_from_pyproject(pyproject, repo_root=tmp_path)
    assert package in str(error.value), "missing-source failure must identify the package"
    assert source in str(error.value), "missing-source failure must identify the source path"


def test_committed_seed_covers_independent_source_inventory(tmp_path: Path) -> None:
    examples = REPO_ROOT / "examples"
    manifest = yaml.safe_load((examples / "pypost-library.yaml").read_text(encoding="utf-8"))
    required = {
        Path("examples/__init__.py"), Path("examples/pypost-library.yaml"),
        Path("examples/README.md"),
    }
    required.update(Path("examples") / collection for collection in manifest["collections"])
    required.update(
        path.relative_to(REPO_ROOT) for path in (examples / "environments").glob("*.json")
    )
    required.update(
        path.relative_to(REPO_ROOT) for path in (REPO_ROOT / "pypost").rglob("__init__.py")
    )
    if (examples / "builtin-collections.yaml").is_file():
        required.add(Path("examples/builtin-collections.yaml"))
    _materialize_slow_smoke_workspace(tmp_path)
    missing = sorted(str(path) for path in required if not (tmp_path / path).is_file())
    assert not missing, f"incomplete committed install seed: {missing}"
    for path in required:
        assert (tmp_path / path).read_bytes() == (REPO_ROOT / path).read_bytes(), path
