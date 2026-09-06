"""Qt-free collection import from connected collection libraries.

The service is deliberately read-only with respect to library connections and
their files.  It resolves a manifest entry again immediately before applying
an import, then delegates conflict planning and active-collection persistence
to the existing collection import contracts.
"""
from __future__ import annotations

import logging
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path, PurePosixPath, PureWindowsPath
from typing import Any, Iterable, Optional

from pypost.core.collection_import import (
    CollectionImportFileError,
    CollectionImportPlanResult,
    load_collection_import_candidates,
    plan_collection_import,
    recount_collection_import_plan,
)
from pypost.core.collection_import_apply import apply_imported_collections
from pypost.core.import_conflicts import ImportConflictDecision
from pypost.core.library_manifest import find_and_read_manifest
from pypost.models.library_manager import LibraryConnectionRecord, LibrarySourceType
from pypost.models.models import Collection, LibraryCollectionLink

logger = logging.getLogger(__name__)

_MANIFEST_ENTRY_LABEL = "<library manifest>"


class LibraryImportMode(str, Enum):
    """How a library collection becomes an active collection."""

    COPY = "copy"
    LINK = "link"


@dataclass(frozen=True)
class LibraryCollectionImportEntry:
    """One manifest-declared collection row shown to an import selector."""

    library_id: str
    manifest_id: Optional[str]
    collection_path: str
    display_name: str
    source_type: LibrarySourceType | str
    local_path: Optional[Path] = None
    error: Optional[str] = None
    candidate_count: int = 0
    collection_index: Optional[int] = None
    library_name: Optional[str] = None

    @property
    def source_label(self) -> str:
        """Return the path fallback used when a collection has no name."""
        return self.collection_path


@dataclass(frozen=True)
class LibraryCollectionImportCandidate:
    """Validated collection content plus the source identity needed for Link."""

    collection: Collection
    library_id: str
    manifest_id: Optional[str]
    collection_path: str
    display_name: str
    source_type: LibrarySourceType | str
    local_path: Optional[Path] = None
    collection_index: Optional[int] = None

    @property
    def payload(self) -> Collection:
        """Compatibility alias for callers that call content a payload."""
        return self.collection

    @property
    def library_link(self) -> LibraryCollectionLink:
        """Build the source association for Link materialization."""
        return LibraryCollectionLink(
            library_id=self.library_id,
            manifest_id=self.manifest_id,
            collection_path=self.collection_path,
            collection_index=self.collection_index,
        )


@dataclass(frozen=True)
class LibraryCollectionImportResolution:
    """Results of re-resolving selected rows immediately before apply."""

    candidates: list[LibraryCollectionImportCandidate] = field(default_factory=list)
    errors: list[str] = field(default_factory=list)
    entries: list[LibraryCollectionImportEntry] = field(default_factory=list)

    @property
    def failed(self) -> list[str]:
        """Compatibility alias for per-entry diagnostics."""
        return self.errors

    @property
    def is_successful(self) -> bool:
        return bool(self.candidates) and not self.errors


@dataclass(frozen=True)
class LibraryCollectionImportResult:
    """Outcome of applying library candidates to active collection storage."""

    plan: CollectionImportPlanResult
    failures: list[str] = field(default_factory=list)
    resolution_errors: list[str] = field(default_factory=list)

    @property
    def collections(self) -> list[Collection]:
        return self.plan.collections

    @property
    def persisted(self) -> list[Collection]:
        return self.plan.persisted

    @property
    def added(self) -> list[str]:
        return self.plan.added

    @property
    def updated(self) -> list[str]:
        return self.plan.updated

    @property
    def skipped(self) -> list[str]:
        return self.plan.skipped

    @property
    def renamed(self) -> list[tuple[str, str]]:
        return self.plan.renamed

    @property
    def errors(self) -> list[str]:
        return [*self.resolution_errors, *self.failures]


class LibraryCollectionImportError(Exception):
    """Raised when no selected library collection can safely be imported."""

    def __init__(self, message: str | Iterable[str], *, errors: Iterable[str] = ()):
        if isinstance(message, str):
            rendered = message
            collected = list(errors)
        else:
            collected = list(message)
            rendered = "; ".join(collected) or "The library collection import failed."
        self.errors = collected or [rendered]
        super().__init__(rendered)


