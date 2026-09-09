"""Framework-neutral registry contract and concurrent callback regressions."""

from __future__ import annotations

import threading
from collections.abc import Callable

import pytest

from pypost.core.mcp_server_registry import MCPServerRegistry
from pypost.models.models import Collection, Environment
from pypost.models.settings import McpServerConfiguration

pytestmark = pytest.mark.timeout(30)


class FakeRuntime:
    def __init__(self) -> None:
        self.last_start_error: str | None = None
        self.is_listening = False
        self._running = False
        self._status_callbacks: list[Callable[[bool], None]] = []
        self._failure_callbacks: list[Callable[[str], None]] = []

    def connect_status_changed(self, callback: Callable[[bool], None]) -> None:
        self._status_callbacks.append(callback)

    def connect_start_failed(self, callback: Callable[[str], None]) -> None:
        self._failure_callbacks.append(callback)

    def set_variable_supplier(self, _supplier) -> None:
        return

    def set_hidden_keys_supplier(self, _supplier) -> None:
        return

    def start_server(self, _port, _tools, _host="127.0.0.1") -> None:
        self._running = self.is_listening = True
        self.emit_status(True)

    def start_proxy_server(self, **_kwargs) -> None:
        self._running = self.is_listening = True
        self.emit_status(True)

    def stop_server(self) -> None:
        self._running = self.is_listening = False
        self.emit_status(False)

    def is_running(self) -> bool:
        return self._running

    def update_tools(self, _tools) -> bool:
        return False

    def activity_entries(self) -> list:
        return []

    def emit_status(self, running: bool) -> None:
        for callback in tuple(self._status_callbacks):
            callback(running)


def _registry() -> tuple[MCPServerRegistry, list[FakeRuntime]]:
    collection = Collection(id="collection")
    environment = Environment(id="environment")
    runtimes: list[FakeRuntime] = []

    def factory() -> FakeRuntime:
        runtime = FakeRuntime()
        runtimes.append(runtime)
        return runtime

    registry = MCPServerRegistry(
        collection_lookup=lambda record_id: (
            collection if record_id == collection.id else None
        ),
        environment_lookup=lambda record_id: (
            environment if record_id == environment.id else None
        ),
        runtime_factory=factory,
    )
    registry.upsert(
        McpServerConfiguration(
            id="server",
            port=1081,
            collection_id=collection.id,
            environment_id=environment.id,
        )
    )
    return registry, runtimes


def test_core_registry_uses_injected_runtime_and_plain_callbacks() -> None:
    registry, runtimes = _registry()
    observed: list[tuple[str, str]] = []
    registry.connect_status_changed(
        lambda instance_id, state, _message: observed.append((instance_id, state))
    )

    registry.start("server")

    assert len(runtimes) == 1
    assert registry.status("server").state == "running"
    assert observed[-1] == ("server", "running")


def test_runtime_callbacks_and_ui_reads_share_a_serialized_state_boundary() -> None:
    registry, runtimes = _registry()
    registry.start("server")
    runtime = runtimes[0]
    failures: list[BaseException] = []

    def publish(index: int) -> None:
        try:
            runtime.emit_status(index % 2 == 0)
            registry.list_statuses()
            registry.list_configurations()
        except BaseException as exc:
            failures.append(exc)

    threads = [threading.Thread(target=publish, args=(index,)) for index in range(100)]
    for thread in threads:
        thread.start()
    for thread in threads:
        thread.join()

    assert failures == []
    assert registry.status("server").state in {"running", "stopped"}
