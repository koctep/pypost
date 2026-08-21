"""Shared test helpers for PyPost unit tests."""

from collections.abc import Mapping, Sequence
from pathlib import Path
from typing import Any

from pydantic import ValidationError

from pypost.core.environment_variables_adapter import EnvironmentSerializeStats
from pypost.core.storage import EnvironmentLoadFailure
from pypost.models.models import Environment


class FakeStorageManager:
    def __init__(self, collections=None):
        self._collections = collections or []
        self.saved_collections: list = []  # Collection instances (see save_collection)
        self.deleted_collection_ids: list = []
        self.environments_file = Path("/tmp/fake-environments.json")
        self.saved_environments: list = []

    def seed_collections(self, collections):
        """Simulate persisted data changing between load_collections() calls (tests only)."""
        self._collections = list(collections) if collections else []

    def apply_encryption_settings(self, settings=None) -> None:
        pass

    def load_collections(self):
        return list(self._collections)

    def save_collection(self, collection):
        self.saved_collections.append(collection)

    def delete_collection(self, collection_id: str, *, collection_name: str | None = None):
        self.deleted_collection_ids.append(collection_id)

    def save_environments(
        self,
        environments,
        *,
        target_envelope_version=None,
    ) -> EnvironmentSerializeStats:
        self.saved_environments = list(environments)
        return EnvironmentSerializeStats()

    def project_save_stats(
        self,
        environments,
        *,
        target_envelope_version=None,
    ) -> EnvironmentSerializeStats:
        return EnvironmentSerializeStats()

    def load_environments(self):
        return []

    def load_environments_with_errors(self):
        return [], ()

    def deserialize_environment_records(
        self,
        records: Sequence[Mapping[str, Any]] | list[dict],
    ) -> tuple[list[Environment], tuple[EnvironmentLoadFailure, ...]]:
        """Deserialize in-memory environment JSON records in plaintext for tests (PYPOST-1060)."""
        environments: list[Environment] = []
        failures: list[EnvironmentLoadFailure] = []

        for item in records:
            if not isinstance(item, (dict, Mapping)):
                failures.append(
                    EnvironmentLoadFailure(
                        name="unknown",
                        environment_id=None,
                        reason=f"Record is not a mapping: {type(item).__name__}",
                    )
                )
                continue

            env_name = str(item.get("name", "unknown"))
            raw_id = item.get("id")
            environment_id = raw_id if isinstance(raw_id, str) else None

            try:
                env = Environment.model_validate(item)
                environments.append(env)
            except ValidationError as exc:
                failures.append(
                    EnvironmentLoadFailure(
                        name=env_name,
                        environment_id=environment_id,
                        reason=str(exc),
                    )
                )
            except Exception as exc:  # noqa: BLE001
                failures.append(
                    EnvironmentLoadFailure(
                        name=env_name,
                        environment_id=environment_id,
                        reason=str(exc),
                    )
                )

        return environments, tuple(failures)

    def serialize_environment_records(
        self,
        environments,
        *,
        target_envelope_version=None,
    ):
        return [env.model_dump(mode="json") for env in environments]
