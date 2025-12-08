import os
import json
from typing import List, Optional
from pypost.models.models import Collection, Environment

class StorageManager:
    def __init__(self, base_path: str = "."):
        self.collections_path = os.path.join(base_path, "collections")
        self.environments_file = os.path.join(base_path, "environments.json")
        self._ensure_paths()

    def _ensure_paths(self):
        if not os.path.exists(self.collections_path):
            os.makedirs(self.collections_path)
        if not os.path.exists(self.environments_file):
            with open(self.environments_file, 'w') as f:
                json.dump([], f)

    def save_collection(self, collection: Collection):
        file_path = os.path.join(self.collections_path, f"{collection.name}.json") # Simplification: using name as filename
        with open(file_path, 'w') as f:
            f.write(collection.model_dump_json(indent=2))

    def load_collections(self) -> List[Collection]:
        collections = []
        if not os.path.exists(self.collections_path):
            return collections

        for filename in os.listdir(self.collections_path):
            if filename.endswith(".json"):
                try:
                    with open(os.path.join(self.collections_path, filename), 'r') as f:
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
        if not os.path.exists(self.environments_file):
            return []
        try:
            with open(self.environments_file, 'r') as f:
                data = json.load(f)
                return [Environment(**item) for item in data]
        except Exception as e:
            print(f"Error loading environments: {e}")
            return []
