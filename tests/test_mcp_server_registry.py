"""Red regression coverage for independent MCP server instances (PYPOST-1044)."""

from __future__ import annotations

import socket
import threading
import time
from unittest.mock import MagicMock, patch

import anyio
import pytest

from pypost.core.mcp_server_registry import MCPServerRegistry, _PendingReconfiguration
from pypost.core.mcp_server_impl import MCPServerImpl
from pypost.core.request_service import ExecutionResult
from pypost.models.models import Collection, Environment, RequestData
from pypost.models.response import ResponseData
from pypost.models.settings import AppSettings, McpServerConfiguration
from tests.helpers.mcp_live_server import free_port, wait_for_port
from tests.test_mcp_server_integration import _mcp_call_tool, _mcp_list_tools


pytestmark = pytest.mark.timeout(120)


def _tool(name: str, tool_id: str) -> RequestData:
    return RequestData(
        id=tool_id,
        name=name,
        method="GET",
        url="https://{{ base_url }}/" + tool_id,
        expose_as_mcp=True,
    )


def _result(body: str = "ok") -> ExecutionResult:
    return ExecutionResult(
        response=ResponseData(
            status_code=200,
            headers={},
            body=body,
            elapsed_time=0.01,
            size=len(body),
        ),
        updated_variables={},
        script_logs=[],
        execution_error=None,
    )


def _configuration(
    instance_id: str,
    *,
    port: int,
    collection_id: str,
    environment_id: str,
    enabled: bool = False,
) -> McpServerConfiguration:
    return McpServerConfiguration(
        id=instance_id,
        host="127.0.0.1",
        port=port,
        collection_id=collection_id,
        environment_id=environment_id,
        enabled=enabled,
    )


def _registry(
    collections: list[Collection], environments: list[Environment]
) -> MCPServerRegistry:
    collection_by_id = {collection.id: collection for collection in collections}
    environment_by_id = {environment.id: environment for environment in environments}
    return MCPServerRegistry(
        collection_lookup=collection_by_id.get,
        environment_lookup=environment_by_id.get,
    )


def _mcp_url(port: int) -> str:
    return f"http://127.0.0.1:{port}/mcp"


def _wait_for_port_to_close(port: int, timeout: float = 5.0) -> None:
    deadline = time.time() + timeout
    while time.time() < deadline:
        try:
            with socket.create_connection(("127.0.0.1", port), timeout=0.2):
                time.sleep(0.05)
        except OSError:
            return
    raise AssertionError(f"MCP server still listens on replaced port {port}")


def test_instances_expose_only_their_selected_tools_and_environment_snapshots():
    """Two endpoints must not inherit tools or variables from a global selection."""
    alpha = Collection(id="alpha-collection", requests=[_tool("Alpha only", "alpha")])
    beta = Collection(id="beta-collection", requests=[_tool("Beta only", "beta")])
    alpha_env = Environment(id="alpha-env", variables={"base_url": "alpha.example"})
    beta_env = Environment(id="beta-env", variables={"base_url": "beta.example"})
    alpha_port, beta_port = free_port(), free_port()
    registry = _registry([alpha, beta], [alpha_env, beta_env])
    registry.upsert(
        _configuration(
            "alpha-server",
            port=alpha_port,
            collection_id=alpha.id,
            environment_id=alpha_env.id,
        )
    )
    registry.upsert(
        _configuration(
            "beta-server",
            port=beta_port,
            collection_id=beta.id,
            environment_id=beta_env.id,
        )
    )

    try:
        registry.start("alpha-server")
        registry.start("beta-server")
        wait_for_port("127.0.0.1", alpha_port)
        wait_for_port("127.0.0.1", beta_port)

        assert anyio.run(_mcp_list_tools, _mcp_url(alpha_port)) == ["alpha_only"]
        assert anyio.run(_mcp_list_tools, _mcp_url(beta_port)) == ["beta_only"]

        alpha_service, beta_service = MagicMock(), MagicMock()
        alpha_service.execute.return_value = _result("alpha")
        beta_service.execute.return_value = _result("beta")
        registry.manager_for("alpha-server")._impl._create_request_service = lambda: alpha_service
        registry.manager_for("beta-server")._impl._create_request_service = lambda: beta_service

        anyio.run(_mcp_call_tool, _mcp_url(alpha_port), "alpha_only", {})
        anyio.run(_mcp_call_tool, _mcp_url(beta_port), "beta_only", {})

        assert alpha_service.execute.call_args.args[1]["base_url"] == "alpha.example"
        assert beta_service.execute.call_args.args[1]["base_url"] == "beta.example"
        assert (
            alpha_service.execute.call_args.args[1]["base_url"]
            != beta_service.execute.call_args.args[1]["base_url"]
        )
    finally:
        registry.stop_all()


