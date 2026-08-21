import json
import logging

import pytest

from pypost.core.daemon_storage import DaemonDataError
from pypost.core.key_provider import EnvironmentEncryptionError
from pypost.core.storage import StorageManager
from pypost.models.models import Collection, Environment

pytestmark = pytest.mark.timeout(30)


def test_daemon_storage_uses_independent_directories_without_initializing(tmp_path):
    collections_dir = tmp_path / "collections"
    environments_dir = tmp_path / "environments"
    collections_dir.mkdir()
    environments_dir.mkdir()

    storage = StorageManager(
        data_dir=tmp_path / "unused",
        collections_dir=collections_dir,
        environments_dir=environments_dir,
        initialize_collections=False,
        initialize_environments=False,
    )

    assert storage.collections_path == collections_dir
    assert storage.environments_file == environments_dir / "environments.json"
    assert not storage.environments_file.exists()


def test_strict_snapshots_return_only_required_records(tmp_path):
    collections_dir = tmp_path / "collections"
    environments_dir = tmp_path / "environments"
    collections_dir.mkdir()
    environments_dir.mkdir()
    required_collection = Collection(id="required", name="Required")
    other_collection = Collection(id="other", name="Other")
    (collections_dir / "required.json").write_text(required_collection.model_dump_json())
    (collections_dir / "other.json").write_text(other_collection.model_dump_json())
    environments = [Environment(id="required-env"), Environment(id="other-env")]
    (environments_dir / "environments.json").write_text(
        json.dumps([environment.model_dump(mode="json") for environment in environments])
    )
    storage = StorageManager(
        collections_dir=collections_dir,
        environments_dir=environments_dir,
        initialize_collections=False,
        initialize_environments=False,
    )

    assert list(storage.load_collections_snapshot_strict(required_ids={"required"})) == [
        "required"
    ]
    assert list(
        storage.load_environments_snapshot_strict(required_ids={"required-env"})
    ) == ["required-env"]


def test_strict_snapshot_reports_missing_required_id(tmp_path):
    collections_dir = tmp_path / "collections"
    environments_dir = tmp_path / "environments"
    collections_dir.mkdir()
    environments_dir.mkdir()
    (environments_dir / "environments.json").write_text("[]")
    storage = StorageManager(
        collections_dir=collections_dir,
        environments_dir=environments_dir,
        initialize_collections=False,
        initialize_environments=False,
    )

    with pytest.raises(DaemonDataError, match=r"collections.*missing.*record_id=absent"):
        storage.load_collections_snapshot_strict(required_ids={"absent"})


def test_malformed_legacy_named_collection_preserves_required_id(tmp_path):
    collections_dir = tmp_path / "collections"
    environments_dir = tmp_path / "environments"
    collections_dir.mkdir()
    environments_dir.mkdir()
    (collections_dir / "legacy-safe-name.json").write_text(
        json.dumps({"id": "required", "name": None}), encoding="utf-8"
    )
    (environments_dir / "environments.json").write_text("[]", encoding="utf-8")
    storage = StorageManager(
        collections_dir=collections_dir,
        environments_dir=environments_dir,
        initialize_collections=False,
        initialize_environments=False,
    )

    with pytest.raises(DaemonDataError) as raised:
        storage.load_collections_snapshot_strict(required_ids={"required"})

    assert raised.value.category == "invalid_record"
    assert raised.value.record_id == "required"
    assert raised.value.filename == "legacy-safe-name.json"


@pytest.mark.parametrize("variables", [1, ["malformed"]])
def test_malformed_environment_variables_are_typed_data_errors(tmp_path, variables):
    collections_dir = tmp_path / "collections"
    environments_dir = tmp_path / "environments"
    collections_dir.mkdir()
    environments_dir.mkdir()
    (environments_dir / "environments.json").write_text(
        json.dumps([{"id": "required-env", "variables": variables}]),
        encoding="utf-8",
    )
    storage = StorageManager(
        collections_dir=collections_dir,
        environments_dir=environments_dir,
        initialize_collections=False,
        initialize_environments=False,
    )

    with pytest.raises(DaemonDataError) as raised:
        storage.load_environments_snapshot_strict(required_ids={"required-env"})

    assert raised.value.category == "invalid_record"
    assert raised.value.record_id == "required-env"


def test_strict_collection_snapshot_rejects_malformed_json(tmp_path):
    collections_dir = tmp_path / "collections"
    environments_dir = tmp_path / "environments"
    collections_dir.mkdir()
    environments_dir.mkdir()
    (collections_dir / "required.json").write_text("{", encoding="utf-8")
    (environments_dir / "environments.json").write_text("[]", encoding="utf-8")
    storage = StorageManager(
        collections_dir=collections_dir,
        environments_dir=environments_dir,
        initialize_collections=False,
        initialize_environments=False,
    )

    with pytest.raises(DaemonDataError, match="invalid_record"):
        storage.load_collections_snapshot_strict(required_ids={"required"})


