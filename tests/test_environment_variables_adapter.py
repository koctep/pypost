import pytest
from prometheus_client import generate_latest

from pypost.core.environment_variables_adapter import EnvironmentVariablesAdapter
from pypost.core.key_provider import EnvironmentEncryptionError
from pypost.core.metrics import MetricsManager
from pypost.models.models import Environment
from pypost.models.settings import AppSettings


def _scrape_metrics(metrics: MetricsManager) -> str:
    return generate_latest(metrics.registry).decode("utf-8")


def test_serialize_encrypts_only_hidden_keys_when_enabled(monkeypatch):
    fernet = pytest.importorskip("cryptography.fernet")
    monkeypatch.setenv("PYPOST_ENV_ENCRYPTION_ENABLED", "true")
    key = fernet.Fernet.generate_key().decode("utf-8")
    monkeypatch.setenv("PYPOST_ENV_ENCRYPTION_KEY", key)

    adapter = EnvironmentVariablesAdapter()
    env = Environment(
        name="Dev",
        variables={"SECRET": "s3cr3t", "VISIBLE": "public"},
        hidden_keys={"SECRET"},
    )

    payload = adapter.serialize_environment(env)

    secret_payload = payload["variables"]["SECRET"]
    assert isinstance(secret_payload, dict)
    assert secret_payload["enc"] is True
    assert payload["variables"]["VISIBLE"] == "public"


def test_round_trip_decrypts_encrypted_hidden_values(monkeypatch):
    fernet = pytest.importorskip("cryptography.fernet")
    monkeypatch.setenv("PYPOST_ENV_ENCRYPTION_ENABLED", "true")
    key = fernet.Fernet.generate_key().decode("utf-8")
    monkeypatch.setenv("PYPOST_ENV_ENCRYPTION_KEY", key)

    adapter = EnvironmentVariablesAdapter()
    env = Environment(
        id="e1",
        name="Dev",
        variables={"SECRET": "s3cr3t"},
        hidden_keys={"SECRET"},
    )

    payload = adapter.serialize_environment(env)
    restored = adapter.deserialize_environment(payload)

    assert restored.variables["SECRET"] == "s3cr3t"
    assert restored.hidden_keys == {"SECRET"}


def test_app_settings_disabled_overrides_env_enabled(monkeypatch):
    monkeypatch.setenv("PYPOST_ENV_ENCRYPTION_ENABLED", "true")
    adapter = EnvironmentVariablesAdapter()
    adapter.apply_encryption_settings(AppSettings(env_encryption_enabled=False))

    env = Environment(
        name="Dev",
        variables={"SECRET": "plain"},
        hidden_keys={"SECRET"},
    )

    payload = adapter.serialize_environment(env)
    assert payload["variables"]["SECRET"] == "plain"


def test_metrics_track_encryption_and_decryption(monkeypatch):
    fernet = pytest.importorskip("cryptography.fernet")
    monkeypatch.setenv("PYPOST_ENV_ENCRYPTION_ENABLED", "true")
    key = fernet.Fernet.generate_key().decode("utf-8")
    monkeypatch.setenv("PYPOST_ENV_ENCRYPTION_KEY", key)

    metrics = MetricsManager()
    adapter = EnvironmentVariablesAdapter(metrics=metrics)
    env = Environment(
        id="e1",
        name="Dev",
        variables={"SECRET": "s3cr3t"},
        hidden_keys={"SECRET"},
    )

    payload = adapter.serialize_environment(env)
    adapter.deserialize_environment(payload)

    scraped = _scrape_metrics(metrics)
    assert "environment_value_encryptions_total 1.0" in scraped
    assert "environment_value_decryptions_total 1.0" in scraped


def test_metrics_track_unsupported_format_error():
    metrics = MetricsManager()
    adapter = EnvironmentVariablesAdapter(metrics=metrics)
    raw = {
        "id": "e1",
        "name": "Dev",
        "variables": {"SECRET": ["invalid", "shape"]},
        "hidden_keys": ["SECRET"],
        "enable_mcp": False,
    }

    with pytest.raises(EnvironmentEncryptionError, match="Unsupported value format"):
        adapter.deserialize_environment(raw)

    scraped = _scrape_metrics(metrics)
    assert (
        'environment_encryption_errors_total{reason="unsupported_format",stage="load"} 1.0'
        in scraped
    )
