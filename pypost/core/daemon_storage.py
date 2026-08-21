from __future__ import annotations

import json
import logging
from pathlib import Path
from types import MappingProxyType
from typing import AbstractSet, Literal, Mapping, Protocol

from pydantic import ValidationError

from pypost.core.environment_variables_adapter import EnvironmentVariablesAdapter
from pypost.core.key_provider import EnvironmentEncryptionError
from pypost.models.models import Collection, Environment

logger = logging.getLogger(__name__)


class DaemonDataError(Exception):
    def __init__(
        self,
        kind: Literal["collections", "environments"],
        category: str,
        *,
        record_id: str | None = None,
        filename: str | None = None,
    ) -> None:
        self.kind = kind
        self.category = category
        self.record_id = record_id
        self.filename = filename
        details = f" record_id={record_id}" if record_id else ""
        if filename:
            details += f" filename={filename}"
        super().__init__(f"{kind} data failure category={category}{details}")


class _Storage(Protocol):
    data_dir: Path
    collections_path: Path
    environments_file: Path
    _env_adapter: EnvironmentVariablesAdapter

    def _ensure_paths(self) -> None:
        ...


def initialize_selected_paths(
    storage: _Storage,
    initialize_collections: bool,
    initialize_environments: bool,
) -> None:
    legacy_layout = (
        storage.collections_path.parent == storage.data_dir
        and storage.environments_file.parent == storage.data_dir
    )
    if initialize_collections and initialize_environments and legacy_layout:
        storage._ensure_paths()
        return
    if initialize_collections:
        storage.collections_path.mkdir(parents=True, exist_ok=True)
    if initialize_environments:
        storage.environments_file.parent.mkdir(parents=True, exist_ok=True)
        if not storage.environments_file.exists():
            storage.environments_file.write_text("[]", encoding="utf-8")


def load_collections_snapshot_strict(
    storage: _Storage,
    required_ids: AbstractSet[str],
) -> Mapping[str, Collection]:
    if not storage.collections_path.is_dir():
        raise DaemonDataError("collections", "store_unavailable")
    if not required_ids:
        return MappingProxyType({})
    found: dict[str, Collection] = {}
    skipped = 0
    try:
        candidates = tuple(storage.collections_path.glob("*.json"))
    except OSError as exc:
        raise DaemonDataError("collections", "store_unreadable") from exc
    for candidate in candidates:
        raw_id: object = None
        try:
            data = json.loads(candidate.read_text(encoding="utf-8"))
            raw_id = data.get("id") if isinstance(data, dict) else None
            collection = Collection.model_validate(data)
        except (OSError, json.JSONDecodeError, ValidationError, TypeError, ValueError) as exc:
            required_id = (
                raw_id
                if isinstance(raw_id, str) and raw_id in required_ids
                else candidate.stem
            )
            if required_id in required_ids:
                if skipped:
                    logger.warning(
                        "daemon_storage_records_skipped kind=collections count=%d",
                        skipped,
                    )
                raise DaemonDataError(
                    "collections",
                    "invalid_record",
                    record_id=required_id,
                    filename=candidate.name,
                ) from exc
            skipped += 1
            continue
        if collection.id not in required_ids:
            continue
        if collection.id in found:
            raise DaemonDataError("collections", "duplicate_id", record_id=collection.id)
        found[collection.id] = collection.model_copy(deep=True)
    if skipped:
        logger.warning(
            "daemon_storage_records_skipped kind=collections count=%d", skipped
        )
    missing = sorted(set(required_ids).difference(found))
    if missing:
        raise DaemonDataError("collections", "missing", record_id=missing[0])
    return MappingProxyType(found)


def load_environments_snapshot_strict(
    storage: _Storage,
    required_ids: AbstractSet[str],
) -> Mapping[str, Environment]:
    if not storage.environments_file.is_file():
        raise DaemonDataError("environments", "store_unavailable")
    if not required_ids:
        return MappingProxyType({})
    try:
        records = json.loads(storage.environments_file.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise DaemonDataError("environments", "store_unreadable") from exc
    if not isinstance(records, list):
        raise DaemonDataError("environments", "invalid_store")
    found: dict[str, Environment] = {}
    skipped = 0
    for record in records:
        raw_id = record.get("id") if isinstance(record, dict) else None
        try:
            environment = storage._env_adapter.deserialize_environment(record)
        except (
            EnvironmentEncryptionError,
            ValidationError,
            TypeError,
            ValueError,
        ) as exc:
            if raw_id in required_ids:
                if skipped:
                    logger.warning(
                        "daemon_storage_records_skipped kind=environments count=%d",
                        skipped,
                    )
                raise DaemonDataError(
                    "environments", "invalid_record", record_id=raw_id
                ) from exc
            skipped += 1
            continue
        if environment.id not in required_ids:
            continue
        if environment.id in found:
            raise DaemonDataError(
                "environments", "duplicate_id", record_id=environment.id
            )
        found[environment.id] = environment.model_copy(deep=True)
    if skipped:
        logger.warning(
            "daemon_storage_records_skipped kind=environments count=%d", skipped
        )
    missing = sorted(set(required_ids).difference(found))
    if missing:
        raise DaemonDataError("environments", "missing", record_id=missing[0])
    return MappingProxyType(found)