def test_strict_collection_snapshot_rejects_duplicate_ids_without_migration(tmp_path):
    collections_dir = tmp_path / "collections"
    environments_dir = tmp_path / "environments"
    collections_dir.mkdir()
    environments_dir.mkdir()
    payload = Collection(id="required", name="Required").model_dump_json()
    legacy_file = collections_dir / "legacy-name.json"
    legacy_file.write_text(payload, encoding="utf-8")
    (collections_dir / "other-name.json").write_text(payload, encoding="utf-8")
    (environments_dir / "environments.json").write_text("[]", encoding="utf-8")
    storage = StorageManager(
        collections_dir=collections_dir,
        environments_dir=environments_dir,
        initialize_collections=False,
        initialize_environments=False,
    )

    with pytest.raises(DaemonDataError, match="duplicate_id"):
        storage.load_collections_snapshot_strict(required_ids={"required"})

    assert legacy_file.exists()
    assert not (collections_dir / "required.json").exists()


def test_strict_environment_snapshot_translates_decryption_failure(
    monkeypatch, tmp_path
):
    collections_dir = tmp_path / "collections"
    environments_dir = tmp_path / "environments"
    collections_dir.mkdir()
    environments_dir.mkdir()
    (environments_dir / "environments.json").write_text(
        json.dumps([{"id": "required-env"}]), encoding="utf-8"
    )
    storage = StorageManager(
        collections_dir=collections_dir,
        environments_dir=environments_dir,
        initialize_collections=False,
        initialize_environments=False,
    )

    def fail_decryption(_record):
        raise EnvironmentEncryptionError("bad ciphertext")

    monkeypatch.setattr(
        storage._env_adapter, "deserialize_environment", fail_decryption
    )

    with pytest.raises(DaemonDataError) as raised:
        storage.load_environments_snapshot_strict(required_ids={"required-env"})

    assert raised.value.category == "invalid_record"
    assert raised.value.record_id == "required-env"


@pytest.mark.parametrize(
    ("records", "category"),
    [
        ([{"id": "required-env"}, {"id": "required-env"}], "duplicate_id"),
        ({"id": "required-env"}, "invalid_store"),
    ],
)
def test_strict_environment_snapshot_rejects_duplicate_or_invalid_store(
    tmp_path, records, category
):
    collections_dir = tmp_path / "collections"
    environments_dir = tmp_path / "environments"
    collections_dir.mkdir()
    environments_dir.mkdir()
    (environments_dir / "environments.json").write_text(
        json.dumps(records), encoding="utf-8"
    )
    storage = StorageManager(
        collections_dir=collections_dir,
        environments_dir=environments_dir,
        initialize_collections=False,
        initialize_environments=False,
    )

    with pytest.raises(DaemonDataError) as raised:
        storage.load_environments_snapshot_strict(required_ids={"required-env"})

    assert raised.value.category == category


def test_strict_snapshot_requires_explicit_environments_file(tmp_path):
    collections_dir = tmp_path / "collections"
    environments_dir = tmp_path / "environments"
    collections_dir.mkdir()
    environments_dir.mkdir()
    storage = StorageManager(
        collections_dir=collections_dir,
        environments_dir=environments_dir,
        initialize_collections=False,
        initialize_environments=False,
    )

    with pytest.raises(DaemonDataError) as raised:
        storage.load_environments_snapshot_strict(required_ids={"required-env"})

    assert raised.value.category == "store_unavailable"


def test_strict_collection_skips_are_count_only(caplog, tmp_path):
    collections_dir = tmp_path / "collections"
    environments_dir = tmp_path / "environments"
    collections_dir.mkdir()
    environments_dir.mkdir()
    secret = "credential-bearing-name"
    (collections_dir / f"{secret}.json").write_text("{", encoding="utf-8")
    (collections_dir / "another-private.json").write_text("[]", encoding="utf-8")
    (collections_dir / "required.json").write_text(
        Collection(id="required", name="Required").model_dump_json(), encoding="utf-8"
    )
    (environments_dir / "environments.json").write_text("[]", encoding="utf-8")
    storage = StorageManager(
        collections_dir=collections_dir,
        environments_dir=environments_dir,
        initialize_collections=False,
        initialize_environments=False,
    )

    with caplog.at_level(logging.WARNING, logger="pypost.core.daemon_storage"):
        storage.load_collections_snapshot_strict(required_ids={"required"})

    messages = [
        record.message
        for record in caplog.records
        if record.name == "pypost.core.daemon_storage"
    ]
    assert messages == [
        "daemon_storage_records_skipped kind=collections count=2"
    ]
    assert secret not in caplog.text


def test_strict_environment_skips_are_count_only(caplog, tmp_path):
    collections_dir = tmp_path / "collections"
    environments_dir = tmp_path / "environments"
    collections_dir.mkdir()
    environments_dir.mkdir()
    secret = "private-environment-id"
    records = [
        {"id": secret, "variables": 1},
        {"id": "other-private-id", "variables": ["malformed"]},
        Environment(id="required-env").model_dump(mode="json"),
    ]
    (environments_dir / "environments.json").write_text(
        json.dumps(records), encoding="utf-8"
    )
    storage = StorageManager(
        collections_dir=collections_dir,
        environments_dir=environments_dir,
        initialize_collections=False,
        initialize_environments=False,
    )

    with caplog.at_level(logging.WARNING, logger="pypost.core.daemon_storage"):
        storage.load_environments_snapshot_strict(required_ids={"required-env"})

    messages = [
        record.message
        for record in caplog.records
        if record.name == "pypost.core.daemon_storage"
    ]
    assert messages == [
        "daemon_storage_records_skipped kind=environments count=2"
    ]
    assert secret not in caplog.text
