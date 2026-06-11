import json

import pytest
from prometheus_client import generate_latest

from pypost.core.metrics import MetricsManager
from pypost.core.key_provider import EnvironmentEncryptionError
from pypost.core.storage import StorageManager
from pypost.models.models import Environment
from pypost.models.settings import AppSettings


def _make_storage(tmp_path, monkeypatch) -> StorageManager:
    monkeypatch.setattr(
        "pypost.core.storage.user_data_dir",
        lambda app_name, app_author: str(tmp_path / "pypost-data"),
    )
    monkeypatch.delenv("PYPOST_ENV_ENCRYPTION_ENABLED", raising=False)
    monkeypatch.delenv("PYPOST_ENV_ENCRYPTION_KEY", raising=False)
    return StorageManager()


def _scrape_metrics(metrics: MetricsManager) -> str:
    return generate_latest(metrics.registry).decode("utf-8")


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


def test_save_environments_encrypts_only_hidden_keys_when_enabled(tmp_path, monkeypatch):
    fernet = pytest.importorskip("cryptography.fernet")
    storage = _make_storage(tmp_path, monkeypatch)
    key = fernet.Fernet.generate_key().decode("utf-8")
    monkeypatch.setenv("PYPOST_ENV_ENCRYPTION_ENABLED", "true")
    monkeypatch.setenv("PYPOST_ENV_ENCRYPTION_KEY", key)

    env = Environment(
        name="Dev",
        variables={"SECRET": "s3cr3t", "VISIBLE": "public"},
        hidden_keys={"SECRET"},
    )
    storage.save_environments([env])

    with open(storage.environments_file, "r") as f:
        payload = json.load(f)

    secret_payload = payload[0]["variables"]["SECRET"]
    assert isinstance(secret_payload, dict)
    assert secret_payload["enc"] is True
    assert secret_payload["alg"] == "fernet"
    assert secret_payload["v"] == 1
    assert isinstance(secret_payload["kid"], str)
    assert isinstance(secret_payload["ct"], str)
    assert payload[0]["variables"]["VISIBLE"] == "public"


def test_load_environments_decrypts_encrypted_hidden_values(tmp_path, monkeypatch):
    fernet = pytest.importorskip("cryptography.fernet")
    storage = _make_storage(tmp_path, monkeypatch)
    key = fernet.Fernet.generate_key().decode("utf-8")
    monkeypatch.setenv("PYPOST_ENV_ENCRYPTION_ENABLED", "true")
    monkeypatch.setenv("PYPOST_ENV_ENCRYPTION_KEY", key)

    env = Environment(
        id="e1",
        name="Dev",
        variables={"SECRET": "s3cr3t"},
        hidden_keys={"SECRET"},
    )
    storage.save_environments([env])

    reloaded = storage.load_environments()
    assert len(reloaded) == 1
    assert reloaded[0].variables["SECRET"] == "s3cr3t"
    assert reloaded[0].hidden_keys == {"SECRET"}


def test_load_environments_with_missing_key_returns_empty(tmp_path, monkeypatch):
    fernet = pytest.importorskip("cryptography.fernet")
    storage = _make_storage(tmp_path, monkeypatch)
    key = fernet.Fernet.generate_key().decode("utf-8")
    monkeypatch.setenv("PYPOST_ENV_ENCRYPTION_ENABLED", "true")
    monkeypatch.setenv("PYPOST_ENV_ENCRYPTION_KEY", key)

    env = Environment(
        id="e1",
        name="Dev",
        variables={"SECRET": "s3cr3t"},
        hidden_keys={"SECRET"},
    )
    storage.save_environments([env])

    monkeypatch.delenv("PYPOST_ENV_ENCRYPTION_KEY", raising=False)
    reloaded = storage.load_environments()
    assert reloaded == []


def test_save_environments_encrypts_hidden_keys_from_app_settings(tmp_path, monkeypatch):
    fernet = pytest.importorskip("cryptography.fernet")
    storage = _make_storage(tmp_path, monkeypatch)
    key = fernet.Fernet.generate_key().decode("utf-8")
    monkeypatch.setenv("PYPOST_ENV_ENCRYPTION_KEY", key)
    storage.apply_encryption_settings(AppSettings(env_encryption_enabled=True))

    env = Environment(
        name="Dev",
        variables={"SECRET": "s3cr3t", "VISIBLE": "public"},
        hidden_keys={"SECRET"},
    )
    storage.save_environments([env])

    with open(storage.environments_file, "r") as f:
        payload = json.load(f)

    secret_payload = payload[0]["variables"]["SECRET"]
    assert isinstance(secret_payload, dict)
    assert secret_payload["enc"] is True
    assert payload[0]["variables"]["VISIBLE"] == "public"


def test_app_settings_disabled_overrides_env_enabled(tmp_path, monkeypatch):
    storage = _make_storage(tmp_path, monkeypatch)
    monkeypatch.setenv("PYPOST_ENV_ENCRYPTION_ENABLED", "true")
    storage.apply_encryption_settings(AppSettings(env_encryption_enabled=False))

    env = Environment(
        name="Dev",
        variables={"SECRET": "plain", "VISIBLE": "public"},
        hidden_keys={"SECRET"},
    )
    storage.save_environments([env])

    with open(storage.environments_file, "r") as f:
        payload = json.load(f)

    assert payload[0]["variables"]["SECRET"] == "plain"


