import json

import pytest

from pypost.core.storage import StorageManager
from pypost.models.models import Collection


@pytest.fixture
def storage(tmp_path, monkeypatch):
    monkeypatch.setattr("pypost.core.storage.user_data_dir", lambda *_: str(tmp_path))
    return StorageManager()


def test_collections_with_duplicate_names_are_stored_separately(storage):
    first = Collection(id="first", name="Shared", requests=[])
    second = Collection(id="second", name="Shared", requests=[])

    storage.save_collection(first)
    storage.save_collection(second)

    files = list(storage.collections_path.glob("*.json"))
    assert len(files) == 2
    assert {item.id for item in storage.load_collections()} == {"first", "second"}


def test_collection_name_cannot_escape_storage_directory(storage, tmp_path):
    collection = Collection(id="safe-id", name="../../outside", requests=[])

    storage.save_collection(collection)

    assert not (tmp_path / "outside.json").exists()
    assert len(list(storage.collections_path.glob("*.json"))) == 1


def test_saving_loaded_legacy_collection_migrates_its_filename(storage):
    legacy_file = storage.collections_path / "Legacy Name.json"
    collection = Collection(id="legacy-id", name="Legacy Name", requests=[])
    legacy_file.write_text(collection.model_dump_json(), encoding="utf-8")

    loaded = storage.load_collections()[0]
    loaded.name = "Renamed"
    storage.save_collection(loaded)

    assert not legacy_file.exists()
    files = list(storage.collections_path.glob("*.json"))
    assert len(files) == 1
    assert json.loads(files[0].read_text(encoding="utf-8"))["name"] == "Renamed"


def test_delete_loaded_legacy_collection_removes_its_file(storage):
    legacy_file = storage.collections_path / "Legacy Name.json"
    collection = Collection(id="legacy-id", name="Legacy Name", requests=[])
    legacy_file.write_text(collection.model_dump_json(), encoding="utf-8")
    loaded = storage.load_collections()[0]

    storage.delete_collection(loaded)

    assert not legacy_file.exists()


def test_failed_replace_keeps_previous_collection_file(storage, monkeypatch):
    collection = Collection(id="collection-id", name="Before", requests=[])
    storage.save_collection(collection)
    saved_file = next(storage.collections_path.glob("*.json"))
    original = saved_file.read_text(encoding="utf-8")
    collection.name = "After"

    def fail_replace(*_args):
        raise OSError("replace failed")

    monkeypatch.setattr("pypost.core.storage.os.replace", fail_replace)

    with pytest.raises(OSError, match="replace failed"):
        storage.save_collection(collection)

    assert saved_file.read_text(encoding="utf-8") == original
    assert not list(storage.collections_path.glob("*.tmp"))
