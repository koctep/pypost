"""Durable registry for clone and in-place library connections."""
from __future__ import annotations

import json
import os
import tempfile
from pathlib import Path
from typing import Optional

from pypost.core.git_service import sanitize_git_url
from pypost.core.library_manifest import MANIFEST_CANDIDATE_NAMES
from pypost.models.library_manager import LibraryConnectionRecord, LibrarySourceType


class LibraryConnectionStore:
    """Persist connection metadata separately from library and overlay contents."""

    def __init__(
        self,
        path: Optional[Path | str] = None,
        legacy_base_dir: Optional[Path | str] = None,
    ) -> None:
        self.path = Path(path or Path.home() / ".pypost" / "library_connections.json")
        self.legacy_base_dir = Path(legacy_base_dir) if legacy_base_dir else None
        self.diagnostics: list[str] = []
        self._disconnected_legacy: set[tuple[str, Optional[Path]]] = set()

    def load(self, legacy_base_dir: Optional[Path | str] = None) -> list[LibraryConnectionRecord]:
        """Load valid records and merge clone directories from the legacy location."""
        self.diagnostics = []
        self._disconnected_legacy = set()
        records: list[LibraryConnectionRecord] = []
        if self.path.is_file():
            try:
                payload = json.loads(self.path.read_text(encoding="utf-8"))
                raw_records = (
                    payload.get("connections", payload)
                    if isinstance(payload, dict)
                    else payload
                )
                if not isinstance(raw_records, list):
                    raise ValueError("connection registry must contain a list")
                if isinstance(payload, dict):
                    self._load_disconnected(payload.get("disconnected", []))
                for raw in raw_records:
                    try:
                        records.append(LibraryConnectionRecord.model_validate(raw))
                    except Exception:
                        self.diagnostics.append("A connection record could not be read.")
            except (OSError, ValueError, json.JSONDecodeError):
                self.diagnostics.append("The library connection registry could not be read.")
        base_dir = Path(legacy_base_dir) if legacy_base_dir else self.legacy_base_dir
        if base_dir:
            records.extend(self._legacy_records(base_dir, records))
        return records

    def _load_disconnected(self, values: object) -> None:
        """Load legacy-disconnect tombstones without exposing registry errors."""
        if not isinstance(values, list):
            return
        for value in values:
            if isinstance(value, str):
                self._disconnected_legacy.add((value, None))
            elif isinstance(value, dict) and isinstance(value.get("stable_id"), str):
                raw_path = value.get("canonical_path", "")
                path = (
                    Path(raw_path).expanduser().resolve(strict=False)
                    if isinstance(raw_path, str) and raw_path
                    else None
                )
                self._disconnected_legacy.add((value["stable_id"], path))

    def _legacy_records(
        self, base_dir: Path, existing: list[LibraryConnectionRecord]
    ) -> list[LibraryConnectionRecord]:
        if not base_dir.is_dir():
            return []
        known_paths = {record.canonical_path for record in existing}
        known_ids = {record.stable_id for record in existing}
        found: list[LibraryConnectionRecord] = []
        for child in sorted(base_dir.iterdir(), key=lambda item: item.name.casefold()):
            has_manifest = any((child / name).is_file() for name in MANIFEST_CANDIDATE_NAMES)
            if not child.is_dir() or child.name.startswith(".") or not (
                (child / ".git").exists() or has_manifest
            ):
                continue
            record = LibraryConnectionRecord(
                stable_id=child.name,
                local_path=child,
                source_type=LibrarySourceType.CLONED,
            )
            if any(
                stable_id == record.stable_id
                and (not ignored_path or ignored_path == record.canonical_path)
                for stable_id, ignored_path in self._disconnected_legacy
            ):
                continue
            if record.stable_id in known_ids:
                self.diagnostics.append("A legacy library identity conflicts with a connection.")
                continue
            if record.canonical_path not in known_paths:
                found.append(record)
                known_paths.add(record.canonical_path)
                known_ids.add(record.stable_id)
        return found

    def save(self, records: list[LibraryConnectionRecord]) -> None:
        """Atomically save records and create only the registry parent directory."""
        self.path.parent.mkdir(parents=True, exist_ok=True)
        connection_payloads: list[dict[str, object]] = []
        for record in records:
            payload = record.model_dump(mode="json")
            remote_url = payload.get("remote_url")
            if isinstance(remote_url, str):
                payload["remote_url"] = sanitize_git_url(remote_url)
            connection_payloads.append(payload)
        payload = {
            "connections": connection_payloads,
            "disconnected": [
                {"stable_id": stable_id, "canonical_path": str(path) if path else None}
                for stable_id, path in sorted(
                    self._disconnected_legacy, key=lambda item: (item[0], str(item[1] or ""))
                )
            ],
        }
        fd, temporary = tempfile.mkstemp(prefix=f"{self.path.name}.", dir=self.path.parent)
        try:
            with os.fdopen(fd, "w", encoding="utf-8") as stream:
                json.dump(payload, stream, indent=2)
            os.replace(temporary, self.path)
        finally:
            temporary_path = Path(temporary)
            if temporary_path.exists():
                temporary_path.unlink()

    def add(self, record: LibraryConnectionRecord) -> LibraryConnectionRecord:
        """Add a record unless its path or declared manifest identity is already present."""
        records = self.load()
        if any(item.stable_id == record.stable_id for item in records):
            raise ValueError("A library with this identity is already connected.")
        if any(item.canonical_path == record.canonical_path for item in records):
            raise ValueError("This local directory is already connected.")
        if record.manifest_id and any(item.manifest_id == record.manifest_id for item in records):
            raise ValueError("A library with this identity is already connected.")
        self._disconnected_legacy = {
            item
            for item in self._disconnected_legacy
            if item[0] != record.stable_id and item[1] != record.canonical_path
        }
        records.append(record)
        self.save(records)
        return record

    def remove(self, stable_id: str) -> bool:
        """Remove one metadata record without deleting its local path."""
        records = self.load()
        removed = next((record for record in records if record.stable_id == stable_id), None)
        remaining = [record for record in records if record.stable_id != stable_id]
        if removed is None:
            return False
        base_dir = self.legacy_base_dir.resolve(strict=False) if self.legacy_base_dir else None
        if base_dir is not None:
            try:
                removed.canonical_path.relative_to(base_dir)
            except ValueError:
                pass
            else:
                self._disconnected_legacy.add((removed.stable_id, removed.canonical_path))
        self.save(remaining)
        return True

    def update(self, record: LibraryConnectionRecord) -> LibraryConnectionRecord:
        """Replace one record after applying the same duplicate checks as add."""
        records = self.load()
        remaining = [item for item in records if item.stable_id != record.stable_id]
        if any(item.canonical_path == record.canonical_path for item in remaining):
            raise ValueError("This local directory is already connected.")
        if any(item.stable_id == record.stable_id for item in remaining):
            raise ValueError("A library with this identity is already connected.")
        if record.manifest_id and any(item.manifest_id == record.manifest_id for item in remaining):
            raise ValueError("A library with this identity is already connected.")
        self.save(remaining + [record])
        return record


__all__ = ["LibraryConnectionStore"]
