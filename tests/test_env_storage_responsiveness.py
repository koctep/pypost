"""Responsiveness tests for async encrypted environment storage."""

import json
import threading
import time
from collections.abc import Callable

import pytest
from PySide6.QtCore import QEventLoop, QTimer
from PySide6.QtTest import QSignalSpy

from pypost.core.qt.environment_storage_gateway import EnvironmentStorageGateway
from pypost.core.storage import StorageManager
from pypost.models.models import Environment

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


def _process_until(
    predicate: Callable[[], bool],
    *,
    timeout_ms: int = 10_000,
    use_poll_timer: bool = True,
) -> None:
    """Pump Qt until predicate() is true or wall-clock deadline passes.

    A daemon thread posts ``loop.quit()`` onto the GUI thread so a stuck or
    silent QTimer cannot leave ``QEventLoop.exec()`` hanging past the deadline
    (SIGALRM alone does not interrupt nested C++ exec without Python callbacks).

    Args:
        use_poll_timer: When False, rely only on the cross-thread posted quit
            (used to prove the hang fix when Qt timer slots never run).
    """
    loop = QEventLoop()
    deadline = time.monotonic() + (timeout_ms / 1000.0)
    timer = None

    if use_poll_timer:

        def tick() -> None:
            if predicate() or time.monotonic() >= deadline:
                loop.quit()

        timer = QTimer()
        timer.setInterval(10)
        timer.timeout.connect(tick)
        timer.start()

    # Cross-thread posted quit must target a QObject living on the GUI thread;
    # bare QTimer.singleShot from a worker thread would own the timer there
    # and never fire (no event loop on that thread).
    remaining_s = max(0.0, deadline - time.monotonic())

    def post_quit() -> None:
        QTimer.singleShot(0, loop, loop.quit)

    watchdog = threading.Timer(remaining_s, post_quit)
    watchdog.daemon = True
    watchdog.start()
    try:
        loop.exec()
    finally:
        watchdog.cancel()
        if timer is not None:
            timer.stop()

    assert predicate(), (
        f"condition not met within {timeout_ms}ms "
        "(wall-clock deadline; load_completed/load_failed or predicate never true)"
    )


def test_process_until_exits_on_wall_clock_deadline(qapp):
    """Watchdog must end the wait when the predicate never becomes true."""
    started = time.monotonic()
    with pytest.raises(AssertionError, match="condition not met within 300ms"):
        _process_until(lambda: False, timeout_ms=300)
    elapsed_s = time.monotonic() - started
    assert elapsed_s < 2.0, f"wait hung for {elapsed_s:.2f}s; expected ~0.3s fail"


def test_process_until_exits_via_posted_quit_without_poll_timer(qapp):
    """Posted quit alone must break exec() when no QTimer poll runs."""
    started = time.monotonic()
    with pytest.raises(AssertionError, match="condition not met within 300ms"):
        _process_until(lambda: False, timeout_ms=300, use_poll_timer=False)
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

    _process_until(lambda: spy.count() >= 1 or fail_spy.count() >= 1)
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

    _process_until(lambda: spy.count() >= 1 or fail_spy.count() >= 1)
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

    _process_until(save_started.is_set, timeout_ms=5_000)
    assert gateway.is_busy()

    assert gateway.wait_idle(timeout_ms=100) is False
    assert gateway.is_busy()

    release_save.set()
    assert gateway.wait_idle() is True
    _process_until(
        lambda: save_spy.count() >= 1 or fail_spy.count() >= 1,
        timeout_ms=10_000,
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
