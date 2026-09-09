"""Qt-independent state machine for persisted MCP server configurations.

The registry deliberately knows neither ``QObject`` nor the concrete server
runtime.  Composition roots provide a ``McpServerRuntimeFactory``; Qt signal
forwarding lives in :mod:`pypost.core.qt.mcp_server_registry`.
"""
from __future__ import annotations

import logging
import threading
import time
from dataclasses import dataclass
from typing import Callable, Literal, Protocol, Sequence

from pypost.core.metrics_protocol import MetricsTrackerProtocol
from pypost.core.mcp_server_validation import (
    validate_available_port,
    validate_bind_available,
    validate_references,
)
from pypost.models.models import Collection, Environment, RequestData
from pypost.models.settings import McpServerConfiguration
from pypost.models.websocket import WebSocketConnection

logger = logging.getLogger(__name__)

ServerState = Literal["stopped", "starting", "running", "failed"]
StatusListener = Callable[[str, ServerState, str], None]
ReconfigurationListener = Callable[[str, bool], None]


class McpServerRuntime(Protocol):
    """Lifecycle surface required by the registry from any server runtime."""

    @property
    def last_start_error(self) -> str | None: ...

    @property
    def is_listening(self) -> bool: ...

    def connect_status_changed(self, callback: Callable[[bool], None]) -> None: ...

    def connect_start_failed(self, callback: Callable[[str], None]) -> None: ...

    def set_variable_supplier(
        self, supplier: Callable[[], dict[str, str]] | None
    ) -> None: ...

    def set_hidden_keys_supplier(
        self, supplier: Callable[[], set[str]] | None
    ) -> None: ...

    def start_server(
        self,
        port: int,
        tools: Sequence[RequestData | WebSocketConnection],
        host: str = "127.0.0.1",
    ) -> None: ...

    def start_proxy_server(
        self,
        port: int,
        upstream_url: str,
        upstream_transport: str = "streamable_http",
        headers: dict[str, str] | None = None,
        host: str = "127.0.0.1",
        name: str = "pypost-proxy",
        timeout: float = 30.0,
    ) -> None: ...

    def stop_server(self) -> None: ...

    def is_running(self) -> bool: ...

    def update_tools(self, tools: list[RequestData]) -> bool: ...

    def activity_entries(self) -> list: ...


McpServerRuntimeFactory = Callable[[], McpServerRuntime]


@dataclass(frozen=True)
class McpServerStatus:
    """Current state of one MCP server instance."""

    id: str
    state: ServerState
    message: str = ""


@dataclass(frozen=True)
class _PendingReconfiguration:
    """Replacement state retained until its asynchronous bind succeeds."""

    previous_configuration: McpServerConfiguration
    replacement: McpServerConfiguration
    previous_manager: McpServerRuntime
    candidate_manager: McpServerRuntime