def test_stopping_or_reconfiguring_one_instance_keeps_the_other_instance_intact():
    """Lifecycle actions address an instance ID rather than a global manager."""
    alpha = Collection(id="alpha-collection", requests=[_tool("Alpha", "alpha")])
    beta = Collection(id="beta-collection", requests=[_tool("Beta", "beta")])
    alpha_env = Environment(id="alpha-env", variables={"base_url": "alpha.example"})
    beta_env = Environment(id="beta-env", variables={"base_url": "beta.example"})
    alpha_port, beta_port, replacement_port = free_port(), free_port(), free_port()
    registry = _registry([alpha, beta], [alpha_env, beta_env])
    alpha_config = _configuration(
        "alpha-server", port=alpha_port, collection_id=alpha.id, environment_id=alpha_env.id
    )
    beta_config = _configuration(
        "beta-server", port=beta_port, collection_id=beta.id, environment_id=beta_env.id
    )
    registry.upsert(alpha_config)
    registry.upsert(beta_config)

    try:
        registry.start("alpha-server")
        registry.start("beta-server")
        wait_for_port("127.0.0.1", alpha_port)
        wait_for_port("127.0.0.1", beta_port)
        beta_manager = registry.manager_for("beta-server")
        beta_service = MagicMock()
        beta_service.execute.return_value = _result("beta")
        beta_manager._impl._create_request_service = lambda: beta_service

        registry.reconfigure(
            "alpha-server",
            alpha_config.model_copy(update={"port": replacement_port}),
        )
        wait_for_port("127.0.0.1", replacement_port)
        _wait_for_port_to_close(alpha_port)
        assert registry.is_running("alpha-server")
        assert registry.is_running("beta-server")
        assert registry.manager_for("beta-server") is beta_manager
        assert anyio.run(_mcp_list_tools, _mcp_url(beta_port)) == ["beta"]

        registry.stop("alpha-server")
        assert not registry.is_running("alpha-server")
        assert registry.manager_for("beta-server") is beta_manager
        assert registry.is_running("beta-server")
        assert anyio.run(_mcp_list_tools, _mcp_url(beta_port)) == ["beta"]
        anyio.run(_mcp_call_tool, _mcp_url(beta_port), "beta", {})
        assert beta_service.execute.call_args.args[1]["base_url"] == "beta.example"
    finally:
        registry.stop_all()


def test_failed_bind_is_reported_for_only_the_requested_instance():
    """A port conflict must not stop a server that is already accepting clients."""
    alpha = Collection(id="alpha-collection", requests=[_tool("Alpha", "alpha")])
    beta = Collection(id="beta-collection", requests=[_tool("Beta", "beta")])
    alpha_env = Environment(id="alpha-env", variables={"base_url": "alpha.example"})
    beta_env = Environment(id="beta-env", variables={"base_url": "beta.example"})
    alpha_port, busy_port = free_port(), free_port()
    registry = _registry([alpha, beta], [alpha_env, beta_env])
    registry.upsert(
        _configuration(
            "alpha-server",
            port=alpha_port,
            collection_id=alpha.id,
            environment_id=alpha_env.id,
        )
    )
    registry.upsert(
        _configuration(
            "beta-server",
            port=busy_port,
            collection_id=beta.id,
            environment_id=beta_env.id,
        )
    )

    # Occupy beta's port with an unrelated listener before its start request.
    occupied = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    occupied.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    occupied.bind(("127.0.0.1", busy_port))
    occupied.listen()
    try:
        registry.start("alpha-server")
        wait_for_port("127.0.0.1", alpha_port)
        registry.start("beta-server")

        assert registry.wait_for_state("beta-server", "failed", timeout=10)
        assert registry.is_running("alpha-server")
        assert not registry.is_running("beta-server")
        assert anyio.run(_mcp_list_tools, _mcp_url(alpha_port)) == ["alpha"]
        failure_message = registry.status("beta-server").message
        assert "beta-server" in failure_message
        assert str(busy_port) in failure_message
    finally:
        registry.stop_all()
        occupied.close()


