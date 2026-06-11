"""PYPOST-534: Guard selective re-encrypt at 100+ hidden keys (PYPOST-485)."""

import json
import time

import pytest
from prometheus_client import generate_latest

from pypost.core.environment_variables_adapter import EnvironmentVariablesAdapter
from pypost.core.metrics import MetricsManager
from pypost.core.storage import StorageManager
from pypost.models.models import Environment

HIDDEN_KEY_COUNT = 120
MIN_REUSE_SPEEDUP_RATIO = 2.0


def _enable_encryption(monkeypatch) -> None:
    fernet = pytest.importorskip("cryptography.fernet")
    monkeypatch.setenv("PYPOST_ENV_ENCRYPTION_ENABLED", "true")
    key = fernet.Fernet.generate_key().decode("utf-8")
    monkeypatch.setenv("PYPOST_ENV_ENCRYPTION_KEY", key)


def _large_environment() -> Environment:
    variables = {f"SECRET_{i:03d}": f"value-{i}" for i in range(HIDDEN_KEY_COUNT)}
    variables["VISIBLE"] = "public"
    hidden_keys = {f"SECRET_{i:03d}" for i in range(HIDDEN_KEY_COUNT)}
    return Environment(
        id="bench-large",
        name="BenchLarge",
        variables=variables,
        hidden_keys=hidden_keys,
    )


def _scrape_metrics(metrics: MetricsManager) -> str:
    return generate_latest(metrics.registry).decode("utf-8")


def _remember_after_first_save(
    adapter: EnvironmentVariablesAdapter,
    env: Environment,
) -> dict:
    first_payload, first_stats = adapter.serialize_environment(env)
    assert first_stats.encrypted_count == HIDDEN_KEY_COUNT
    assert first_stats.reused_count == 0
    adapter.remember_environment_state(env.id, first_payload["variables"], dict(env.variables))
    return first_payload


def test_large_env_second_save_reuses_all_hidden_envelopes(monkeypatch):
    _enable_encryption(monkeypatch)
    adapter = EnvironmentVariablesAdapter()
    env = _large_environment()
    first_payload = _remember_after_first_save(adapter, env)

    second_payload, second_stats = adapter.serialize_environment(env)

    assert second_stats.reused_count == HIDDEN_KEY_COUNT
    assert second_stats.encrypted_count == 0
    assert second_payload["variables"]["SECRET_000"] == first_payload["variables"]["SECRET_000"]


def test_large_env_single_change_reencrypts_one(monkeypatch):
    _enable_encryption(monkeypatch)
    adapter = EnvironmentVariablesAdapter()
    env = _large_environment()
    first_payload = _remember_after_first_save(adapter, env)

    env.variables["SECRET_059"] = "changed"
    second_payload, second_stats = adapter.serialize_environment(env)

    assert second_stats.reused_count == HIDDEN_KEY_COUNT - 1
    assert second_stats.encrypted_count == 1
    assert second_payload["variables"]["SECRET_058"] == first_payload["variables"]["SECRET_058"]
    assert second_payload["variables"]["SECRET_059"] != first_payload["variables"]["SECRET_059"]


def test_large_env_second_save_does_not_increment_encryption_metric(monkeypatch):
    _enable_encryption(monkeypatch)
    metrics = MetricsManager()
    adapter = EnvironmentVariablesAdapter(metrics=metrics)
    env = _large_environment()
    _remember_after_first_save(adapter, env)

    adapter.serialize_environment(env)

    scraped = _scrape_metrics(metrics)
    assert f"environment_value_encryptions_total {HIDDEN_KEY_COUNT}.0" in scraped


def test_selective_second_save_faster_than_full_reencrypt(monkeypatch):
    _enable_encryption(monkeypatch)
    adapter = EnvironmentVariablesAdapter()
    env = _large_environment()
    _remember_after_first_save(adapter, env)

    reuse_start = time.perf_counter()
    adapter.serialize_environment(env)
    reuse_elapsed = time.perf_counter() - reuse_start

    adapter.clear_persisted_state()
    full_start = time.perf_counter()
    adapter.serialize_environment(env)
    full_elapsed = time.perf_counter() - full_start

    assert full_elapsed >= reuse_elapsed * MIN_REUSE_SPEEDUP_RATIO


def test_storage_manager_large_env_second_save_reuses_envelopes(tmp_path, monkeypatch):
    _enable_encryption(monkeypatch)
    monkeypatch.setattr(
        "pypost.core.storage.user_data_dir",
        lambda app_name, app_author: str(tmp_path / "pypost-data"),
    )
    metrics = MetricsManager()
    storage = StorageManager(metrics=metrics)
    env = _large_environment()

    storage.save_environments([env])
    with open(storage.environments_file, "r") as handle:
        first_payload = json.load(handle)

    storage.save_environments([env])
    with open(storage.environments_file, "r") as handle:
        second_payload = json.load(handle)

    first_vars = first_payload[0]["variables"]
    second_vars = second_payload[0]["variables"]
    for index in range(HIDDEN_KEY_COUNT):
        key = f"SECRET_{index:03d}"
        assert second_vars[key] == first_vars[key]

    scraped = _scrape_metrics(metrics)
    assert f"environment_value_encryptions_total {HIDDEN_KEY_COUNT}.0" in scraped
