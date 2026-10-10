"""Curated built-in collection view over the bundled examples library (PYPOST-1350)."""
from __future__ import annotations

from dataclasses import dataclass
import json
import logging
from pathlib import Path
from typing import Any, Optional

import yaml

from pypost.core.collection_serializer import read_collection_file
from pypost.core.predefined_library import PredefinedLibraryService
from pypost.models.models import Collection, Environment
from pypost.models.settings import McpServerConfiguration

logger = logging.getLogger(__name__)

__all__ = [
    "BuiltinCollectionEntry",
    "BuiltinCollectionView",
]


@dataclass(frozen=True)
class BuiltinCollectionEntry:
    """Descriptor for one curated built-in collection entry."""

    collection_path: str
    environment_path: str
    name: str
    collection_id: str
    version: Optional[str]

    def selection(self) -> dict[str, str]:
        """Return library identity dictionary matching McpServerConfiguration expectations."""
        return {
            "library_id": PredefinedLibraryService.DEFAULT_LIBRARY_ID,
            "manifest_id": PredefinedLibraryService.DEFAULT_LIBRARY_ID,
            "path": self.collection_path,
        }


class BuiltinCollectionView:
    """Read-only view over the bundled examples library presenting curated Built-in collections."""

    CATALOG_FILENAME = "builtin-collections.yaml"

    def __init__(self, predefined: Optional[PredefinedLibraryService] = None) -> None:
        self._predefined = predefined or PredefinedLibraryService()
        self.diagnostics: list[str] = []

    @property
    def root(self) -> Optional[Path]:
        """Return root path to the predefined examples library."""
        return self._predefined.root

    def list_entries(self) -> list[BuiltinCollectionEntry]:
        """List curated built-in collection entries validated against the library manifest."""
        self.diagnostics.clear()

        if self.root is None:
            msg = "Bundled examples root not found."
            self.diagnostics.append(msg)
            logger.warning("builtin_collections_unavailable reason=no_root")
            return []

        resolved_root = self.root.expanduser().resolve(strict=False)
        if not resolved_root.is_dir():
            msg = f"Bundled examples root does not exist: {resolved_root}"
            self.diagnostics.append(msg)
            logger.warning(
                "builtin_collections_unavailable reason=dir_not_found root=%s",
                resolved_root,
            )
            return []

        library_record = self._predefined.discover()
        if library_record is None:
            self.diagnostics.extend(self._predefined.diagnostics)
            if not self.diagnostics:
                self.diagnostics.append("Predefined library discovery failed.")
            logger.warning("builtin_collections_discovery_failed")
            return []

        catalog_path = resolved_root / self.CATALOG_FILENAME
        if not catalog_path.is_file():
            msg = f"Built-in collections catalog not found: {catalog_path}"
            self.diagnostics.append(msg)
            logger.warning("builtin_collections_catalog_missing path=%s", catalog_path)
            return []

        try:
            content = catalog_path.read_text(encoding="utf-8")
            data = yaml.safe_load(content)
        except Exception as exc:
            msg = f"Failed to parse {self.CATALOG_FILENAME}: {exc}"
            self.diagnostics.append(msg)
            logger.warning("builtin_collections_catalog_parse_failed reason=%s", exc)
            return []

        if not isinstance(data, dict):
            msg = (
                f"Invalid {self.CATALOG_FILENAME}: expected root mapping, "
                f"got {type(data).__name__}"
            )
            self.diagnostics.append(msg)
            logger.warning("builtin_collections_catalog_invalid_root")
            return []

        entries_raw = data.get("entries")
        if not isinstance(entries_raw, list):
            msg = f"Invalid {self.CATALOG_FILENAME}: 'entries' field must be a list."
            self.diagnostics.append(msg)
            logger.warning("builtin_collections_catalog_invalid_entries")
            return []

        # Read manifest collections to verify that each catalog entry is in the manifest
        manifest_collections = self._get_manifest_collections(resolved_root)

        entries: list[BuiltinCollectionEntry] = []
        for raw_entry in entries_raw:
            if not isinstance(raw_entry, dict):
                self.diagnostics.append(
                    f"Invalid catalog entry: expected dict, got {type(raw_entry).__name__}"
                )
                continue

            collection_rel = raw_entry.get("collection")
            env_rel = raw_entry.get("environment")

            if not collection_rel or not isinstance(collection_rel, str):
                self.diagnostics.append("Catalog entry missing valid 'collection' path.")
                continue

            if not env_rel or not isinstance(env_rel, str):
                self.diagnostics.append(
                    f"Catalog entry '{collection_rel}' missing valid 'environment' path."
                )
                continue

            if collection_rel not in manifest_collections:
                msg = (
                    f"Catalog entry '{collection_rel}' is not declared in "
                    "library manifest collections."
                )
                self.diagnostics.append(msg)
                logger.warning("builtin_collections_entry_undeclared path=%s", collection_rel)
                continue

            collection_full_path = (resolved_root / collection_rel).resolve(strict=False)
            try:
                collection_full_path.relative_to(resolved_root)
            except ValueError:
                self.diagnostics.append(f"Collection path escapes library root: {collection_rel}")
                continue

            if not collection_full_path.is_file():
                self.diagnostics.append(f"Collection file not found: {collection_rel}")
                continue

            try:
                coll_text = collection_full_path.read_text(encoding="utf-8")
                coll_json = json.loads(coll_text)
            except Exception as exc:
                self.diagnostics.append(
                    f"Failed to read collection JSON '{collection_rel}': {exc}"
                )
                continue

            entry_name = raw_entry.get("name") or coll_json.get("name") or collection_rel
            collection_id = coll_json.get("id") or raw_entry.get("id") or ""
            version = coll_json.get("version")

            entry = BuiltinCollectionEntry(
                collection_path=collection_rel,
                environment_path=env_rel,
                name=entry_name,
                collection_id=collection_id,
                version=version,
            )
            entries.append(entry)
            logger.debug(
                "builtin_collection_entry_loaded entry_id=%s path=%s env=%s",
                collection_id,
                collection_rel,
                env_rel,
            )

        logger.info(
            "builtin_collections_list_completed library_id=%s entry_count=%d",
            PredefinedLibraryService.DEFAULT_LIBRARY_ID,
            len(entries),
        )
        return entries

    def _get_manifest_collections(self, root: Path) -> set[str]:
        """Read collection paths declared in pypost-library.yaml."""
        manifest_path = root / "pypost-library.yaml"
        if not manifest_path.is_file():
            return set()
        try:
            manifest_data = yaml.safe_load(manifest_path.read_text(encoding="utf-8"))
            if isinstance(manifest_data, dict):
                return set(manifest_data.get("collections", []))
        except Exception:
            return set()
        return set()

    def load_collection(self, collection_path: str) -> Collection:
        """Load and parse the collection file freshly from disk (no caching)."""
        target = self._resolve_entry_path(collection_path, is_environment=False)
        return read_collection_file(target)

    def load_paired_environment(self, collection_path: str) -> Environment:
        """Load and parse the paired template environment file freshly from disk (no caching)."""
        target = self._resolve_entry_path(collection_path, is_environment=True)
        try:
            content = target.read_text(encoding="utf-8")
            data = json.loads(content)
        except OSError as exc:
            raise FileNotFoundError(f"Could not read environment file {target}: {exc}") from exc
        except json.JSONDecodeError as exc:
            raise ValueError(f"Invalid JSON in environment file {target}: {exc}") from exc

        env_item = data[0] if isinstance(data, list) and data else data
        if not isinstance(env_item, dict):
            raise ValueError(
                f"Expected environment object in {target}, got {type(env_item).__name__}"
            )
        return Environment(**env_item)

    def _resolve_entry_path(self, collection_path: str, *, is_environment: bool) -> Path:
        """Validate collection_path against curated entries and resolve file path."""
        entries = self.list_entries()
        matched = next((e for e in entries if e.collection_path == collection_path), None)
        if matched is None:
            raise ValueError(
                f"Collection '{collection_path}' is not a curated built-in collection."
            )

        if self.root is None:
            raise FileNotFoundError("Bundled examples root is unavailable.")

        resolved_root = self.root.expanduser().resolve(strict=False)
        rel_path = matched.environment_path if is_environment else matched.collection_path
        target = (resolved_root / rel_path).resolve(strict=False)

        try:
            target.relative_to(resolved_root)
        except ValueError as exc:
            raise ValueError(f"Path escapes library root: {rel_path}") from exc

        if not target.is_file():
            raise FileNotFoundError(f"File not found: {target}")

        return target

    def is_builtin(self, configuration: Any) -> bool:
        """Check whether a configuration targets a curated built-in collection."""
        if not isinstance(configuration, McpServerConfiguration):
            return False

        if configuration.library_id != PredefinedLibraryService.DEFAULT_LIBRARY_ID:
            return False

        builtin_paths = {entry.collection_path for entry in self.list_entries()}
        return configuration.library_collection_path in builtin_paths