def test_start_enabled_launches_only_enabled_configurations():
    collection = Collection(id="collection", requests=[])
    environment = Environment(id="environment", variables={})
    registry = _registry([collection], [environment])
    enabled = _configuration(
        "enabled",
        port=free_port(),
        collection_id=collection.id,
        environment_id=environment.id,
        enabled=True,
    )
    disabled = _configuration(
        "disabled",
        port=free_port(),
        collection_id=collection.id,
        environment_id=environment.id,
    )
    registry.upsert(enabled)
    registry.upsert(disabled)

    with patch.object(registry, "start") as start:
        registry.start_enabled()

    start.assert_called_once_with("enabled")
    assert registry.status("disabled").state == "stopped"


def test_start_enabled_isolates_a_missing_enabled_row_from_healthy_server():
    healthy = Collection(id="healthy", requests=[])
    environment = Environment(id="environment", variables={})
    healthy_port = free_port()
    registry = _registry([healthy], [environment])
    registry.upsert(
        _configuration(
            "missing-collection",
            port=free_port(),
            collection_id="gone",
            environment_id=environment.id,
            enabled=True,
        )
    )
    registry.upsert(
        _configuration(
            "healthy-server",
            port=healthy_port,
            collection_id=healthy.id,
            environment_id=environment.id,
            enabled=True,
        )
    )

    try:
        registry.start_enabled()

        assert registry.status("missing-collection").state == "failed"
        assert "missing collection" in registry.status("missing-collection").message
        wait_for_port("127.0.0.1", healthy_port)
        assert registry.is_running("healthy-server")
    finally:
        registry.stop_all()


def test_refresh_collection_updates_only_its_selected_manager():
    alpha = Collection(id="alpha", requests=[_tool("Alpha", "alpha")])
    beta = Collection(id="beta", requests=[_tool("Beta", "beta")])
    environment = Environment(id="environment", variables={})
    registry = _registry([alpha, beta], [environment])
    registry.upsert(
        _configuration(
            "alpha-server",
            port=free_port(),
            collection_id="alpha",
            environment_id="environment",
        )
    )
    registry.upsert(
        _configuration(
            "beta-server",
            port=free_port(),
            collection_id="beta",
            environment_id="environment",
        )
    )
    alpha_manager, beta_manager = MagicMock(), MagicMock()
    alpha_manager.last_start_error = None
    beta_manager.last_start_error = None
    registry._managers.update({"alpha-server": alpha_manager, "beta-server": beta_manager})

    alpha.requests = [_tool("Alpha replacement", "alpha-replacement")]
    registry.refresh_collection("alpha")

    updated_tools = alpha_manager.update_tools.call_args.args[0]
    assert [tool.id for tool in updated_tools] == ["alpha-replacement"]
    assert updated_tools[0] is not alpha.requests[0]
    beta_manager.update_tools.assert_not_called()


def test_refresh_environment_replaces_only_selected_immutable_snapshot():
    collection = Collection(id="collection", requests=[])
    alpha = Environment(id="alpha", variables={"base_url": "alpha.example"}, hidden_keys=["secret"])
    beta = Environment(id="beta", variables={"base_url": "beta.example"})
    registry = _registry([collection], [alpha, beta])
    registry.upsert(
        _configuration(
            "alpha-server",
            port=free_port(),
            collection_id="collection",
            environment_id="alpha",
        )
    )
    registry.upsert(
        _configuration(
            "beta-server",
            port=free_port(),
            collection_id="collection",
            environment_id="beta",
        )
    )
    alpha_manager, beta_manager = MagicMock(), MagicMock()
    registry._managers.update({"alpha-server": alpha_manager, "beta-server": beta_manager})

    registry.refresh_environment("alpha")
    alpha.variables["base_url"] = "changed.example"

    variables_supplier = alpha_manager.set_variable_supplier.call_args.args[0]
    hidden_keys_supplier = alpha_manager.set_hidden_keys_supplier.call_args.args[0]
    assert variables_supplier() == {"base_url": "alpha.example"}
    assert hidden_keys_supplier() == {"secret"}
    beta_manager.set_variable_supplier.assert_not_called()
    beta_manager.set_hidden_keys_supplier.assert_not_called()