class MCPServerRegistry:
    """Own one abstract server runtime per configured MCP endpoint.

    Collection requests and environment data are copied before they reach a
    manager, preventing a UI selection or a later mutable collection edit from
    changing another endpoint's tool map or credentials.
    """

    def __init__(
        self,
        *,
        collection_lookup: Callable[[str], Collection | None] | None = None,
        environment_lookup: Callable[[str], Environment | None] | None = None,
        metrics: MetricsTrackerProtocol | None = None,
        runtime_factory: McpServerRuntimeFactory | None = None,
    ) -> None:
        self._collection_lookup = collection_lookup or (lambda _id: None)
        self._environment_lookup = environment_lookup or (lambda _id: None)
        self._metrics = metrics
        self._runtime_factory = runtime_factory
        self._configurations: dict[str, McpServerConfiguration] = {}
        self._managers: dict[str, McpServerRuntime] = {}
        self._statuses: dict[str, McpServerStatus] = {}
        self._pending_reconfigurations: dict[str, _PendingReconfiguration] = {}
        self._reconfiguration_lock = threading.RLock()
        self._status_listeners: list[StatusListener] = []
        self._reconfiguration_listeners: list[ReconfigurationListener] = []

    def connect_status_changed(self, listener: StatusListener) -> None:
        """Subscribe to state changes without imposing an event-loop framework."""
        with self._reconfiguration_lock:
            self._status_listeners.append(listener)

    def connect_reconfiguration_finished(
        self, listener: ReconfigurationListener
    ) -> None:
        with self._reconfiguration_lock:
            self._reconfiguration_listeners.append(listener)

    def get(self, instance_id: str) -> McpServerConfiguration | None:
        """Return the configuration for instance_id, or None if not found."""
        with self._reconfiguration_lock:
            configuration = self._configurations.get(instance_id)
            return configuration.model_copy(deep=True) if configuration else None

    def upsert(self, configuration: McpServerConfiguration) -> None:
        """Persist an in-memory configuration after globally checking its port."""
        with self._reconfiguration_lock:
            self._validate_available_port(configuration)
            self._configurations[configuration.id] = configuration.model_copy(deep=True)
            self._statuses.setdefault(
                configuration.id, McpServerStatus(configuration.id, "stopped")
            )
            self._publish_instance_metrics()

    def start_enabled(self) -> None:
        """Best-effort startup: one broken row never blocks another endpoint."""
        for configuration in tuple(self._configurations.values()):
            if configuration.enabled:
                self.start(configuration.id)

    def start(self, instance_id: str) -> None:
        configuration = self._configuration(instance_id)
        logger.info(
            "mcp_registry_start_requested instance_id=%s port=%d",
            instance_id,
            configuration.port,
        )
        runtime = self._runtime_inputs(configuration)
        if runtime is None:
            missing = self._missing_reference(configuration)
            self._set_status(
                instance_id,
                "failed",
                f"{instance_id} cannot start: missing {missing} for port {configuration.port}",
            )
            return

        manager = self._managers.get(instance_id)
        if manager is None:
            manager = self._new_manager(instance_id, configuration.port)
            self._managers[instance_id] = manager
        if manager.is_running():
            return

        self._set_status(instance_id, "starting")
        self._start_manager(manager, configuration, runtime)

    def stop(self, instance_id: str) -> None:
        configuration = self._configuration(instance_id)
        logger.info(
            "mcp_registry_stop_requested instance_id=%s port=%d",
            instance_id,
            configuration.port,
        )
        # A candidate is not registered as active until its bind succeeds.
        # Stop must cancel it too, otherwise a late worker signal could commit
        # a replacement after the user explicitly stopped this row.
        with self._reconfiguration_lock:
            pending = self._pending_reconfigurations.pop(instance_id, None)
            if pending is not None:
                pending.candidate_manager.stop_server()
            manager = self._managers.get(instance_id)
            if manager is not None:
                manager.stop_server()
            self._set_status(instance_id, "stopped")

    def stop_all(self) -> None:
        for instance_id in tuple(self._managers):
            self.stop(instance_id)

    def reconfigure(self, instance_id: str, configuration: McpServerConfiguration) -> None:
        """Replace only the selected endpoint; neighbours keep their managers.

        Validate the replacement before disturbing a running manager.  In
        particular, a duplicate port must leave the current endpoint serving
        clients, rather than turning an invalid edit into downtime.
        """
        if instance_id != configuration.id:
            raise ValueError("MCP server configuration id cannot change")
        self._configuration(instance_id)
        previous = self._configuration(instance_id)
        replacement = McpServerConfiguration.model_validate(configuration.model_dump())
        self._validate_available_port(replacement)
        self._validate_replacement_references(replacement)
        if (replacement.host, replacement.port) != (previous.host, previous.port):
            self._validate_os_port(replacement.host, replacement.port)
        was_running = self.is_running(instance_id)
        if not was_running:
            self._configurations[instance_id] = replacement.model_copy(deep=True)
            self._managers.pop(instance_id, None)
            return

        runtime = self._runtime_inputs(replacement)
        if runtime is None:  # Defensive: references were validated immediately above.
            raise ValueError(
                f"MCP server {instance_id} references a missing "
                f"{self._missing_reference(replacement)}"
            )
        previous_manager = self._managers[instance_id]
        candidate = self._make_runtime()
        pending = _PendingReconfiguration(
            previous_configuration=previous.model_copy(deep=True),
            replacement=replacement.model_copy(deep=True),
            previous_manager=previous_manager,
            candidate_manager=candidate,
        )
        with self._reconfiguration_lock:
            self._pending_reconfigurations[instance_id] = pending
        candidate.connect_status_changed(
            lambda running: self._complete_reconfiguration(instance_id, candidate)
            if running
            else None
        )
        candidate.connect_start_failed(
            lambda message: self._rollback_reconfiguration(instance_id, candidate, message)
        )

        # A candidate with a new endpoint can bind while the old one stays
        # live. For the same endpoint, release it only after all validation;
        # the original manager remains available for rollback on a bind race.
        if (replacement.host, replacement.port) == (previous.host, previous.port):
            previous_manager.stop_server()
        self._set_status(instance_id, "starting")
        self._start_manager(candidate, replacement, runtime)
        threading.Thread(
            target=self._watch_reconfiguration,
            args=(instance_id, candidate),
            daemon=True,
        ).start()

    def refresh_collection(self, collection_id: str) -> None:
        """Refresh tools only for running servers bound to ``collection_id``."""
        collection = self._collection_lookup(collection_id)
        instance_ids = tuple(
            instance_id
            for instance_id, configuration in self._configurations.items()
            if configuration.collection_id == collection_id
        )
        if collection is None:
            for instance_id in instance_ids:
                self._set_status(
                    instance_id,
                    "failed",
                    f"{instance_id} cannot refresh: missing collection for "
                    f"port {self._configuration(instance_id).port}",
                )
            return

        for instance_id in instance_ids:
            manager = self._managers.get(instance_id)
            if manager is None:
                continue
            tools = [request.model_copy(deep=True) for request in collection.requests]
            manager.update_tools(tools)

    def reconcile_references(
        self,
        valid_collection_ids: set[str] | None = None,
        valid_environment_ids: set[str] | None = None,
    ) -> bool:
        """Stop and mark only endpoints whose persisted inputs were removed.

        Collection and environment presenters can no longer name a deleted
        record, so refreshing each remaining record alone would leave an
        endpoint serving its last copied tool or variable snapshot.  Reconcile
        every persisted row after those source lists change instead.
        """
        changed = False
        for instance_id, configuration in self._configurations.items():
            if configuration.server_type == "proxy":
                if valid_environment_ids is not None:
                    env_valid = (
                        not configuration.environment_id
                        or configuration.environment_id in valid_environment_ids
                    )
                else:
                    env = (
                        self._environment_lookup(configuration.environment_id)
                        if configuration.environment_id
                        else None
                    )
                    env_valid = not configuration.environment_id or env is not None

                if env_valid:
                    continue

                self.stop(instance_id)
                self._set_status(
                    instance_id,
                    "failed",
                    f"{instance_id} cannot run: missing environment for port "
                    f"{configuration.port}",
                )
                changed = True
                continue

            # Local server
            if valid_collection_ids is not None:
                coll_valid = (
                    configuration.collection_id is not None
                    and configuration.collection_id in valid_collection_ids
                )
            else:
                coll_valid = (
                    configuration.collection_id is not None
                    and self._collection_lookup(configuration.collection_id) is not None
                )

            if valid_environment_ids is not None:
                env_valid = configuration.environment_id in valid_environment_ids
            else:
                env_valid = self._environment_lookup(configuration.environment_id) is not None

            if coll_valid and env_valid:
                continue
            self.stop(instance_id)
            missing = "collection" if not coll_valid else "environment"
            self._set_status(
                instance_id,
                "failed",
                f"{instance_id} cannot run: missing {missing} for port "
                f"{configuration.port}",
            )
            changed = True
        return changed

    def refresh_environment(self, environment_id: str) -> None:
        """Replace environment snapshots only for servers selecting that ID."""
        environment = self._environment_lookup(environment_id)
        instance_ids = tuple(
            instance_id
            for instance_id, configuration in self._configurations.items()
            if configuration.environment_id == environment_id
        )
        if environment is None:
            for instance_id in instance_ids:
                self._set_status(
                    instance_id,
                    "failed",
                    f"{instance_id} cannot refresh: missing environment for "
                    f"port {self._configuration(instance_id).port}",
                )
            return

        variables = dict(environment.variables)
        hidden_keys = set(environment.hidden_keys)

        def supply_variables(snapshot: dict[str, str] = variables) -> dict[str, str]:
            return dict(snapshot)

        def supply_hidden_keys(snapshot: set[str] = hidden_keys) -> set[str]:
            return set(snapshot)

        for instance_id in instance_ids:
            manager = self._managers.get(instance_id)
            if manager is None:
                continue
            manager.set_variable_supplier(supply_variables)
            manager.set_hidden_keys_supplier(supply_hidden_keys)

    def remove(self, instance_id: str) -> None:
        with self._reconfiguration_lock:
            pending = self._pending_reconfigurations.pop(instance_id, None)
            if pending is not None:
                pending.candidate_manager.stop_server()
            self.stop(instance_id)
            self._managers.pop(instance_id, None)
            self._configurations.pop(instance_id, None)
            self._statuses.pop(instance_id, None)
            self._publish_instance_metrics()

    def is_running(self, instance_id: str) -> bool:
        with self._reconfiguration_lock:
            manager = self._managers.get(instance_id)
            return manager is not None and manager.is_running()

    def manager_for(self, instance_id: str) -> McpServerRuntime:
        with self._reconfiguration_lock:
            return self._managers[instance_id]

    def status(self, instance_id: str) -> McpServerStatus:
        with self._reconfiguration_lock:
            self._refresh_async_failure(instance_id)
            manager = self._managers.get(instance_id)
            if manager is not None and manager.is_running():
                current = self._statuses[instance_id]
                if current.state == "starting":
                    self._set_status(instance_id, "running")
            return self._statuses[instance_id]

    def list_statuses(self) -> list[McpServerStatus]:
        with self._reconfiguration_lock:
            return [self._statuses[key] for key in self._configurations]

    def list_configurations(self) -> list[McpServerConfiguration]:
        """Return independent configuration copies in their persisted order."""
        with self._reconfiguration_lock:
            return [
                configuration.model_copy(deep=True)
                for configuration in self._configurations.values()
            ]

    def wait_for_state(self, instance_id: str, state: ServerState, timeout: float) -> bool:
        deadline = time.monotonic() + timeout
        while time.monotonic() < deadline:
            if self.status(instance_id).state == state:
                return True
            time.sleep(0.02)
        return self.status(instance_id).state == state

    def _refresh_async_failure(self, instance_id: str) -> None:
        manager = self._managers.get(instance_id)
        if manager is None or manager.last_start_error is None:
            return
        configuration = self._configuration(instance_id)
        current = self._statuses[instance_id]
        # An explicit Stop wins over a stale worker error from the cancelled
        # startup/reconfiguration attempt.
        if current.state != "stopped":
            self._set_status(
                instance_id,
                "failed",
                f"{instance_id} on port {configuration.port}: {manager.last_start_error}",
            )

    def _configuration(self, instance_id: str) -> McpServerConfiguration:
        with self._reconfiguration_lock:
            try:
                return self._configurations[instance_id]
            except KeyError as exc:
                raise KeyError(f"Unknown MCP server instance: {instance_id}") from exc

    def _runtime_inputs(
        self, configuration: McpServerConfiguration
    ) -> tuple[list, dict[str, str], set[str]] | None:
        if configuration.server_type == "proxy":
            env_vars = {}
            hidden_keys = set()
            if configuration.environment_id:
                environment = self._environment_lookup(configuration.environment_id)
                if environment is not None:
                    env_vars = dict(environment.variables)
                    hidden_keys = set(environment.hidden_keys)
            return ([], env_vars, hidden_keys)

        if not configuration.collection_id:
            return None
        collection = self._collection_lookup(configuration.collection_id)
        environment = self._environment_lookup(configuration.environment_id)
        if collection is None or environment is None:
            return None
        return (
            [request.model_copy(deep=True) for request in collection.requests],
            dict(environment.variables),
            set(environment.hidden_keys),
        )

    def _missing_reference(self, configuration: McpServerConfiguration) -> str:
        if configuration.server_type == "proxy":
            return "environment"
        if (
            not configuration.collection_id
            or self._collection_lookup(configuration.collection_id) is None
        ):
            return "collection"
        return "environment"

    @staticmethod
    def _start_manager(
        manager: McpServerRuntime,
        configuration: McpServerConfiguration,
        runtime: tuple[list, dict[str, str], set[str]],
    ) -> None:
        tools, variables, hidden_keys = runtime
        manager.set_variable_supplier(lambda: dict(variables))
        manager.set_hidden_keys_supplier(lambda: set(hidden_keys))
        if configuration.server_type == "proxy":
            manager.start_proxy_server(
                port=configuration.port,
                upstream_url=configuration.upstream_url or "",
                upstream_transport=configuration.upstream_transport,
                headers=configuration.headers,
                host=configuration.host,
                name=configuration.name or configuration.id,
                timeout=configuration.timeout,
            )
        else:
            manager.start_server(configuration.port, tools, configuration.host)

    def _complete_reconfiguration(
        self, instance_id: str, candidate: McpServerRuntime
    ) -> None:
        with self._reconfiguration_lock:
            pending = self._pending_reconfigurations.get(instance_id)
            if pending is None or pending.candidate_manager is not candidate:
                return
            self._pending_reconfigurations.pop(instance_id)
            self._configurations[instance_id] = pending.replacement
            self._managers[instance_id] = candidate
            pending.previous_manager.stop_server()
            self._set_status(instance_id, "running")
            self._notify_reconfiguration_finished(instance_id, True)

    def _watch_reconfiguration(
        self, instance_id: str, candidate: McpServerRuntime
    ) -> None:
        """Finish or roll back a candidate when Qt has no running event loop.

        Normal desktop operation delivers the manager signals through Qt. The
        watcher provides the same state transition in headless callers and
        tests, where those cross-thread queued signals otherwise remain
        undispatched.
        """
        deadline = time.monotonic() + 10.0
        while time.monotonic() < deadline:
            if candidate.is_listening:
                self._complete_reconfiguration(instance_id, candidate)
                return
            if candidate.last_start_error is not None:
                self._rollback_reconfiguration(
                    instance_id, candidate, candidate.last_start_error
                )
                return
            time.sleep(0.02)
        self._rollback_reconfiguration(
            instance_id,
            candidate,
            "replacement startup timed out before the endpoint became available",
        )

    def _rollback_reconfiguration(
        self, instance_id: str, candidate: McpServerRuntime, message: str
    ) -> None:
        with self._reconfiguration_lock:
            pending = self._pending_reconfigurations.get(instance_id)
            if pending is None or pending.candidate_manager is not candidate:
                return
            self._pending_reconfigurations.pop(instance_id)
            candidate.stop_server()
            self._configurations[instance_id] = pending.previous_configuration
            self._managers[instance_id] = pending.previous_manager
            logger.warning(
                "mcp_registry_reconfigure_rolled_back instance_id=%s port=%d reason=%s",
                instance_id,
                pending.replacement.port,
                message,
            )
            if pending.previous_manager.is_running():
                self._set_status(
                    instance_id,
                    "running",
                    "Replacement failed; the previous endpoint remains available.",
                )
                self._notify_reconfiguration_finished(instance_id, False)
                return
            runtime = self._runtime_inputs(pending.previous_configuration)
            if runtime is None:
                self._set_status(
                    instance_id,
                    "failed",
                    f"{instance_id} rollback failed: missing "
                    f"{self._missing_reference(pending.previous_configuration)}",
                )
                self._notify_reconfiguration_finished(instance_id, False)
                return
            self._set_status(instance_id, "starting")
            self._start_manager(
                pending.previous_manager, pending.previous_configuration, runtime
            )
            self._notify_reconfiguration_finished(instance_id, False)

    def _validate_available_port(self, configuration: McpServerConfiguration) -> None:
        validate_available_port(configuration, self._configurations.values())

    def _validate_replacement_references(
        self, configuration: McpServerConfiguration
    ) -> None:
        validate_references(
            configuration,
            collection_lookup=self._collection_lookup,
            environment_lookup=self._environment_lookup,
        )

    @staticmethod
    def _validate_os_port(host: str, port: int) -> None:
        validate_bind_available(host, port)

    def _make_runtime(self) -> McpServerRuntime:
        if self._runtime_factory is None:
            raise RuntimeError("MCP server runtime factory was not configured")
        return self._runtime_factory()

    def _new_manager(self, instance_id: str, port: int) -> McpServerRuntime:
        """Create and observe a runtime (legacy method name kept for callers)."""
        manager = self._make_runtime()

        def on_status_changed(running: bool) -> None:
            """Keep an asynchronous startup failure from becoming ``stopped``.

            ``MCPServerManager`` emits ``start_failed`` and then its legacy
            ``status_changed(False)`` signal.  The registry's lifecycle gauge
            must retain the failed state immediately, rather than relying on a
            later UI status read to restore it.
            """
            if running:
                self._set_status(instance_id, "running")
                return
            message = manager.last_start_error
            if message is not None:
                self._set_status(
                    instance_id,
                    "failed",
                    f"{instance_id} on port {port}: {message}",
                )
                return
            self._set_status(instance_id, "stopped")

        manager.connect_status_changed(on_status_changed)
        manager.connect_start_failed(
            lambda message: self._set_status(
                instance_id, "failed", f"{instance_id} on port {port}: {message}"
            )
        )
        return manager

    def _set_status(self, instance_id: str, state: ServerState, message: str = "") -> None:
        with self._reconfiguration_lock:
            status = McpServerStatus(instance_id, state, message)
            self._statuses[instance_id] = status
            logger.info(
                "mcp_registry_status instance_id=%s state=%s message_present=%s",
                instance_id,
                state,
                bool(message),
            )
            self._publish_instance_metrics()
        self._notify_status_changed(instance_id, state, message)

    def _notify_status_changed(
        self, instance_id: str, state: ServerState, message: str
    ) -> None:
        with self._reconfiguration_lock:
            listeners = tuple(self._status_listeners)
        for listener in listeners:
            listener(instance_id, state, message)

    def _notify_reconfiguration_finished(
        self, instance_id: str, committed: bool
    ) -> None:
        with self._reconfiguration_lock:
            listeners = tuple(self._reconfiguration_listeners)
        for listener in listeners:
            listener(instance_id, committed)

    def _publish_instance_metrics(self) -> None:
        if self._metrics is None:
            return
        with self._reconfiguration_lock:
            counts = {
                state: sum(status.state == state for status in self._statuses.values())
                for state in ("stopped", "starting", "running", "failed")
            }
        self._metrics.set_mcp_server_instance_counts(counts)
