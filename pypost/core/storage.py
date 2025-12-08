import os
import json
from pathlib import Path
from typing import List, Optional
from platformdirs import user_data_dir
from pypost.models.models import Collection, Environment

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
                print(f"Error creating data directory: {e}")

        if not self.collections_path.exists():
            try:
                self.collections_path.mkdir(exist_ok=True)
            except Exception as e:
                print(f"Error creating collections directory: {e}")
                
        if not self.environments_file.exists():
            try:
                with open(self.environments_file, 'w') as f:
                    json.dump([], f)
            except Exception as e:
                 print(f"Error creating environments file: {e}")

    def save_collection(self, collection: Collection):
        # Ensure collections directory exists before saving (in case it was deleted)
        if not self.collections_path.exists():
             self.collections_path.mkdir(exist_ok=True, parents=True)

        file_path = self.collections_path / f"{collection.name}.json" # Simplification: using name as filename
        with open(file_path, 'w') as f:
            f.write(collection.model_dump_json(indent=2))

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
                    print(f"Error loading collection {filename}: {e}")
        return collections

    def save_environments(self, environments: List[Environment]):
        data = [env.model_dump() for env in environments]
        with open(self.environments_file, 'w') as f:
            json.dump(data, f, indent=2)

    def load_environments(self) -> List[Environment]:
        if not self.environments_file.exists():
            return []
        try:
            with open(self.environments_file, 'r') as f:
                data = json.load(f)
                return [Environment(**item) for item in data]
        except Exception as e:
            print(f"Error loading environments: {e}")
            return []
