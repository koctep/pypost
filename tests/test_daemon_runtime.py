import logging
from types import SimpleNamespace

import pytest
from PySide6.QtCore import QCoreApplication, QEventLoop, QObject, QTimer, Signal

from pypost.core.qt.daemon_runtime import (
    DaemonRuntime,
    affected_server_ids,
    build_required_data_consumers,
)
from pypost.core.daemon_storage import DaemonDataError
from pypost.models.models import Collection, Environment
from pypost.models.settings import AppSettings, McpServerConfiguration

pytestmark = pytest.mark.timeout(30)


class FakeMetrics(QObject):
    listening_changed = Signal(bool)
    unexpected_exit = Signal(str)

    def __init__(self):
        super().__init__()
        self.is_listening = False
        self.stopped = False
        self.start_failure = False
        self._start_failed_slot = None

    def connect_start_failed(self, slot):
        self._start_failed_slot = slot

    def start_server(self, _host, _port):
        if self.start_failure:
            self._start_failed_slot("sensitive bind detail")
            return
        self.is_listening = True
        self.listening_changed.emit(True)

    def stop_server(self):
        self.stopped = True


class EmptyStorage:
    def apply_encryption_settings(self, _settings):
        return None

    def load_collections_snapshot_strict(self, *, required_ids):
        assert not required_ids
        return {}

    def load_environments_snapshot_strict(self, *, required_ids):
        assert not required_ids
        return {}


class MissingCollectionStorage(EmptyStorage):
    def load_collections_snapshot_strict(self, *, required_ids):
        raise DaemonDataError("collections", "missing", record_id=next(iter(required_ids)))


class RequiredStorage(EmptyStorage):
    def load_collections_snapshot_strict(self, *, required_ids):
        return {
            record_id: Collection(id=record_id, name="Collection")
            for record_id in required_ids
        }

    def load_environments_snapshot_strict(self, *, required_ids):
        return {record_id: Environment(id=record_id) for record_id in required_ids}


class FakeRegistry(QObject):
    status_changed = Signal(str, str, str)
    next_state = "running"
    latest = None

    def __init__(self, **_kwargs):
        super().__init__()
        self.rows = []
        self.states = {}
        self.stop_calls = 0
        self.start_calls = 0
        FakeRegistry.latest = self

    def upsert(self, row):
        self.rows.append(row)
        self.states[row.id] = "stopped"

    def start_enabled(self):
        self.start_calls += 1
        for row in self.rows:
            self.states[row.id] = self.next_state
            self.status_changed.emit(row.id, self.next_state, "private detail")

    def list_statuses(self):
        return [SimpleNamespace(id=row.id, state=self.states[row.id]) for row in self.rows]

    def stop_all(self):
        self.stop_calls += 1


def test_required_data_error_maps_to_all_affected_servers():
    rows = [
        McpServerConfiguration(
            id="one", port=1201, collection_id="collection", environment_id="environment",
            enabled=True,
        ),
        McpServerConfiguration(
            id="two", port=1202, collection_id="collection", environment_id="environment",
            enabled=True,
        ),
    ]
    consumers = build_required_data_consumers(rows)

    assert affected_server_ids(
        DaemonDataError("collections", "store_unreadable"), consumers
    ) == ("one", "two")


def test_runtime_becomes_ready_without_gui_when_no_mcp_rows(tmp_path):
    application = QCoreApplication.instance() or QCoreApplication([])
    metrics = FakeMetrics()
    runtime = DaemonRuntime(
        SimpleNamespace(
            collections_dir=tmp_path,
            environments_dir=tmp_path,
            collections_source="cli",
            environments_source="cli",
        ),
        config_manager=SimpleNamespace(load_config_strict=lambda: AppSettings()),
        storage=EmptyStorage(),
        metrics=metrics,
    )

    runtime.start()

    assert runtime.is_ready
    assert runtime.exit_code == 0
    runtime.shutdown()
    assert metrics.stopped
    assert application is QCoreApplication.instance()


def test_runtime_reports_each_affected_server_without_persisted_values(
    caplog, tmp_path
):
    rows = [
        McpServerConfiguration(
            id=server_id,
            port=port,
            collection_id="missing-id",
            environment_id="environment-id",
            enabled=True,
        )
        for server_id, port in (("server-one", 1201), ("server-two", 1202))
    ]
    runtime = DaemonRuntime(
        SimpleNamespace(
            collections_dir=tmp_path,
            environments_dir=tmp_path,
            collections_source="cli",
            environments_source="cli",
        ),
        config_manager=SimpleNamespace(
            load_config_strict=lambda: AppSettings(mcp_servers=rows)
        ),
        storage=MissingCollectionStorage(),
        metrics=FakeMetrics(),
    )

    with caplog.at_level(logging.ERROR, logger="pypost.core.qt.daemon_runtime"):
        runtime.start()

    assert runtime.exit_code == 1
    affected_records = [
        record
        for record in caplog.records
        if record.message.startswith("daemon_data_failed")
    ]
    assert [record.message.rsplit("=", 1)[-1] for record in affected_records] == [
        "server-one",
        "server-two",
    ]
    assert "affected_count=2" in caplog.text
    assert "missing-id" not in caplog.text