class LibraryCollectionImportCancelled(LibraryCollectionImportError):
    """Raised when selection or conflict decisions are cancelled."""

    def __init__(self, message: str = "Library collection import was cancelled."):
        super().__init__(message)


# Short names are useful to UI code and preserve a small public import surface.
LibraryImportEntry = LibraryCollectionImportEntry
LibraryImportCandidate = LibraryCollectionImportCandidate
LibraryImportResolution = LibraryCollectionImportResolution


class LibraryCollectionImportService:
    """Read connected library collections and apply safe active imports."""

    def __init__(self, *, library_manager: Any) -> None:
        self.library_manager = library_manager

    def list_entries(
        self, connection: LibraryConnectionRecord | None = None
    ) -> list[LibraryCollectionImportEntry]:
        """List declared collection files for registered and cloned libraries.

        A bad library or bad collection remains represented by a row with a
        diagnostic.  This lets the selector explain why an item is unavailable
        without making one malformed entry hide the remaining libraries.
        """
        connections = [connection] if connection is not None else self._connections()
        entries: list[LibraryCollectionImportEntry] = []
        for record in connections:
            if not self._is_supported_source(record):
                continue
            try:
                root = self._canonical_root(record)
                manifest, _manifest_path = find_and_read_manifest(root)
            except Exception as exc:  # noqa: BLE001 - row diagnostics are intentional
                diagnostic = self._diagnostic("Library unavailable", exc)
                entries.append(
                    self._entry(
                        record,
                        _MANIFEST_ENTRY_LABEL,
                        record.display_name or record.stable_id,
                        diagnostic,
                    )
                )
                logger.warning(
                    "library_collection_manifest_unavailable library_id=%s error_type=%s",
                    record.stable_id,
                    type(exc).__name__,
                )
                continue

            for raw_path in manifest.collections:
                path_text = str(raw_path)
                display_name = path_text
                error: str | None = None
                candidate_count = 0
                try:
                    collection_path, normalized = self._resolve_declared_path(
                        root, path_text
                    )
                    collections, parse_errors = load_collection_import_candidates(
                        collection_path
                    )
                    candidate_count = len(collections)
                    if collections:
                        for collection_index, collection in enumerate(collections):
                            entries.append(
                                self._entry(
                                    record,
                                    path_text,
                                    self._collection_label(collection, normalized),
                                    None,
                                    candidate_count=1,
                                    collection_index=collection_index,
                                    library_name=manifest.name,
                                )
                            )
                        if parse_errors:
                            entries.append(
                                self._entry(
                                    record,
                                    path_text,
                                    normalized,
                                    "; ".join(parse_errors),
                                    candidate_count=candidate_count,
                                    library_name=manifest.name,
                                )
                            )
                        continue
                    if parse_errors:
                        error = "; ".join(parse_errors)
                    if not collections and error is None:
                        error = "The collection entry is invalid or empty."
                except Exception as exc:  # noqa: BLE001 - per-row diagnostics
                    error = self._diagnostic("Collection unavailable", exc)
                entries.append(
                    self._entry(
                        record,
                        path_text,
                        display_name,
                        error,
                        candidate_count=candidate_count,
                        library_name=manifest.name,
                    )
                )
        logger.info(
            "library_collection_entries_listed library_count=%d entry_count=%d error_count=%d",
            len(connections),
            len(entries),
            sum(entry.error is not None for entry in entries),
        )
        return entries

    def resolve_entries(
        self, entries: Iterable[LibraryCollectionImportEntry]
    ) -> LibraryCollectionImportResolution:
        """Reload selected connections and resolve each manifest path safely."""
        selected = list(entries)
        candidates: list[LibraryCollectionImportCandidate] = []
        errors: list[str] = []
        for entry in selected:
            try:
                record = self._find_connection(entry.library_id)
                if record is None:
                    raise LibraryCollectionImportError(
                        f"Library '{entry.library_id}' is unavailable."
                    )
                root = self._canonical_root(record)
                manifest, _manifest_path = find_and_read_manifest(root)
                if entry.manifest_id and manifest.id != entry.manifest_id:
                    raise LibraryCollectionImportError(
                        f"Library '{entry.library_id}' changed its manifest identity."
                    )
                normalized_entry = self._normalize_relative_path(entry.collection_path)
                declared = {
                    self._normalize_relative_path(path)
                    for path in manifest.collections
                    if self._is_safe_relative_path(path)
                }
                if normalized_entry not in declared:
                    raise LibraryCollectionImportError(
                        "Collection "
                        f"'{entry.collection_path}' is no longer declared by the library."
                    )
                collection_path, normalized = self._resolve_declared_path(
                    root, entry.collection_path
                )
                collections, parse_errors = load_collection_import_candidates(
                    collection_path
                )
                errors.extend(self._entry_error(entry, error) for error in parse_errors)
                if not collections:
                    if parse_errors:
                        continue
                    raise LibraryCollectionImportError(
                        f"Collection '{entry.collection_path}' is unavailable or invalid."
                    )
                indexes = (
                    [entry.collection_index]
                    if entry.collection_index is not None
                    else range(len(collections))
                )
                for collection_index in indexes:
                    if collection_index is None or collection_index >= len(collections):
                        raise LibraryCollectionImportError(
                            f"Collection '{entry.collection_path}' is no longer available."
                        )
                    collection = collections[collection_index]
                    candidates.append(
                        LibraryCollectionImportCandidate(
                            collection=collection.model_copy(deep=True),
                            library_id=record.stable_id,
                            manifest_id=manifest.id,
                            collection_path=normalized,
                            display_name=self._collection_label(collection, normalized),
                            source_type=record.source_type,
                            local_path=collection_path,
                            collection_index=collection_index,
                        )
                    )
            except LibraryCollectionImportError as exc:
                errors.extend(self._entry_error(entry, error) for error in exc.errors)
            except Exception as exc:  # noqa: BLE001 - resolution is per selection
                errors.append(
                    self._entry_error(
                        entry, self._diagnostic("Collection unavailable", exc)
                    )
                )

        logger.info(
            "library_collection_entries_resolved selected_count=%d "
            "candidate_count=%d error_count=%d",
            len(selected),
            len(candidates),
            len(errors),
        )
        return LibraryCollectionImportResolution(
            candidates=candidates, errors=errors, entries=selected
        )

    def materialize_candidate(
        self,
        candidate: LibraryCollectionImportCandidate | Collection,
        mode: LibraryImportMode,
    ) -> Collection:
        """Deep-copy a candidate, optionally adding its source association."""
        import_mode = self._mode(mode)
        source, link = self._candidate_source(candidate)
        materialized = source.model_copy(deep=True)
        if import_mode is LibraryImportMode.COPY:
            return materialized.model_copy(update={"library_link": None}, deep=True)
        if link is None:
            raise LibraryCollectionImportError(
                "Link mode requires a connected library collection source."
            )
        return materialized.model_copy(update={"library_link": link}, deep=True)

    def apply_candidates(
        self,
        active_manager: Any,
        candidates: Iterable[LibraryCollectionImportCandidate | Collection],
        mode: LibraryImportMode,
        conflict_decisions: dict[str, ImportConflictDecision] | None = None,
        *,
        cancelled: bool = False,
    ) -> LibraryCollectionImportResult:
        """Plan and durably apply candidates to the active collection manager."""
        if cancelled:
            raise LibraryCollectionImportCancelled()
        import_mode = self._mode(mode)
        materialized = [
            self.materialize_candidate(candidate, import_mode) for candidate in candidates
        ]
        existing = list(active_manager.get_collections())
        decisions = self._normalize_decisions(conflict_decisions or {})
        plan = plan_collection_import(existing, materialized, decisions)
        self._restore_link_metadata(plan, materialized, import_mode)
        apply_result = apply_imported_collections(
            active_manager, plan.collections, plan.persisted
        )
        if apply_result.failed_ids:
            plan = recount_collection_import_plan(plan, apply_result.failed_ids)
        logger.info(
            "library_collection_import_applied mode=%s candidate_count=%d "
            "persisted_count=%d failure_count=%d",
            import_mode.value,
            len(materialized),
            len(plan.persisted),
            len(apply_result.failures),
        )
        return LibraryCollectionImportResult(plan, failures=list(apply_result.failures))

    def import_entries(
        self,
        active_manager: Any,
        entries: Iterable[LibraryCollectionImportEntry],
        *,
        mode: LibraryImportMode,
        conflict_decisions: dict[str, ImportConflictDecision] | None = None,
        cancelled: bool = False,
    ) -> LibraryCollectionImportResult:
        """Resolve, validate, and apply selected entries without source writes."""
        if cancelled or conflict_decisions is None:
            raise LibraryCollectionImportCancelled()
        resolution = self.resolve_entries(entries)
        if not resolution.candidates:
            raise LibraryCollectionImportError(
                resolution.errors or ["No selected library collection is available."]
            )
        result = self.apply_candidates(
            active_manager,
            resolution.candidates,
            mode,
            conflict_decisions,
        )
        return LibraryCollectionImportResult(
            result.plan,
            failures=result.failures,
            resolution_errors=resolution.errors,
        )

    def resolve_link(self, link: LibraryCollectionLink) -> Collection:
        """Resolve the current source content for a persisted Link metadata value."""
        entry = LibraryCollectionImportEntry(
            library_id=link.library_id,
            manifest_id=link.manifest_id,
            collection_path=link.collection_path,
            display_name=link.collection_path,
            source_type=LibrarySourceType.REGISTERED,
            collection_index=link.collection_index,
        )
        resolution = self.resolve_entries([entry])
        if not resolution.candidates:
            raise LibraryCollectionImportError(
                resolution.errors or ["The linked library collection is unavailable."]
            )
        return self.materialize_candidate(resolution.candidates[0], LibraryImportMode.LINK)

    def refresh_linked_collection(self, collection: Collection) -> Collection:
        """Return source-authoritative content while preserving the active ID."""
        if collection.library_link is None:
            raise LibraryCollectionImportError("The collection has no library link.")
        refreshed = self.resolve_link(collection.library_link)
        return refreshed.model_copy(update={"id": collection.id}, deep=True)

    # A concise alias for presenter code and callers using the architecture name.
    refresh_link = refresh_linked_collection

    def _connections(self) -> list[LibraryConnectionRecord]:
        list_connections = getattr(self.library_manager, "list_connections", None)
        if not callable(list_connections):
            return []
        records = list_connections()
        return [record for record in records or [] if isinstance(record, LibraryConnectionRecord)]

    def _find_connection(self, stable_id: str) -> LibraryConnectionRecord | None:
        for record in self._connections():
            if record.stable_id == stable_id:
                return record
        get_connection = getattr(self.library_manager, "get_connection", None)
        if callable(get_connection):
            record = get_connection(stable_id)
            if isinstance(record, LibraryConnectionRecord):
                return record
        return None

    @staticmethod
    def _is_supported_source(record: LibraryConnectionRecord) -> bool:
        return record.source_type in (LibrarySourceType.REGISTERED, LibrarySourceType.CLONED)

    @staticmethod
    def _canonical_root(record: LibraryConnectionRecord) -> Path:
        root = Path(record.local_path).expanduser().resolve(strict=False)
        if not root.is_dir():
            raise LibraryCollectionImportError(
                f"Library '{record.stable_id}' is unavailable at its configured root."
            )
        return root

    @staticmethod
    def _is_safe_relative_path(raw_path: str) -> bool:
        if not isinstance(raw_path, str) or not raw_path.strip():
            return False
        value = raw_path.strip()
        if "\\" in value:
            return False
        posix = PurePosixPath(value)
        windows = PureWindowsPath(value)
        return not (
            posix.is_absolute()
            or windows.is_absolute()
            or bool(windows.drive)
            or any(part == ".." for part in posix.parts)
        )

    @classmethod
    def _normalize_relative_path(cls, raw_path: str) -> str:
        if not cls._is_safe_relative_path(raw_path):
            raise LibraryCollectionImportError(
                f"Invalid collection path '{raw_path}': paths must stay within the library root."
            )
        parts = [part for part in PurePosixPath(raw_path.strip()).parts if part not in ("", ".")]
        if not parts:
            raise LibraryCollectionImportError("Invalid collection path: path is empty.")
        return PurePosixPath(*parts).as_posix()

    @classmethod
    def _resolve_declared_path(cls, root: Path, raw_path: str) -> tuple[Path, str]:
        normalized = cls._normalize_relative_path(raw_path)
        candidate = (root / normalized).resolve(strict=False)
        try:
            candidate.relative_to(root)
        except ValueError as exc:
            raise LibraryCollectionImportError(
                f"Invalid collection path '{raw_path}': path escapes the library root."
            ) from exc
        if not candidate.is_file():
            raise LibraryCollectionImportError(
                f"Collection '{normalized}' is unavailable or missing."
            )
        return candidate, normalized

    @staticmethod
    def _collection_label(collection: Collection, fallback: str) -> str:
        return collection.name.strip() if collection.name.strip() else fallback

    @staticmethod
    def _entry(
        record: LibraryConnectionRecord,
        path: str,
        display_name: str,
        error: str | None,
        *,
        candidate_count: int = 0,
        collection_index: int | None = None,
        library_name: str | None = None,
    ) -> LibraryCollectionImportEntry:
        return LibraryCollectionImportEntry(
            library_id=record.stable_id,
            manifest_id=record.manifest_id,
            collection_path=path,
            display_name=display_name or path or record.stable_id,
            source_type=record.source_type,
            local_path=Path(record.local_path),
            error=error,
            candidate_count=candidate_count,
            collection_index=collection_index,
            library_name=library_name or record.display_name or record.stable_id,
        )

    @staticmethod
    def _diagnostic(prefix: str, exc: Exception) -> str:
        if isinstance(exc, CollectionImportFileError):
            detail = str(exc)
        else:
            detail = str(exc) or type(exc).__name__
        return f"{prefix}: {detail}"

    @staticmethod
    def _entry_error(entry: LibraryCollectionImportEntry, error: str) -> str:
        return f"{entry.display_name} ({entry.collection_path}): {error}"

    @staticmethod
    def _mode(mode: LibraryImportMode | str) -> LibraryImportMode:
        try:
            return mode if isinstance(mode, LibraryImportMode) else LibraryImportMode(mode)
        except ValueError as exc:
            raise LibraryCollectionImportError(
                f"Unsupported library import mode: {mode!r}"
            ) from exc

    @staticmethod
    def _normalize_decisions(
        decisions: dict[str, ImportConflictDecision],
    ) -> dict[str, ImportConflictDecision]:
        normalized: dict[str, ImportConflictDecision] = {}
        for name, decision in decisions.items():
            normalized[name] = (
                decision
                if isinstance(decision, ImportConflictDecision)
                else ImportConflictDecision(decision)
            )
        return normalized

    @staticmethod
    def _candidate_source(
        candidate: LibraryCollectionImportCandidate | Collection,
    ) -> tuple[Collection, LibraryCollectionLink | None]:
        if isinstance(candidate, LibraryCollectionImportCandidate):
            return candidate.collection, candidate.library_link
        return candidate, candidate.library_link

    @staticmethod
    def _restore_link_metadata(
        plan: CollectionImportPlanResult,
        materialized: list[Collection],
        mode: LibraryImportMode,
    ) -> None:
        if mode is not LibraryImportMode.LINK:
            return
        links_by_name = {
            collection.name: collection.library_link
            for collection in materialized
            if collection.library_link is not None
        }
        renamed_to_original = {new: original for original, new in plan.renamed}
        for collection in plan.persisted:
            link = links_by_name.get(collection.name)
            if link is None:
                original_name = renamed_to_original.get(collection.name)
                if original_name is not None:
                    link = links_by_name.get(original_name)
            if link is not None:
                collection.library_link = link.model_copy(deep=True)


__all__ = [
    "LibraryCollectionImportCandidate",
    "LibraryCollectionImportCancelled",
    "LibraryCollectionImportEntry",
    "LibraryCollectionImportError",
    "LibraryCollectionImportResolution",
    "LibraryCollectionImportResult",
    "LibraryCollectionImportService",
    "LibraryImportCandidate",
    "LibraryImportEntry",
    "LibraryImportMode",
    "LibraryImportResolution",
]