def test_reconcile_references_stops_only_server_with_deleted_input():
    alpha = Collection(id="alpha", requests=[])
    beta = Collection(id="beta", requests=[])
    environment = Environment(id="environment", variables={})
    collections = {alpha.id: alpha, beta.id: beta}
    registry = MCPServerRegistry(
        collection_lookup=collections.get,
        environment_lookup=lambda environment_id: (
            environment if environment_id == environment.id else None
        ),
    )
    alpha_config = _configuration(
        "alpha-server", port=free_port(), collection_id=alpha.id, environment_id=environment.id
    )
    beta_config = _configuration(
        "beta-server", port=free_port(), collection_id=beta.id, environment_id=environment.id
    )
    registry.upsert(alpha_config)
    registry.upsert(beta_config)
    alpha_manager, beta_manager = MagicMock(), MagicMock()
    alpha_manager.last_start_error = None
    beta_manager.last_start_error = None
    registry._managers.update(
        {"alpha-server": alpha_manager, "beta-server": beta_manager}
    )
    collections.pop(alpha.id)

    registry.reconcile_references()

    alpha_manager.stop_server.assert_called_once()
    assert registry.status("alpha-server").state == "failed"
    assert "missing collection" in registry.status("alpha-server").message
    beta_manager.stop_server.assert_not_called()
    assert registry.status("beta-server").state == "stopped"


def test_invalid_reconfiguration_does_not_stop_or_replace_running_server():
    collection = Collection(id="collection", requests=[])
    environment = Environment(id="environment", variables={})
    registry = _registry([collection], [environment])
    alpha_config = _configuration(
        "alpha-server", port=free_port(), collection_id="collection", environment_id="environment"
    )
    beta_config = _configuration(
        "beta-server", port=free_port(), collection_id="collection", environment_id="environment"
    )
    registry.upsert(alpha_config)
    registry.upsert(beta_config)
    alpha_manager = MagicMock()
    alpha_manager.is_running.return_value = True
    registry._managers["alpha-server"] = alpha_manager

    with pytest.raises(ValueError, match="already used by beta-server"):
        registry.reconfigure(
            "alpha-server", alpha_config.model_copy(update={"port": beta_config.port})
        )

    alpha_manager.stop_server.assert_not_called()
    assert registry._configurations["alpha-server"].port == alpha_config.port
    assert registry.manager_for("alpha-server") is alpha_manager


def test_reconfiguration_with_missing_reference_keeps_running_endpoint_intact():
    collection = Collection(id="collection", requests=[])
    environment = Environment(id="environment", variables={})
    registry = _registry([collection], [environment])
    configuration = _configuration(
        "server", port=free_port(), collection_id="collection", environment_id="environment"
    )
    registry.upsert(configuration)
    manager = MagicMock()
    manager.is_running.return_value = True
    registry._managers["server"] = manager

    with pytest.raises(ValueError, match="missing collection"):
        registry.reconfigure(
            "server", configuration.model_copy(update={"collection_id": "missing"})
        )

    manager.stop_server.assert_not_called()
    assert registry.list_configurations()[0] == configuration
    assert registry.manager_for("server") is manager


def test_reconfiguration_preflights_a_changed_host_before_stopping_server():
    collection = Collection(id="collection", requests=[])
    environment = Environment(id="environment", variables={})
    registry = _registry([collection], [environment])
    configuration = _configuration(
        "server", port=free_port(), collection_id="collection", environment_id="environment"
    )
    registry.upsert(configuration)
    manager = MagicMock()
    manager.is_running.return_value = True
    registry._managers["server"] = manager

    with patch.object(
        registry, "_validate_os_port", side_effect=ValueError("port unavailable")
    ):
        with pytest.raises(ValueError, match="port unavailable"):
            registry.reconfigure(
                "server", configuration.model_copy(update={"host": "0.0.0.0"})
            )

    manager.stop_server.assert_not_called()
    assert registry.list_configurations()[0] == configuration


