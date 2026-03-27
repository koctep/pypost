import os
import json
import logging
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

    def save_collection(self, collection: Collection):
        # Ensure collections directory exists before saving (in case it was deleted)
        if not self.collections_path.exists():
            self.collections_path.mkdir(exist_ok=True, parents=True)

        # Simplification: using collection name as filename.
        file_path = self.collections_path / f"{collection.name}.json"
        with open(file_path, 'w') as f:
            f.write(collection.model_dump_json(indent=2))

    def delete_collection(self, collection_name: str):
        file_path = self.collections_path / f"{collection_name}.json"
        if file_path.exists():
            file_path.unlink()

    def load_collections(self) -> List[Collection]:
        collections = []
        if not self.collections_path.exists():
            return collections

        for filename in os.listdir(self.collections_path):
            if filename.endswith(".json"):
                try:
                    with open(self.collections_path / filename, 'r') as f:
                        data = json.load(f)
                        collections.append(Collection(**data))
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
