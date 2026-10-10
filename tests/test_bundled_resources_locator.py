"""Unit tests for the bundled resources locator (PYPOST-1349).

Asserts hierarchical resolution of bundled examples:
1. Sibling examples/ directory in repository checkout with __init__.py and pypost-library.yaml.
2. Sibling directory without __init__.py or with foreign manifest id is rejected.
3. Package resource pypost.bundled_examples resolution when sibling tree is unavailable.
4. Sibling directory precedence over package resource pointing elsewhere.
5. Fallback to None when neither exists or is valid.
6. PredefinedLibraryService(root=None) uses bundled_examples_root().
7. PredefinedLibraryService.copy_to(destination) filters __init__.py, __pycache__, and *.pyc.
"""
from __future__ import annotations

import json
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest
import yaml

from pypost.core.bundled_resources import (
    EXPECTED_LIBRARY_MANIFEST_ID,
    bundled_examples_root,
)
from pypost.core.predefined_library import PredefinedLibraryService

pytestmark = pytest.mark.timeout(30)


def _create_mock_manifest(directory: Path, manifest_id: str = EXPECTED_LIBRARY_MANIFEST_ID) -> Path:
    """Create a minimal valid pypost-library.yaml manifest file in directory."""
    manifest_data = {
        "schema_version": "1.0.0",
        "id": manifest_id,
        "name": "Test Examples",
        "version": "1.0.0",
        "collections": [],
    }
    manifest_path = directory / "pypost-library.yaml"
    manifest_path.write_text(yaml.safe_dump(manifest_data), encoding="utf-8")
    return manifest_path


def test_bundled_examples_root_resolves_sibling_tree(tmp_path: Path):
    """bundled_examples_root locates the sibling examples/ directory when valid."""
    repo_root = tmp_path / "mock_repo"
    repo_root.mkdir()

    pypost_dir = repo_root / "pypost"
    pypost_dir.mkdir()
    fake_pypost_file = pypost_dir / "__init__.py"
    fake_pypost_file.write_text("# fake pypost", encoding="utf-8")

    examples_dir = repo_root / "examples"
    examples_dir.mkdir()
    (examples_dir / "__init__.py").write_text("# marker", encoding="utf-8")
    _create_mock_manifest(examples_dir, manifest_id=EXPECTED_LIBRARY_MANIFEST_ID)

    mock_pypost = MagicMock()
    mock_pypost.__file__ = str(fake_pypost_file)

    with patch.dict("sys.modules", {"pypost": mock_pypost}):
        resolved = bundled_examples_root()
        assert resolved is not None
        assert resolved.resolve() == examples_dir.resolve()


def test_bundled_examples_root_sibling_takes_precedence_over_package_resource(tmp_path: Path):
    """Sibling directory takes precedence over a package resource pointing elsewhere."""
    repo_root = tmp_path / "mock_repo"
    repo_root.mkdir()

    pypost_dir = repo_root / "pypost"
    pypost_dir.mkdir()
    fake_pypost_file = pypost_dir / "__init__.py"
    fake_pypost_file.write_text("# fake pypost", encoding="utf-8")

    examples_dir = repo_root / "examples"
    examples_dir.mkdir()
    (examples_dir / "__init__.py").write_text("# marker", encoding="utf-8")
    _create_mock_manifest(examples_dir, manifest_id=EXPECTED_LIBRARY_MANIFEST_ID)

    pkg_resource_dir = tmp_path / "site-packages" / "pypost" / "bundled_examples"
    pkg_resource_dir.mkdir(parents=True)
    _create_mock_manifest(pkg_resource_dir, manifest_id=EXPECTED_LIBRARY_MANIFEST_ID)

    mock_pypost = MagicMock()
    mock_pypost.__file__ = str(fake_pypost_file)

    with patch.dict("sys.modules", {"pypost": mock_pypost}), \
         patch("importlib.resources.files", return_value=pkg_resource_dir):
        resolved = bundled_examples_root()
        assert resolved is not None
        assert resolved.resolve() == examples_dir.resolve()
        assert resolved.resolve() != pkg_resource_dir.resolve()


def test_bundled_examples_root_rejects_sibling_without_init(tmp_path: Path):
    """Sibling directory without __init__.py is rejected."""
    repo_root = tmp_path / "mock_repo"
    repo_root.mkdir()

    pypost_dir = repo_root / "pypost"
    pypost_dir.mkdir()
    fake_pypost_file = pypost_dir / "__init__.py"
    fake_pypost_file.write_text("# fake pypost", encoding="utf-8")

    examples_dir = repo_root / "examples"
    examples_dir.mkdir()
    # Missing __init__.py intentionally
    _create_mock_manifest(examples_dir, manifest_id=EXPECTED_LIBRARY_MANIFEST_ID)

    mock_pypost = MagicMock()
    mock_pypost.__file__ = str(fake_pypost_file)

    with patch.dict("sys.modules", {"pypost": mock_pypost}), \
         patch("importlib.resources.files", side_effect=ModuleNotFoundError):
        resolved = bundled_examples_root()
        assert resolved is None