def test_failed_reconfiguration_bind_restores_previous_running_endpoint():
    collection = Collection(id="collection", requests=[_tool("Only", "only")])
    environment = Environment(id="environment", variables={})
    old_port, busy_port = free_port(), free_port()
    registry = _registry([collection], [environment])
    configuration = _configuration(
        "server", port=old_port, collection_id=collection.id, environment_id=environment.id
    )
    registry.upsert(configuration)
    occupied = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    occupied.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    occupied.bind(("127.0.0.1", busy_port))
    occupied.listen()
    try:
        registry.start("server")
        wait_for_port("127.0.0.1", old_port)
        with patch.object(registry, "_validate_os_port"):
            registry.reconfigure(
                "server", configuration.model_copy(update={"port": busy_port})
            )
        assert registry.wait_for_state("server", "running", timeout=10)
        assert registry.list_configurations() == [configuration]
        assert registry.is_running("server")
        assert anyio.run(_mcp_list_tools, _mcp_url(old_port)) == ["only"]
    finally:
        registry.stop_all()
        occupied.close()


def test_stop_cancels_pending_reconfiguration_before_candidate_can_commit():
    collection = Collection(id="collection", requests=[])
    environment = Environment(id="environment", variables={})
    registry = _registry([collection], [environment])
    previous = _configuration(
        "server", port=free_port(), collection_id=collection.id, environment_id=environment.id
    )
    replacement = previous.model_copy(update={"port": free_port()})
    registry.upsert(previous)
    previous_manager, candidate = MagicMock(), MagicMock()
    registry._managers["server"] = previous_manager
    registry._pending_reconfigurations["server"] = _PendingReconfiguration(
        previous_configuration=previous,
        replacement=replacement,
        previous_manager=previous_manager,
        candidate_manager=candidate,
    )

    registry.stop("server")
    registry._complete_reconfiguration("server", candidate)

    candidate.stop_server.assert_called_once()
    previous_manager.stop_server.assert_called_once()
    assert "server" not in registry._pending_reconfigurations
    assert registry.manager_for("server") is previous_manager
    assert registry.list_configurations() == [previous]
    assert registry.status("server").state == "stopped"


def test_stop_and_completion_serialize_pending_reconfiguration_access():
    """A completion callback racing Stop must not pop the same pending row."""
    collection = Collection(id="collection", requests=[])
    environment = Environment(id="environment", variables={})
    registry = _registry([collection], [environment])
    previous = _configuration(
        "server", port=free_port(), collection_id=collection.id, environment_id=environment.id
    )
    replacement = previous.model_copy(update={"port": free_port()})
    registry.upsert(previous)
    previous_manager, candidate = MagicMock(), MagicMock()
    registry._managers["server"] = previous_manager
    entered, release = threading.Event(), threading.Event()

    class BlockingPendingReconfigurations(dict):
        def get(self, key, default=None):
            entered.set()
            assert release.wait(timeout=2), "completion did not receive release signal"
            return super().get(key, default)

    registry._pending_reconfigurations = BlockingPendingReconfigurations(
        {
            "server": _PendingReconfiguration(
                previous_configuration=previous,
                replacement=replacement,
                previous_manager=previous_manager,
                candidate_manager=candidate,
            )
        }
    )
    completion_errors: list[BaseException] = []

    def complete() -> None:
        try:
            registry._complete_reconfiguration("server", candidate)
        except BaseException as exc:  # pragma: no cover - asserted below
            completion_errors.append(exc)

    completion_thread = threading.Thread(target=complete)
    stop_thread = threading.Thread(target=registry.stop, args=("server",))
    completion_thread.start()
    assert entered.wait(timeout=2)
    stop_thread.start()
    release.set()
    completion_thread.join(timeout=2)
    stop_thread.join(timeout=2)

    assert not completion_thread.is_alive()
    assert not stop_thread.is_alive()
    assert completion_errors == []
    assert "server" not in registry._pending_reconfigurations
    assert registry.status("server").state == "stopped"
    candidate.stop_server.assert_called_once()


