"""Fast declaration contracts for the single-source official examples package."""

from __future__ import annotations

import tomllib
from pathlib import Path
from typing import Any

import pytest
import yaml

pytestmark = pytest.mark.timeout(30)

REPO_ROOT = Path(__file__).resolve().parents[1]
EXAMPLES_PACKAGE = "pypost.bundled_examples"


def _setuptools_config() -> dict[str, Any]:
    data = tomllib.loads((REPO_ROOT / "pyproject.toml").read_text(encoding="utf-8"))
    return data["tool"]["setuptools"]


def _application_packages() -> set[str]:
    return {
        ".".join(path.parent.relative_to(REPO_ROOT).parts)
        for path in (REPO_ROOT / "pypost").rglob("__init__.py")
    }


def _required_examples(root: Path) -> set[Path]:
    manifest = yaml.safe_load((root / "pypost-library.yaml").read_text(encoding="utf-8"))
    required = {Path("pypost-library.yaml"), Path("README.md")}
    for collection in manifest["collections"]:
        path = Path(collection)
        assert not path.is_absolute() and ".." not in path.parts, collection
        required.add(path)
    required.update(path.relative_to(root) for path in (root / "environments").glob("*.json"))
    if (root / "builtin-collections.yaml").exists():
        required.add(Path("builtin-collections.yaml"))
    assert all((root / path).is_file() for path in required), "missing canonical example"
    return required


def _assert_package_set(packages: object) -> None:
    assert isinstance(packages, list), "setuptools must declare an explicit packages list"
    expected = _application_packages() | {EXAMPLES_PACKAGE}
    assert set(packages) == expected, f"package set differs: {set(packages) ^ expected}"


def _assert_resource_coverage(root: Path, patterns: list[str]) -> None:
    covered = {
        path.relative_to(root)
        for pattern in patterns
        for path in root.glob(pattern)
        if path.is_file()
    }
    missing = _required_examples(root) - covered
    assert not missing, f"uncovered required examples: {sorted(str(path) for path in missing)}"
    assert "builtin-collections.yaml" in patterns, "missing reserved Built-in declaration pattern"


def test_explicit_packages_cover_application_tree_and_examples() -> None:
    _assert_package_set(_setuptools_config().get("packages"))


def test_examples_mapping_has_regular_package_anchor() -> None:
    mapping = _setuptools_config().get("package-dir", {})
    assert mapping.get(EXAMPLES_PACKAGE) == "examples", "official examples source mapping missing"
    source = REPO_ROOT / mapping[EXAMPLES_PACKAGE]
    assert source.is_dir(), f"missing mapped package source: {source}"
    assert (source / "__init__.py").is_file(), f"missing mapped initializer: {source}"


def test_declared_data_covers_manifest_and_all_environments() -> None:
    patterns = _setuptools_config().get("package-data", {}).get(EXAMPLES_PACKAGE, [])
    _assert_resource_coverage(REPO_ROOT / "examples", patterns)


def test_package_guard_rejects_omitted_application_package() -> None:
    packages = sorted(_application_packages() | {EXAMPLES_PACKAGE})
    packages.remove("pypost.core")
    with pytest.raises(AssertionError, match="pypost.core"):
        _assert_package_set(packages)


@pytest.mark.parametrize("omitted", ["collections/*.json", "environments/*.json"])
def test_resource_guard_rejects_uncovered_files(omitted: str) -> None:
    patterns = [
        "pypost-library.yaml", "builtin-collections.yaml", "README.md",
        "collections/*.json", "environments/*.json",
    ]
    patterns.remove(omitted)
    with pytest.raises(AssertionError, match="uncovered required examples"):
        _assert_resource_coverage(REPO_ROOT / "examples", patterns)


def test_reserved_builtin_pattern_covers_future_declaration(tmp_path: Path) -> None:
    (tmp_path / "pypost-library.yaml").write_text("collections: []\n", encoding="utf-8")
    (tmp_path / "README.md").write_text("Examples\n", encoding="utf-8")
    (tmp_path / "builtin-collections.yaml").write_text("collections: []\n", encoding="utf-8")
    patterns = _setuptools_config().get("package-data", {}).get(EXAMPLES_PACKAGE, [])
    _assert_resource_coverage(tmp_path, patterns)
