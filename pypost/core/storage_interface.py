"""Protocol for collection and environment persistence."""

from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING, List, Protocol, runtime_checkable

from pypost.core.environment_variables_adapter import EnvironmentSerializeStats
from pypost.models.models import Collection, Environment
from pypost.models.settings import AppSettings

if TYPE_CHECKING:
    from pypost.core.storage import EnvironmentLoadFailure


@runtime_checkable
class StorageInterface(Protocol):
    """Collections and environments persistence — consumed by managers and presenters."""

    environments_file: Path

    def apply_encryption_settings(self, settings: AppSettings | None) -> None: ...

    def save_collection(self, collection: Collection) -> None: ...

    def delete_collection(
        self, collection_id: str, *, collection_name: str | None = None
    ) -> None: ...

    def load_collections(self) -> List[Collection]: ...

    def save_environments(
        self,
        environments: List[Environment],
        *,
        target_envelope_version: int | None = None,
    ) -> EnvironmentSerializeStats: ...

    def project_save_stats(
        self,
        environments: List[Environment],
        *,
        target_envelope_version: int | None = None,
    ) -> EnvironmentSerializeStats: ...

    def load_environments(self) -> List[Environment]: ...

    def load_environments_with_errors(
        self,
    ) -> tuple[list[Environment], tuple[EnvironmentLoadFailure, ...]]: ...

    def deserialize_environment_records(
        self,
        records: list[dict],
    ) -> tuple[list[Environment], tuple[EnvironmentLoadFailure, ...]]: ...

    def serialize_environment_records(
        self,
        environments: List[Environment],
        *,
        target_envelope_version: int | None = None,
    ) -> list[dict]: ...
