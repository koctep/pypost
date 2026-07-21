"""Responsiveness tests for async encrypted environment storage."""

import json
import threading
import time

import pytest
from PySide6.QtCore import QTimer
from PySide6.QtTest import QSignalSpy

from pypost.core.qt.environment_storage_gateway import EnvironmentStorageGateway
from pypost.core.storage import StorageManager
from pypost.models.models import Environment
from tests.helpers.process_until import gateway_timeout_detail, process_until

pytestmark = pytest.mark.timeout(120)


def _make_storage(tmp_path, monkeypatch) -> StorageManager:
    monkeypatch.setattr(
        "pypost.core.storage.user_data_dir",
        lambda app_name, app_author: str(tmp_path / "pypost-data"),
    )
    monkeypatch.setenv("PYPOST_ENV_ENCRYPTION_ENABLED", "true")
    fernet = pytest.importorskip("cryptography.fernet")
    monkeypatch.setenv("PYPOST_ENV_ENCRYPTION_KEY", fernet.Fernet.generate_key().decode("utf-8"))
    return StorageManager()


def _large_environments(count: int, hidden_per_env: int) -> list[Environment]:
    environments = []
    for i in range(count):
        variables = {f"SECRET_{j}": f"value-{i}-{j}" for j in range(hidden_per_env)}
        environments.append(
            Environment(
                name=f"Env-{i}",
                variables=variables,
                hidden_keys=set(variables),
            )
        )
    return environments


def test_process_until_exits_on_wall_clock_deadline(qapp):
    """Watchdog must end the wait when the predicate never becomes true."""
    started = time.monotonic()
    with pytest.raises(AssertionError, match="condition not met within 300ms"):
        process_until(lambda: False, timeout_ms=300)
    elapsed_s = time.monotonic() - started
    assert elapsed_s < 2.0, f"wait hung for {elapsed_s:.2f}s; expected ~0.3s fail"


def test_process_until_exits_via_posted_quit_without_poll_timer(qapp):
    """Posted quit alone must break exec() when no QTimer poll runs."""
    started = time.monotonic()
    with pytest.raises(AssertionError, match="condition not met within 300ms"):
        process_until(lambda: False, timeout_ms=300, use_poll_timer=False)
    elapsed_s = time.monotonic() - started
    assert elapsed_s < 2.0, f"watchdog hung for {elapsed_s:.2f}s; expected ~0.3s fail"


def test_event_loop_stays_responsive_during_encrypted_load(
    tmp_path, monkeypatch, qapp
):
    storage = _make_storage(tmp_path, monkeypatch)
    environments = _large_environments(count=8, hidden_per_env=40)
    storage.save_environments(environments)
    gateway = EnvironmentStorageGateway(storage)
    timer_fired = []

    def on_timeout():
        timer_fired.append(True)

    timer = QTimer()
    timer.setInterval(0)
    timer.setSingleShot(True)
    timer.timeout.connect(on_timeout)
    timer.start()

    spy = QSignalSpy(gateway.load_completed)
    fail_spy = QSignalSpy(gateway.load_failed)
    gateway.load_async()

    process_until(
        lambda: spy.count() >= 1 or fail_spy.count() >= 1,
        timeout_ms=10_000,
        timeout_detail=gateway_timeout_detail(gateway),
    )
    if fail_spy.count() >= 1:
        pytest.fail(f"load failed: {fail_spy.at(0)[0]}")
    assert timer_fired, "event loop should process timer during async load"
    assert len(spy.at(0)[0]) == len(environments)


def test_event_loop_stays_responsive_during_encrypted_save(
    tmp_path, monkeypatch, qapp
):
    storage = _make_storage(tmp_path, monkeypatch)
    environments = _large_environments(count=8, hidden_per_env=40)
    payload = [env.model_dump(mode="json") for env in environments]
    with open(storage.environments_file, "w") as f:
        json.dump(payload, f)

    gateway = EnvironmentStorageGateway(storage)
    timer_fired = []

    def on_timeout():
        timer_fired.append(True)

    timer = QTimer()
    timer.setInterval(0)
    timer.setSingleShot(True)
    timer.timeout.connect(on_timeout)
    timer.start()

    spy = QSignalSpy(gateway.save_completed)
    fail_spy = QSignalSpy(gateway.save_failed)
    gateway.save_async(environments)

    process_until(
        lambda: spy.count() >= 1 or fail_spy.count() >= 1,
        timeout_ms=10_000,
        timeout_detail=gateway_timeout_detail(gateway),
    )
    if fail_spy.count() >= 1:
        pytest.fail(f"save failed: {fail_spy.at(0)[0]}")
    assert timer_fired, "event loop should process timer during async save"


def test_apply_encryption_settings_after_wait_idle_no_mixed_persistence(
    tmp_path, monkeypatch, qapp
):
    storage = _make_storage(tmp_path, monkeypatch)
    environments = _large_environments(count=3, hidden_per_env=2)
    gateway = EnvironmentStorageGateway(storage)

    save_started = threading.Event()
    release_save = threading.Event()
    original_save = storage.save_environments

    def gated_save(envs):
        save_started.set()
        if not release_save.wait(timeout=5):
            raise TimeoutError("save gate timed out")
        return original_save(envs)

    storage.save_environments = gated_save

    save_spy = QSignalSpy(gateway.save_completed)
    fail_spy = QSignalSpy(gateway.save_failed)
    gateway.save_async(environments)

    process_until(
        save_started.is_set,
        timeout_ms=5_000,
        timeout_detail=gateway_timeout_detail(gateway),
    )
    assert gateway.is_busy()

    assert gateway.wait_idle(timeout_ms=100) is False
    assert gateway.is_busy()

    release_save.set()
    assert gateway.wait_idle() is True
    process_until(
        lambda: save_spy.count() >= 1 or fail_spy.count() >= 1,
        timeout_ms=10_000,
        timeout_detail=gateway_timeout_detail(gateway),
    )
    if fail_spy.count() >= 1:
        pytest.fail(f"save failed: {fail_spy.at(0)[0]}")

    with open(storage.environments_file) as f:
        payload = json.load(f)

    for item in payload:
        hidden = set(item.get("hidden_keys", []))
        for key, value in item["variables"].items():
            if key in hidden:
                assert isinstance(value, dict)
                assert value.get("enc") is True
            else:
                assert isinstance(value, str)

    loaded = storage.load_environments()
    assert len(loaded) == len(environments)
    for env in loaded:
        for key in env.hidden_keys:
            assert env.variables[key].startswith("value-")
