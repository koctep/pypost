"""Discovery and safe copying of PyPost's bundled example library."""
from __future__ import annotations

from pathlib import Path
import logging
import shutil
from typing import Optional

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
        shutil.copytree(source, target)
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


__all__ = ["PredefinedLibraryService"]
