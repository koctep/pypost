"""Shared test helpers for PyPost unit tests."""

from pathlib import Path

from pypost.core.environment_variables_adapter import EnvironmentSerializeStats


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

    def deserialize_environment_records(self, records):
        return [], ()
