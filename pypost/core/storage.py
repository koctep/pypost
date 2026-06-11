import json
import logging
import os
from pathlib import Path
from typing import TYPE_CHECKING, List

from platformdirs import user_data_dir

from pypost.core.environment_variables_adapter import EnvironmentVariablesAdapter
from pypost.models.models import Collection, Environment
from pypost.models.settings import AppSettings

if TYPE_CHECKING:
    from pypost.core.metrics import MetricsManager

logger = logging.getLogger(__name__)


class StorageManager:
    def __init__(
        self,
        app_name: str = "pypost",
        app_author=None,
        metrics: "MetricsManager | None" = None,
    ):
        self.data_dir = Path(user_data_dir(app_name, app_author))
        self.collections_path = self.data_dir / "collections"
        self.environments_file = self.data_dir / "environments.json"
        self._metrics = metrics
        self._env_adapter = EnvironmentVariablesAdapter(metrics=metrics)
        self._ensure_paths()

    def apply_encryption_settings(self, settings: AppSettings | None) -> None:
        self._env_adapter.apply_encryption_settings(settings)

    def _ensure_paths(self):
        if not self.data_dir.exists():
            try:
                self.data_dir.mkdir(parents=True, exist_ok=True)
            except Exception as e:
                logger.error("storage_data_dir_create_failed path=%s error=%s", self.data_dir, e)

        if not self.collections_path.exists():
            try:
                self.collections_path.mkdir(exist_ok=True)
            except Exception as e:
                logger.error(
                    "storage_collections_dir_create_failed path=%s error=%s",
                    self.collections_path,
                    e,
                )

        if not self.environments_file.exists():
            try:
                with open(self.environments_file, "w") as f:
                    json.dump([], f)
            except Exception as e:
                logger.error(
                    "storage_environments_file_create_failed path=%s error=%s",
                    self.environments_file,
                    e,
                )

    def _collection_path_by_id(self, collection_id: str) -> Path:
        return self.collections_path / f"{collection_id}.json"

    @staticmethod
    def _is_legacy_name_file(filename: str, collection: Collection) -> bool:
        stem = Path(filename).stem
        return stem == collection.name and stem != collection.id

    def save_collection(self, collection: Collection):
        if not self.collections_path.exists():
            self.collections_path.mkdir(exist_ok=True, parents=True)

        file_path = self._collection_path_by_id(collection.id)
        with open(file_path, "w") as f:
            f.write(collection.model_dump_json(indent=2))

        legacy_path = self.collections_path / f"{collection.name}.json"
        if legacy_path.exists() and legacy_path != file_path:
            legacy_path.unlink()
            logger.info(
                "storage_collection_legacy_file_removed collection_id=%s path=%s",
                collection.id,
                legacy_path,
            )

    def delete_collection(self, collection_id: str, *, collection_name: str | None = None):
        id_path = self._collection_path_by_id(collection_id)
        if id_path.exists():
            id_path.unlink()

        if collection_name:
            legacy_path = self.collections_path / f"{collection_name}.json"
            if legacy_path.exists():
                legacy_path.unlink()

    def _migrate_legacy_collection_file(self, legacy_filename: str, collection: Collection) -> None:
        legacy_path = self.collections_path / legacy_filename
        id_path = self._collection_path_by_id(collection.id)
        if not id_path.exists():
            with open(id_path, "w") as f:
                f.write(collection.model_dump_json(indent=2))
        legacy_path.unlink(missing_ok=True)
        logger.info(
            "storage_collection_migrated collection_id=%s legacy=%s",
            collection.id,
            legacy_filename,
        )

    def load_collections(self) -> List[Collection]:
        collections = []
        if not self.collections_path.exists():
            return collections

        for filename in os.listdir(self.collections_path):
            if not filename.endswith(".json"):
                continue
            try:
                with open(self.collections_path / filename, "r") as f:
                    data = json.load(f)
                    collection = Collection(**data)
                    collections.append(collection)
                    if self._is_legacy_name_file(filename, collection):
                        self._migrate_legacy_collection_file(filename, collection)
            except Exception as e:
                logger.warning(
                    "storage_collection_load_failed filename=%s error=%s",
                    filename,
                    e,
                )
        return collections

    def save_environments(self, environments: List[Environment]):
        data = [self._env_adapter.serialize_environment(env) for env in environments]
        tmp_file = self.environments_file.with_suffix(".json.tmp")
        with open(tmp_file, "w") as f:
            json.dump(data, f, indent=2)
        try:
            os.replace(tmp_file, self.environments_file)
        except Exception as e:
            logger.error(
                "save_environments_replace_failed src=%s dst=%s error=%s",
                tmp_file,
                self.environments_file,
                e,
            )
            if tmp_file.exists():
                tmp_file.unlink(missing_ok=True)
            raise
        logger.info(
            "save_environments_completed count=%d file=%s",
            len(environments),
            self.environments_file,
        )

    def load_environments(self) -> List[Environment]:
        if not self.environments_file.exists():
            return []
        try:
            with open(self.environments_file, "r") as f:
                data = json.load(f)
                environments = [
                    self._env_adapter.deserialize_environment(item) for item in data
                ]
                logger.info(
                    "load_environments_completed count=%d file=%s",
                    len(environments),
                    self.environments_file,
                )
                return environments
        except Exception as e:
            logger.error(
                "load_environments_failed file=%s error=%s",
                self.environments_file,
                e,
            )
            return []
