"""Tests verifying concurrent MCP server teardown and parallel cleanup (PYPOST-1434)."""

from __future__ import annotations

import time
import pytest

from pypost.core.mcp_server_registry import MCPServerRegistry
from pypost.models.settings import McpServerConfiguration
from tests.helpers.collection_integration_harness import ServerRegistryFixtureMixin

pytestmark = pytest.mark.timeout(30)


class MockServerManager:
    """Mock MCPServerManager simulating shutdown latency and failure modes."""

    def __init__(self, delay: float = 0.0, should_fail: bool = False) -> None:
        self.delay = delay
        self.should_fail = should_fail
        self.stopped = False
        self.stop_count = 0

    def stop_server(self) -> None:
        self.stop_count += 1
        if self.delay > 0:
            time.sleep(self.delay)
        if self.should_fail:
            raise RuntimeError("simulated crash")
        self.stopped = True

    def is_running(self) -> bool:
        return not self.stopped


def _create_registry_with_mock_servers(
    count: int,
    delay: float = 0.20,
    fail_index: int | None = None,
) -> tuple[MCPServerRegistry, list[MockServerManager]]:
    """Helper to populate an MCPServerRegistry with mock server managers."""
    registry = MCPServerRegistry()
    managers: list[MockServerManager] = []

    for i in range(count):
        instance_id = f"test-srv-{i}"
        cfg = McpServerConfiguration(
            id=instance_id,
            host="127.0.0.1",
            port=9100 + i,
            collection_id=f"col-{i}",
            environment_id=f"env-{i}",
            enabled=True,
        )
        registry.upsert(cfg)
        should_fail = i == fail_index
        manager = MockServerManager(delay=delay, should_fail=should_fail)
        registry._managers[instance_id] = manager  # type: ignore[assignment]
        managers.append(manager)

    return registry, managers


def test_concurrent_teardown_acceleration() -> None:
    """Assert concurrent teardown of 5x 0.20s servers takes < 0.45s (fails on serial >= 1.0s)."""
    registry, managers = _create_registry_with_mock_servers(count=5, delay=0.20)

    start_time = time.monotonic()
    registry.stop_all()
    elapsed = time.monotonic() - start_time

    assert elapsed < 0.45, (
        f"Expected concurrent stop_all() to take < 0.45s, but took {elapsed:.3f}s. "
        "Servers are being stopped sequentially rather than concurrently."
    )
    for i, manager in enumerate(managers):
        assert manager.stopped is True, f"Manager {i} was not stopped"


def test_concurrent_teardown_error_isolation() -> None:
    """Assert partial server failure during stop_all() isolates errors and stops other servers."""
    registry, managers = _create_registry_with_mock_servers(
        count=5, delay=0.05, fail_index=2
    )

    # In unpatched sequential code, stopping manager 2 raises RuntimeError, aborting
    # stop_all() and leaving subsequent managers (3 and 4) unstopped.
    try:
        registry.stop_all()
    except RuntimeError:
        pytest.fail("stop_all() raised an unhandled RuntimeError; error isolation failed.")

    # All non-failing managers must be successfully stopped
    assert managers[0].stopped is True
    assert managers[1].stopped is True
    assert managers[2].stop_count >= 1
    assert managers[3].stopped is True
    assert managers[4].stopped is True


def test_harness_teardown_stops_candidates_and_active_instances() -> None:
    """Assert fixture teardown stops both active instances and tracked candidates."""
    server_fix = ServerRegistryFixtureMixin()
    # Verify candidate list is initialized on the fixture
    assert hasattr(server_fix, "_server_candidates"), (
        "ServerRegistryFixtureMixin must initialize `_server_candidates` list"
    )

    # Active registry server
    config = McpServerConfiguration.model_construct(
        id="active-srv-1",
        name="Active Server 1",
        host="127.0.0.1",
        port=9991,
        server_type="local",
        enabled=True,
    )
    server_fix.registry.upsert(config)
    active_mgr = MockServerManager()
    server_fix.registry._managers["active-srv-1"] = active_mgr  # type: ignore[assignment]

    # Track candidate managers
    cand1 = MockServerManager()
    cand2 = MockServerManager()
    server_fix._server_candidates.extend([cand1, cand2])

    server_fix.teardown()

    assert active_mgr.stopped is True, "Active registry manager was not stopped"
    assert cand1.stopped is True, "Candidate manager 1 was not stopped"
    assert cand2.stopped is True, "Candidate manager 2 was not stopped"
    assert len(server_fix._server_candidates) == 0, (
        "_server_candidates should be cleared after teardown"
    )


def test_concurrent_teardown_idempotent() -> None:
    """Assert calling stop_all() twice in succession completes cleanly and quickly without error."""
    registry, managers = _create_registry_with_mock_servers(count=3, delay=0.0)

    registry.stop_all()
    for manager in managers:
        assert manager.stopped is True

    # Second invocation should be a no-op / idempotent
    start_time = time.monotonic()
    registry.stop_all()
    elapsed = time.monotonic() - start_time

    assert elapsed < 0.10, f"Second stop_all() took too long: {elapsed:.3f}s"
    for manager in managers:
        assert manager.stop_count == 2
