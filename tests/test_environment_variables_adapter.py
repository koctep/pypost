
import pytest

pytestmark = pytest.mark.timeout(30)

from prometheus_client import generate_latest

from pypost.core.environment_variables_adapter import EnvironmentVariablesAdapter
from pypost.core.key_provider import EnvironmentEncryptionError
from pypost.core.qt.metrics import MetricsManager
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

    payload, _stats = adapter.serialize_environment(env)

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

    payload, _stats = adapter.serialize_environment(env)
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

    payload, _stats = adapter.serialize_environment(env)
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

    payload, _stats = adapter.serialize_environment(env)
    adapter.deserialize_environment(payload)

    scraped = _scrape_metrics(metrics)
    assert "environment_value_encryptions_total 1.0" in scraped
    assert "environment_value_decryptions_total 1.0" in scraped


def test_second_save_reuses_unchanged_hidden_envelopes(monkeypatch):
    fernet = pytest.importorskip("cryptography.fernet")
    monkeypatch.setenv("PYPOST_ENV_ENCRYPTION_ENABLED", "true")
    key = fernet.Fernet.generate_key().decode("utf-8")
    monkeypatch.setenv("PYPOST_ENV_ENCRYPTION_KEY", key)

    metrics = MetricsManager()
    adapter = EnvironmentVariablesAdapter(metrics=metrics)
    env = Environment(
        id="e1",
        name="Dev",
        variables={"A": "one", "B": "two", "VISIBLE": "public"},
        hidden_keys={"A", "B"},
    )

    first, _first_stats = adapter.serialize_environment(env)
    adapter.remember_environment_state(env.id, first["variables"], dict(env.variables))

    second, second_stats = adapter.serialize_environment(env)

    assert second["variables"]["A"] == first["variables"]["A"]
    assert second["variables"]["B"] == first["variables"]["B"]
    assert second_stats.reused_count == 2
    assert second_stats.encrypted_count == 0
    scraped = _scrape_metrics(metrics)
    assert "environment_value_encryptions_total 2.0" in scraped


def test_changed_hidden_key_reencrypts_only_that_value(monkeypatch):
    fernet = pytest.importorskip("cryptography.fernet")
    monkeypatch.setenv("PYPOST_ENV_ENCRYPTION_ENABLED", "true")
    key = fernet.Fernet.generate_key().decode("utf-8")
    monkeypatch.setenv("PYPOST_ENV_ENCRYPTION_KEY", key)

    metrics = MetricsManager()
    adapter = EnvironmentVariablesAdapter(metrics=metrics)
    env = Environment(
        id="e1",
        name="Dev",
        variables={"A": "one", "B": "two"},
        hidden_keys={"A", "B"},
    )

    first, _first_stats = adapter.serialize_environment(env)
    adapter.remember_environment_state(env.id, first["variables"], dict(env.variables))

    env.variables["B"] = "changed"
    second, second_stats = adapter.serialize_environment(env)

    assert second["variables"]["A"] == first["variables"]["A"]
    assert second_stats.reused_count == 1
    assert second_stats.encrypted_count == 1
    assert second["variables"]["B"] != first["variables"]["B"]
    scraped = _scrape_metrics(metrics)
    assert "environment_value_encryptions_total 3.0" in scraped


def test_reuse_requires_matching_active_kid(monkeypatch):
    fernet = pytest.importorskip("cryptography.fernet")
    monkeypatch.setenv("PYPOST_ENV_ENCRYPTION_ENABLED", "true")
    key_a = fernet.Fernet.generate_key().decode("utf-8")
    key_b = fernet.Fernet.generate_key().decode("utf-8")
    from pypost.core.key_provider import build_key_id

    kid_a = build_key_id(key_a)
    kid_b = build_key_id(key_b)
    monkeypatch.setenv("PYPOST_ENV_ENCRYPTION_KEY", key_b)

    adapter = EnvironmentVariablesAdapter()
    env = Environment(
        id="e1",
        name="Dev",
        variables={"SECRET": "value"},
        hidden_keys={"SECRET"},
    )
    stale_envelope = {
        "enc": True,
        "v": 2,
        "alg": "fernet",
        "kid": kid_a,
        "ct": "stale",
    }
    adapter.remember_environment_state(
        env.id,
        {"SECRET": stale_envelope},
        {"SECRET": "value"},
    )

    payload, stats = adapter.serialize_environment(env)

    assert payload["variables"]["SECRET"] != stale_envelope
    assert stats.encrypted_count == 1
    assert stats.reused_count == 0


def test_apply_encryption_settings_clears_persisted_state(monkeypatch):
    monkeypatch.setenv("PYPOST_ENV_ENCRYPTION_ENABLED", "true")
    adapter = EnvironmentVariablesAdapter()
    adapter.remember_environment_state("e1", {"SECRET": {"enc": True}}, {"SECRET": "x"})
    adapter.apply_encryption_settings(AppSettings(env_encryption_enabled=True))
    assert adapter._persisted_variables == {}
    assert adapter._persisted_plaintext == {}


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
