import json

from pypost.core.storage import StorageManager
from pypost.models.models import Collection, RequestData


def _make_storage(tmp_path, monkeypatch) -> StorageManager:
    monkeypatch.setattr(
        "pypost.core.storage.user_data_dir",
        lambda app_name, app_author: str(tmp_path / "pypost-data"),
    )
    return StorageManager()


def test_save_collection_uses_collection_id_as_filename(tmp_path, monkeypatch):
    storage = _make_storage(tmp_path, monkeypatch)
    collection = Collection(id="col-uuid-1", name="My API", requests=[])

    storage.save_collection(collection)

    id_path = storage.collections_path / "col-uuid-1.json"
    name_path = storage.collections_path / "My API.json"
    assert id_path.exists()
    assert not name_path.exists()
    with open(id_path, "r") as f:
        data = json.load(f)
    assert data["id"] == "col-uuid-1"
    assert data["name"] == "My API"


def test_rename_collection_does_not_change_filename(tmp_path, monkeypatch):
    storage = _make_storage(tmp_path, monkeypatch)
    collection = Collection(id="col-uuid-2", name="Original", requests=[])
    storage.save_collection(collection)

    collection.name = "Renamed"
    storage.save_collection(collection)

    assert (storage.collections_path / "col-uuid-2.json").exists()
    assert not (storage.collections_path / "Original.json").exists()
    assert not (storage.collections_path / "Renamed.json").exists()


def test_load_collections_migrates_legacy_name_based_files(tmp_path, monkeypatch):
    storage = _make_storage(tmp_path, monkeypatch)
    collection = Collection(
        id="legacy-id-1",
        name="Legacy Name",
        requests=[RequestData(id="r1", name="Req")],
    )
    legacy_path = storage.collections_path / "Legacy Name.json"
    with open(legacy_path, "w") as f:
        f.write(collection.model_dump_json(indent=2))

    loaded = storage.load_collections()

    assert len(loaded) == 1
    assert loaded[0].id == "legacy-id-1"
    assert (storage.collections_path / "legacy-id-1.json").exists()
    assert not legacy_path.exists()


def test_same_display_name_collections_persist_as_separate_files(tmp_path, monkeypatch):
    storage = _make_storage(tmp_path, monkeypatch)
    c1 = Collection(id="id-1", name="Shared Name", requests=[])
    c2 = Collection(id="id-2", name="Shared Name", requests=[])

    storage.save_collection(c1)
    storage.save_collection(c2)

    loaded = storage.load_collections()
    assert len(loaded) == 2
    assert {col.id for col in loaded} == {"id-1", "id-2"}


def test_delete_collection_removes_id_based_file(tmp_path, monkeypatch):
    storage = _make_storage(tmp_path, monkeypatch)
    collection = Collection(id="del-id-1", name="To Delete", requests=[])
    storage.save_collection(collection)

    storage.delete_collection("del-id-1", collection_name="To Delete")

    assert not (storage.collections_path / "del-id-1.json").exists()