def test_second_save_reencrypts_only_changed_hidden_keys(tmp_path, monkeypatch):
    fernet = pytest.importorskip("cryptography.fernet")
    monkeypatch.setattr(
        "pypost.core.storage.user_data_dir",
        lambda app_name, app_author: str(tmp_path / "pypost-data"),
    )
    monkeypatch.setenv("PYPOST_ENV_ENCRYPTION_ENABLED", "true")
    key = fernet.Fernet.generate_key().decode("utf-8")
    monkeypatch.setenv("PYPOST_ENV_ENCRYPTION_KEY", key)
    metrics = MetricsManager()
    storage = StorageManager(metrics=metrics)

    env = Environment(
        id="e1",
        name="Dev",
        variables={"A": "one", "B": "two"},
        hidden_keys={"A", "B"},
    )
    storage.save_environments([env])
    with open(storage.environments_file, "r") as f:
        first_payload = json.load(f)

    env.variables["B"] = "changed"
    storage.save_environments([env])
    with open(storage.environments_file, "r") as f:
        second_payload = json.load(f)

    assert second_payload[0]["variables"]["A"] == first_payload[0]["variables"]["A"]
    assert second_payload[0]["variables"]["B"] != first_payload[0]["variables"]["B"]
    scraped = _scrape_metrics(metrics)
    assert "environment_value_encryptions_total 3.0" in scraped


def test_metrics_track_encryption_and_decryption_counters(tmp_path, monkeypatch):
    fernet = pytest.importorskip("cryptography.fernet")
    monkeypatch.setattr(
        "pypost.core.storage.user_data_dir",
        lambda app_name, app_author: str(tmp_path / "pypost-data"),
    )
    monkeypatch.setenv("PYPOST_ENV_ENCRYPTION_ENABLED", "true")
    key = fernet.Fernet.generate_key().decode("utf-8")
    monkeypatch.setenv("PYPOST_ENV_ENCRYPTION_KEY", key)
    metrics = MetricsManager()
    storage = StorageManager(metrics=metrics)

    env = Environment(
        id="e1",
        name="Dev",
        variables={"SECRET": "s3cr3t", "VISIBLE": "public"},
        hidden_keys={"SECRET"},
    )
    storage.save_environments([env])
    reloaded = storage.load_environments()

    assert reloaded[0].variables["SECRET"] == "s3cr3t"
    scraped = _scrape_metrics(metrics)
    assert "environment_value_encryptions_total 1.0" in scraped
    assert "environment_value_decryptions_total 1.0" in scraped


def test_metrics_track_save_encryption_error_when_key_missing(tmp_path, monkeypatch):
    monkeypatch.setattr(
        "pypost.core.storage.user_data_dir",
        lambda app_name, app_author: str(tmp_path / "pypost-data"),
    )
    monkeypatch.setenv("PYPOST_ENV_ENCRYPTION_ENABLED", "true")
    monkeypatch.delenv("PYPOST_ENV_ENCRYPTION_KEY", raising=False)
    metrics = MetricsManager()
    storage = StorageManager(metrics=metrics)

    env = Environment(
        name="Dev",
        variables={"SECRET": "s3cr3t"},
        hidden_keys={"SECRET"},
    )
    with pytest.raises(EnvironmentEncryptionError, match="Encryption key is unavailable"):
        storage.save_environments([env])

    scraped = _scrape_metrics(metrics)
    assert (
        'environment_encryption_errors_total{reason="encrypt_failed",stage="save"} 1.0' in scraped
    )


def test_metrics_track_load_decryption_error_when_key_mismatch(tmp_path, monkeypatch):
    fernet = pytest.importorskip("cryptography.fernet")
    monkeypatch.setattr(
        "pypost.core.storage.user_data_dir",
        lambda app_name, app_author: str(tmp_path / "pypost-data"),
    )
    monkeypatch.setenv("PYPOST_ENV_ENCRYPTION_ENABLED", "true")
    metrics = MetricsManager()
    storage = StorageManager(metrics=metrics)

    original_key = fernet.Fernet.generate_key().decode("utf-8")
    monkeypatch.setenv("PYPOST_ENV_ENCRYPTION_KEY", original_key)
    env = Environment(
        id="e1",
        name="Dev",
        variables={"SECRET": "s3cr3t"},
        hidden_keys={"SECRET"},
    )
    storage.save_environments([env])

    different_key = fernet.Fernet.generate_key().decode("utf-8")
    monkeypatch.setenv("PYPOST_ENV_ENCRYPTION_KEY", different_key)
    reloaded = storage.load_environments()

    assert reloaded == []
    scraped = _scrape_metrics(metrics)
    assert (
        'environment_encryption_errors_total{reason="decrypt_failed",stage="load"} 1.0' in scraped
    )


def test_metrics_track_load_unsupported_format_error(tmp_path, monkeypatch):
    monkeypatch.setattr(
        "pypost.core.storage.user_data_dir",
        lambda app_name, app_author: str(tmp_path / "pypost-data"),
    )
    metrics = MetricsManager()
    storage = StorageManager(metrics=metrics)
    payload = [
        {
            "id": "e1",
            "name": "Dev",
            "variables": {"SECRET": ["invalid", "shape"]},
            "hidden_keys": ["SECRET"],
            "enable_mcp": False,
        }
    ]
    with open(storage.environments_file, "w") as f:
        json.dump(payload, f)

    assert storage.load_environments() == []

    scraped = _scrape_metrics(metrics)
    assert (
        'environment_encryption_errors_total{reason="unsupported_format",stage="load"} 1.0'
        in scraped
    )
