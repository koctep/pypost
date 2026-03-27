import json

import pytest
from pypost.core.storage import StorageManager
from pypost.models.models import Environment


def _make_storage(tmp_path, monkeypatch) -> StorageManager:
    monkeypatch.setattr(
        "pypost.core.storage.user_data_dir",
        lambda app_name, app_author: str(tmp_path / "pypost-data"),
    )
    return StorageManager()


def test_save_environments_serializes_hidden_keys_as_json_list(tmp_path, monkeypatch):
    storage = _make_storage(tmp_path, monkeypatch)
    env = Environment(
        name="Dev",
        variables={"API_KEY": "secret"},
        hidden_keys={"API_KEY"},
    )

    storage.save_environments([env])

    with open(storage.environments_file, "r") as f:
        data = json.load(f)
    assert data[0]["hidden_keys"] == ["API_KEY"]


def test_load_environments_restores_hidden_keys_to_set(tmp_path, monkeypatch):
    storage = _make_storage(tmp_path, monkeypatch)
    payload = [
        {
            "id": "e1",
            "name": "Dev",
            "variables": {"TOKEN": "abc"},
            "hidden_keys": ["TOKEN"],
            "enable_mcp": False,
        }
    ]
    with open(storage.environments_file, "w") as f:
        json.dump(payload, f)

    environments = storage.load_environments()

    assert len(environments) == 1
    assert environments[0].hidden_keys == {"TOKEN"}


def test_save_environments_replace_failure_keeps_original_file(tmp_path, monkeypatch):
    storage = _make_storage(tmp_path, monkeypatch)
    original_payload = [
        {
            "id": "e0",
            "name": "Orig",
            "variables": {"A": "1"},
            "hidden_keys": [],
            "enable_mcp": False,
        }
    ]
    with open(storage.environments_file, "w") as f:
        json.dump(original_payload, f)

    env = Environment(
        name="Dev",
        variables={"API_KEY": "secret"},
        hidden_keys={"API_KEY"},
    )

    def _raise_replace(_src, _dst):
        raise OSError("replace failed")

    monkeypatch.setattr("pypost.core.storage.os.replace", _raise_replace)

    with pytest.raises(OSError, match="replace failed"):
        storage.save_environments([env])

    with open(storage.environments_file, "r") as f:
        reloaded = json.load(f)
    assert reloaded == original_payload
    assert not storage.environments_file.with_suffix(".json.tmp").exists()