def test_bundled_examples_root_rejects_sibling_with_mismatched_manifest_id(tmp_path: Path):
    """Sibling directory with a foreign manifest id is rejected."""
    repo_root = tmp_path / "mock_repo"
    repo_root.mkdir()

    pypost_dir = repo_root / "pypost"
    pypost_dir.mkdir()
    fake_pypost_file = pypost_dir / "__init__.py"
    fake_pypost_file.write_text("# fake pypost", encoding="utf-8")

    examples_dir = repo_root / "examples"
    examples_dir.mkdir()
    (examples_dir / "__init__.py").write_text("# marker", encoding="utf-8")
    _create_mock_manifest(examples_dir, manifest_id="foreign-examples-id")

    mock_pypost = MagicMock()
    mock_pypost.__file__ = str(fake_pypost_file)

    with patch.dict("sys.modules", {"pypost": mock_pypost}), \
         patch("importlib.resources.files", side_effect=ModuleNotFoundError):
        resolved = bundled_examples_root()
        assert resolved is None


def test_bundled_examples_root_resolves_package_resource_when_no_sibling(tmp_path: Path):
    """When no valid sibling exists, package resource pypost.bundled_examples is resolved."""
    pkg_resource_dir = tmp_path / "site-packages" / "pypost" / "bundled_examples"
    pkg_resource_dir.mkdir(parents=True)
    _create_mock_manifest(pkg_resource_dir, manifest_id=EXPECTED_LIBRARY_MANIFEST_ID)

    # Isolated pypost module path whose sibling is not an examples directory
    isolated_dir = tmp_path / "isolated" / "pypost"
    isolated_dir.mkdir(parents=True)
    fake_pypost_file = isolated_dir / "__init__.py"
    fake_pypost_file.write_text("# isolated pypost", encoding="utf-8")

    mock_pypost = MagicMock()
    mock_pypost.__file__ = str(fake_pypost_file)

    with patch.dict("sys.modules", {"pypost": mock_pypost}), \
         patch("importlib.resources.files", return_value=pkg_resource_dir):
        resolved = bundled_examples_root()
        assert resolved is not None
        assert resolved.resolve() == pkg_resource_dir.resolve()


def test_bundled_examples_root_returns_none_when_neither_exists(tmp_path: Path):
    """Fallback to None when neither sibling nor package resource exists."""
    isolated_dir = tmp_path / "isolated" / "pypost"
    isolated_dir.mkdir(parents=True)
    fake_pypost_file = isolated_dir / "__init__.py"
    fake_pypost_file.write_text("# isolated pypost", encoding="utf-8")

    mock_pypost = MagicMock()
    mock_pypost.__file__ = str(fake_pypost_file)

    with patch.dict("sys.modules", {"pypost": mock_pypost}), \
         patch("importlib.resources.files", side_effect=ModuleNotFoundError):
        resolved = bundled_examples_root()
        assert resolved is None


def test_predefined_library_service_defaults_to_locator():
    """PredefinedLibraryService(root=None) uses bundled_examples_root()."""
    sentinel_path = Path("/mock/sentinel/examples")

    with patch(
        "pypost.core.predefined_library.bundled_examples_root", return_value=sentinel_path
    ) as mock_locator:
        service = PredefinedLibraryService(root=None)
        mock_locator.assert_called_once()
        assert service.root == sentinel_path


def test_predefined_library_service_handles_none_root_in_discover():
    """When locator returns None, PredefinedLibraryService.discover() returns None gracefully."""
    with patch("pypost.core.predefined_library.bundled_examples_root", return_value=None):
        service = PredefinedLibraryService(root=None)
        record = service.discover()
        assert record is None
        assert any("unavailable" in diag.lower() for diag in service.diagnostics)


def test_predefined_library_copy_to_filters_packaging_artifacts(tmp_path: Path):
    """PredefinedLibraryService.copy_to(destination) ignores __init__.py and __pycache__."""
    source_root = tmp_path / "source_examples"
    source_root.mkdir()
    (source_root / "__init__.py").write_text("# packaging anchor", encoding="utf-8")
    pycache_dir = source_root / "__pycache__"
    pycache_dir.mkdir()
    (pycache_dir / "marker.cpython-311.pyc").write_bytes(b"\x00\x00")
    (source_root / "stray.pyc").write_bytes(b"\x00\x00")

    # Valid manifest and minimal collection
    manifest_data = {
        "schema_version": "1.0.0",
        "id": "pypost-examples",
        "name": "PyPost Official Examples",
        "version": "2.0.0",
        "collections": ["collections/sample.json"],
    }
    manifest_yaml = yaml.safe_dump(manifest_data)
    (source_root / "pypost-library.yaml").write_text(manifest_yaml, encoding="utf-8")
    collections_dir = source_root / "collections"
    collections_dir.mkdir()
    sample_collection = {
        "id": "sample-coll",
        "name": "Sample Collection",
        "requests": [],
    }
    (collections_dir / "sample.json").write_text(json.dumps(sample_collection), encoding="utf-8")

    service = PredefinedLibraryService(root=source_root)
    destination = tmp_path / "user_copy"

    service.copy_to(destination)

    assert destination.is_dir()
    assert (destination / "pypost-library.yaml").is_file()
    assert (destination / "collections" / "sample.json").is_file()

    # Packaging artifacts MUST be ignored
    assert not (destination / "__init__.py").exists(), "__init__.py should not be copied"
    assert not (destination / "__pycache__").exists(), "__pycache__ directory should not be copied"
    assert not (destination / "stray.pyc").exists(), "*.pyc files should not be copied"