def test_settings_preserve_multiple_server_configurations_and_reject_port_conflicts():
    first = _configuration(
        "first", port=1081, collection_id="collection-a", environment_id="environment-a"
    )
    second = _configuration(
        "second", port=1082, collection_id="collection-b", environment_id="environment-b"
    )
    restored = AppSettings.model_validate(
        AppSettings(mcp_servers=[first, second]).model_dump(mode="json")
    )
    assert restored.mcp_servers == [first, second]
    with pytest.raises(ValueError, match="unique ports"):
        AppSettings(mcp_servers=[first, first.model_copy(update={"id": "duplicate"})])


def test_list_configurations_returns_deep_copies_in_insertion_order():
    collection = Collection(id="collection", requests=[])
    environment = Environment(id="environment", variables={})
    registry = _registry([collection], [environment])
    first = _configuration(
        "first", port=free_port(), collection_id="collection", environment_id="environment"
    )
    second = _configuration(
        "second", port=free_port(), collection_id="collection", environment_id="environment"
    )
    registry.upsert(first)
    registry.upsert(second)

    configurations = registry.list_configurations()
    configurations[0].name = "caller mutation"

    assert [configuration.id for configuration in configurations] == ["first", "second"]
    assert registry.list_configurations()[0].name is None


def test_registry_reports_aggregate_lifecycle_counts_without_instance_metadata():
    collection = Collection(id="collection", requests=[])
    environment = Environment(id="environment", variables={})
    metrics = MagicMock()
    registry = MCPServerRegistry(
        collection_lookup=lambda _id: collection,
        environment_lookup=lambda _id: environment,
        metrics=metrics,
    )
    registry.upsert(
        _configuration(
            "first", port=free_port(), collection_id=collection.id, environment_id=environment.id
        )
    )
    registry.upsert(
        _configuration(
            "second", port=free_port(), collection_id=collection.id, environment_id=environment.id
        )
    )

    registry._set_status("first", "running")
    registry._set_status("second", "failed", "bind unavailable")

    assert metrics.set_mcp_server_instance_counts.call_args.args == (
        {"stopped": 0, "starting": 0, "running": 1, "failed": 1},
    )


def test_instance_tool_registration_does_not_overwrite_aggregate_lifecycle_metric():
    """A single endpoint's tools must not corrupt the registry-owned up gauge."""
    collection = Collection(id="collection", requests=[])
    environment = Environment(id="environment", variables={})
    metrics = MagicMock()
    registry = MCPServerRegistry(
        collection_lookup=lambda _id: collection,
        environment_lookup=lambda _id: environment,
        metrics=metrics,
    )
    registry.upsert(
        _configuration(
            "running", port=free_port(), collection_id=collection.id, environment_id=environment.id
        )
    )
    registry.upsert(
        _configuration(
            "stopped", port=free_port(), collection_id=collection.id, environment_id=environment.id
        )
    )
    metrics.reset_mock()

    registry._set_status("running", "running")
    MCPServerImpl(metrics=metrics).register_tools([])

    assert metrics.set_mcp_server_instance_counts.call_args.args == (
        {"stopped": 1, "starting": 0, "running": 1, "failed": 0},
    )
    metrics.set_mcp_server_up.assert_not_called()


def test_bind_failure_status_signal_does_not_overwrite_failed_metric_state():
    """The legacy stopped signal follows start_failed on the worker thread."""
    collection = Collection(id="collection", requests=[])
    environment = Environment(id="environment", variables={})
    metrics = MagicMock()
    registry = MCPServerRegistry(
        collection_lookup=lambda _id: collection,
        environment_lookup=lambda _id: environment,
        metrics=metrics,
    )
    configuration = _configuration(
        "server", port=free_port(), collection_id=collection.id, environment_id=environment.id
    )
    registry.upsert(configuration)
    manager = registry._new_manager(configuration.id, configuration.port)

    manager._start_error = "port is unavailable"
    manager.status_changed.emit(False)

    assert registry.status(configuration.id).state == "failed"
    assert metrics.set_mcp_server_instance_counts.call_args.args == (
        {"stopped": 0, "starting": 0, "running": 0, "failed": 1},
    )