def _enabled_row():
    return McpServerConfiguration(
        id="opaque-server",
        port=1201,
        collection_id="collection-id",
        environment_id="environment-id",
        enabled=True,
    )


def _runtime_with_enabled_row(monkeypatch, tmp_path, metrics):
    monkeypatch.setattr(
        "pypost.core.qt.daemon_runtime.MCPServerRegistry", FakeRegistry
    )
    return DaemonRuntime(
        SimpleNamespace(
            collections_dir=tmp_path,
            environments_dir=tmp_path,
            collections_source="cli",
            environments_source="cli",
        ),
        startup_timeout_ms=100,
        config_manager=SimpleNamespace(
            load_config_strict=lambda: AppSettings(mcp_servers=[_enabled_row()])
        ),
        storage=RequiredStorage(),
        metrics=metrics,
    )


def test_runtime_waits_for_metrics_and_enabled_mcp_readiness(monkeypatch, tmp_path):
    FakeRegistry.next_state = "running"
    runtime = _runtime_with_enabled_row(monkeypatch, tmp_path, FakeMetrics())

    runtime.start()

    assert runtime.is_ready
    assert runtime.exit_code == 0
    runtime.shutdown()


@pytest.mark.parametrize("failure", ["metrics_bind", "mcp_start", "startup_timeout"])
def test_runtime_startup_failures_cleanup_partial_services(
    monkeypatch, tmp_path, failure
):
    metrics = FakeMetrics()
    if failure == "metrics_bind":
        metrics.start_failure = True
    FakeRegistry.next_state = "failed" if failure == "mcp_start" else "starting"
    runtime = _runtime_with_enabled_row(monkeypatch, tmp_path, metrics)

    runtime.start()
    if failure == "startup_timeout":
        runtime._deadline.timeout.emit()

    assert runtime.exit_code == 1
    assert metrics.stopped
    assert FakeRegistry.latest.stop_calls == 1
    if failure == "metrics_bind":
        assert FakeRegistry.latest.start_calls == 0


def test_runtime_unexpected_metrics_exit_is_fatal(monkeypatch, tmp_path):
    metrics = FakeMetrics()
    FakeRegistry.next_state = "running"
    runtime = _runtime_with_enabled_row(monkeypatch, tmp_path, metrics)
    runtime.start()
    assert runtime.is_ready

    metrics.unexpected_exit.emit("listener_stopped")

    assert runtime.exit_code == 1
    assert not runtime.is_ready
    assert FakeRegistry.latest.stop_calls == 1


def test_runtime_mcp_exit_after_readiness_is_fatal(caplog, monkeypatch, tmp_path):
    metrics = FakeMetrics()
    FakeRegistry.next_state = "running"
    runtime = _runtime_with_enabled_row(monkeypatch, tmp_path, metrics)
    runtime.start()
    assert runtime.is_ready

    with caplog.at_level(logging.ERROR, logger="pypost.core.qt.daemon_runtime"):
        FakeRegistry.latest.status_changed.emit(
            "opaque-server", "stopped", "private process detail"
        )

    assert runtime.exit_code == 1
    assert not runtime.is_ready
    assert metrics.stopped
    assert "private process detail" not in caplog.text


def test_runtime_reaches_ready_through_bounded_qt_core_event_loop(tmp_path):
    application = QCoreApplication.instance() or QCoreApplication([])
    runtime = DaemonRuntime(
        SimpleNamespace(
            collections_dir=tmp_path,
            environments_dir=tmp_path,
            collections_source="cli",
            environments_source="cli",
        ),
        config_manager=SimpleNamespace(load_config_strict=lambda: AppSettings()),
        storage=EmptyStorage(),
        metrics=FakeMetrics(),
    )
    event_loop = QEventLoop()

    def start_and_finish():
        runtime.start()
        event_loop.quit()

    QTimer.singleShot(0, start_and_finish)
    QTimer.singleShot(1_000, event_loop.quit)
    event_loop.exec()

    assert runtime.is_ready
    runtime.shutdown()
    assert application is QCoreApplication.instance()
