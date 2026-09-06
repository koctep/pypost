"""Discovery and safe copying of PyPost's bundled example library."""
from __future__ import annotations

from pathlib import Path
import logging
import shutil
from typing import Optional

from pypost.core.collection_import import load_collection_import_candidates
from pypost.core.library_manifest import find_and_read_manifest, validate_manifest_collections
from pypost.models.library_manager import LibraryConnectionRecord, LibrarySourceType
from pypost.models.library_manifest import ManifestDiagnosticError

logger = logging.getLogger(__name__)


class PredefinedLibraryService:
    """Expose the repository examples as a validated, read-only library template."""

    DEFAULT_LIBRARY_ID = "pypost-examples"

    def __init__(self, root: Path | str | None = None) -> None:
        self.root = (
            Path(root)
            if root is not None
            else Path(__file__).resolve().parents[2] / "examples"
        )
        self.diagnostics: list[str] = []

    def discover(self) -> Optional[LibraryConnectionRecord]:
        """Return the predefined record when the bundled content is valid."""
        self.diagnostics.clear()
        logger.info(
            "predefined_library_discovery_started library_id=%s", self.DEFAULT_LIBRARY_ID
        )
        try:
            manifest, _ = find_and_read_manifest(self.root)
            missing = validate_manifest_collections(manifest, manifest_dir=self.root)
        except (ManifestDiagnosticError, OSError, ValueError) as error:
            self.diagnostics.append(
                f"Predefined library is unavailable: {type(error).__name__}."
            )
            logger.warning(
                "predefined_library_discovery_failed library_id=%s error_type=%s",
                self.DEFAULT_LIBRARY_ID,
                type(error).__name__,
            )
            return None
        if manifest.id != self.DEFAULT_LIBRARY_ID:
            self.diagnostics.append("Predefined library manifest has an unexpected identity.")
            logger.warning(
                "predefined_library_identity_mismatch library_id=%s", manifest.id
            )
            return None
        if missing:
            self.diagnostics.append("Predefined library is missing declared collections.")
            logger.warning(
                "predefined_library_collections_missing library_id=%s count=%d",
                self.DEFAULT_LIBRARY_ID,
                len(missing),
            )
            return None
        root = self.root.expanduser().resolve(strict=False)
        for relative in manifest.collections:
            try:
                collection_path = _declared_collection_path(root, relative)
                _collections, parse_errors = load_collection_import_candidates(collection_path)
            except Exception as error:  # noqa: BLE001 - discovery must reject bad bundles
                self.diagnostics.append(
                    f"Predefined library collection is invalid: {relative}."
                )
                logger.warning(
                    "predefined_library_collection_invalid library_id=%s path=%s "
                    "error_type=%s",
                    self.DEFAULT_LIBRARY_ID,
                    relative,
                    type(error).__name__,
                )
                return None
            if parse_errors or not _collections:
                self.diagnostics.append(
                    f"Predefined library collection is invalid: {relative}."
                )
                logger.warning(
                    "predefined_library_collection_invalid library_id=%s path=%s "
                    "parse_error_count=%d collection_count=%d",
                    self.DEFAULT_LIBRARY_ID,
                    relative,
                    len(parse_errors),
                    len(_collections),
                )
                return None
        logger.info(
            "predefined_library_discovery_completed library_id=%s collection_count=%d",
            manifest.id,
            len(manifest.collections),
        )
        return LibraryConnectionRecord(
            stable_id=manifest.id,
            manifest_id=manifest.id,
            display_name=manifest.name,
            local_path=self.root,
            source_type=LibrarySourceType.PREDEFINED,
            is_read_only=True,
        )

    def copy_to(self, destination: Path | str) -> LibraryConnectionRecord:
        """Copy the validated template to a new editable local library."""
        source_record = self.discover()
        if source_record is None:
            raise ValueError("predefined_invalid: bundled examples are unavailable")
        source = self.root.expanduser().resolve(strict=False)
        target = Path(destination).expanduser().resolve(strict=False)
        if target == source or _contains(source, target) or _contains(target, source):
            raise ValueError("predefined_invalid: editable copy must be outside bundled examples")
        if target.exists():
            raise FileExistsError(f"Editable library destination already exists: {target}")
        logger.info(
            "predefined_library_copy_started library_id=%s destination_name=%s",
            source_record.stable_id,
            target.name,
        )
        try:
            shutil.copytree(source, target)
        except Exception:
            if target.is_dir():
                shutil.rmtree(target, ignore_errors=True)
            raise
        copied = PredefinedLibraryService(target).discover()
        if copied is None:
            shutil.rmtree(target, ignore_errors=True)
            raise ValueError("predefined_invalid: copied examples failed validation")
        logger.info(
            "predefined_library_copy_completed library_id=%s destination_name=%s",
            source_record.stable_id,
            target.name,
        )
        return copied.model_copy(
            update={
                "stable_id": f"{source_record.stable_id}-copy",
                "source_type": LibrarySourceType.REGISTERED,
                "is_read_only": False,
            }
        )


def _contains(parent: Path, child: Path) -> bool:
    """Return whether child is equal to or below parent."""
    try:
        child.relative_to(parent)
    except ValueError:
        return False
    return True


def _declared_collection_path(root: Path, relative: str) -> Path:
    """Resolve a manifest collection only when it stays inside the bundle."""
    candidate = (root / relative).resolve(strict=False)
    try:
        candidate.relative_to(root)
    except ValueError as error:
        raise ValueError(f"Collection path escapes predefined library: {relative}") from error
    return candidate


__all__ = ["PredefinedLibraryService"]
