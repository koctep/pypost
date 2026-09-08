import os
import json
import logging
import hashlib
from pathlib import Path
from typing import List
from platformdirs import user_data_dir
from pypost.models.models import Collection, Environment

logger = logging.getLogger(__name__)


class StorageManager:
    def __init__(self, app_name="pypost", app_author=None):
        self.data_dir = Path(user_data_dir(app_name, app_author))
        self.collections_path = self.data_dir / "collections"
        self.environments_file = self.data_dir / "environments.json"
        self._collection_files: dict[str, Path] = {}
        self._ensure_paths()

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
                with open(self.environments_file, 'w') as f:
                    json.dump([], f)
            except Exception as e:
                logger.error(
                    "storage_environments_file_create_failed path=%s error=%s",
                    self.environments_file,
                    e,
                )

    def _collection_file(self, collection_id: str) -> Path:
        """Return a stable filename without exposing model data as a path."""
        digest = hashlib.sha256(collection_id.encode("utf-8")).hexdigest()
        return self.collections_path / f"{digest}.json"

    def save_collection(self, collection: Collection):
        # Ensure collections directory exists before saving (in case it was deleted)
        if not self.collections_path.exists():
            self.collections_path.mkdir(exist_ok=True, parents=True)

        file_path = self._collection_file(collection.id)
        tmp_file = file_path.with_suffix(".json.tmp")
        with open(tmp_file, 'w') as f:
            f.write(collection.model_dump_json(indent=2))
        try:
            os.replace(tmp_file, file_path)
        except Exception:
            tmp_file.unlink(missing_ok=True)
            raise

        previous_file = self._collection_files.get(collection.id)
        if previous_file is not None and previous_file != file_path:
            previous_file.unlink(missing_ok=True)
        self._collection_files[collection.id] = file_path

    def delete_collection(self, collection: Collection):
        file_path = self._collection_files.pop(
            collection.id, self._collection_file(collection.id)
        )
        file_path.unlink(missing_ok=True)

    def load_collections(self) -> List[Collection]:
        collections = []
        self._collection_files.clear()
        if not self.collections_path.exists():
            return collections

        for filename in os.listdir(self.collections_path):
            if filename.endswith(".json"):
                try:
                    with open(self.collections_path / filename, 'r') as f:
                        data = json.load(f)
                        collection = Collection(**data)
                        collections.append(collection)
                        self._collection_files[collection.id] = (
                            self.collections_path / filename
                        )
                except Exception as e:
                    logger.warning(
                        "storage_collection_load_failed filename=%s error=%s",
                        filename,
                        e,
                    )
        return collections

    def save_environments(self, environments: List[Environment]):
        # Use JSON mode so non-JSON-native types (e.g. set) are serialized safely.
        data = [env.model_dump(mode="json") for env in environments]
        tmp_file = self.environments_file.with_suffix(".json.tmp")
        with open(tmp_file, 'w') as f:
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
            with open(self.environments_file, 'r') as f:
                data = json.load(f)
                environments = [Environment(**item) for item in data]
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
