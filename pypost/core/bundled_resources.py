"""Authoritative filesystem discovery of bundled PyPost examples resources."""
from __future__ import annotations

import importlib
import importlib.resources
import logging
from pathlib import Path

import yaml

logger = logging.getLogger(__name__)

EXPECTED_LIBRARY_MANIFEST_ID = "pypost-examples"
BUNDLED_EXAMPLES_PACKAGE = "pypost.bundled_examples"
MANIFEST_FILENAME = "pypost-library.yaml"


def _validate_sibling_manifest(root: Path) -> bool:
    """Return True if root contains a readable manifest with the expected library id."""
    manifest_path = root / MANIFEST_FILENAME
    if not manifest_path.is_file():
        logger.debug(
            "bundled_examples_sibling_manifest_missing path=%s", manifest_path
        )
        return False
    try:
        content = manifest_path.read_text(encoding="utf-8")
        parsed = yaml.safe_load(content)
        if isinstance(parsed, dict) and parsed.get("id") == EXPECTED_LIBRARY_MANIFEST_ID:
            return True
        logger.warning(
            "bundled_examples_sibling_manifest_id_mismatch path=%s found_id=%s",
            manifest_path,
            parsed.get("id") if isinstance(parsed, dict) else None,
        )
        return False
    except Exception as error:  # noqa: BLE001 - robust discovery fallback
        logger.warning(
            "bundled_examples_sibling_manifest_read_failed path=%s error=%s",
            manifest_path,
            error,
        )
        return False


def _resolve_sibling_root() -> Path | None:
    """Resolve sibling examples/ root relative to active pypost module directory."""
    try:
        import pypost
        pypost_file = getattr(pypost, "__file__", None)
        if not pypost_file:
            return None
        pypost_dir = Path(pypost_file).resolve().parent
        candidate = pypost_dir.parent / "examples"
        if not candidate.is_dir():
            return None
        if not (candidate / "__init__.py").is_file():
            logger.debug(
                "bundled_examples_sibling_missing_init path=%s", candidate
            )
            return None
        if not _validate_sibling_manifest(candidate):
            return None
        return candidate
    except Exception as error:  # noqa: BLE001 - robust discovery fallback
        logger.warning("bundled_examples_sibling_resolution_failed error=%s", error)
        return None


def _resolve_package_resource() -> Path | None:
    """Resolve package resource pypost.bundled_examples when backed by a filesystem directory."""
    try:
        traversable = importlib.resources.files(BUNDLED_EXAMPLES_PACKAGE)
        if isinstance(traversable, Path) and traversable.is_dir():
            if (traversable / MANIFEST_FILENAME).is_file():
                return traversable
        # Handle cases where traversable is not directly Path or has as_file / other interface
        if hasattr(traversable, "is_dir") and traversable.is_dir():
            candidate = Path(str(traversable))
            if candidate.is_dir() and (candidate / MANIFEST_FILENAME).is_file():
                return candidate
    except Exception as error:  # noqa: BLE001 - robust discovery fallback
        logger.debug(
            "bundled_examples_package_resource_resolution_failed package=%s error=%s",
            BUNDLED_EXAMPLES_PACKAGE,
            error,
        )
    return None


def bundled_examples_root() -> Path | None:
    """Return the authoritative root directory for bundled examples, or None if unavailable.

    Resolution order:
    1. Sibling source tree: Path(pypost.__file__).resolve().parents[1] / "examples",
       requiring __init__.py and pypost-library.yaml with id matching EXPECTED_LIBRARY_MANIFEST_ID.
    2. Package resource: importlib.resources.files("pypost.bundled_examples") when it resolves
       to a filesystem Path containing pypost-library.yaml.
    3. None fallback.
    """
    sibling = _resolve_sibling_root()
    if sibling is not None:
        logger.info("bundled_examples_root_resolved source=sibling path=%s", sibling)
        return sibling

    package_resource = _resolve_package_resource()
    if package_resource is not None:
        logger.info(
            "bundled_examples_root_resolved source=package_resource path=%s",
            package_resource,
        )
        return package_resource

    logger.warning("bundled_examples_root_not_found")
    return None


__all__ = [
    "BUNDLED_EXAMPLES_PACKAGE",
    "EXPECTED_LIBRARY_MANIFEST_ID",
    "bundled_examples_root",
]
