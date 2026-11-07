"""MCP server runner strategy: thread vs process isolation (PYPOST-1439)."""

from __future__ import annotations

import logging
from copy import deepcopy
from dataclasses import dataclass, field
from typing import Any, Callable, Protocol, runtime_checkable

from pypost.core.mcp_process_supervisor import (
    DEFAULT_STOP_BUDGET_S,
    McpProcessSupervisor,
)
from pypost.core.qt.mcp_server import MCPServerManager
from pypost.models.settings import McpServerConfiguration

logger = logging.getLogger(__name__)


@dataclass
class ServerStartSpec:
    """Picklable / deep-copied start payload for a runner."""

    configuration: McpServerConfiguration
    tools: list[Any] = field(default_factory=list)
    variables: dict[str, str] = field(default_factory=dict)
    hidden_keys: set[str] = field(default_factory=set)
    overridable_keys: set[str] = field(default_factory=set)


@runtime_checkable
class MCPServerRunnerProtocol(Protocol):
    """Host-facing lifecycle surface used by the registry."""

    def start(self, spec: ServerStartSpec) -> None: ...

    def stop(self, timeout: float | None = None) -> bool: ...

    def is_running(self) -> bool: ...

    def is_listening(self) -> bool: ...

    @property
    def last_start_error(self) -> str | None: ...

    def update_tools(self, tools: list[Any]) -> bool: ...

    def update_variables(
        self,
        variables: dict[str, str],
        hidden_keys: set[str],
        overridable_keys: set[str],
    ) -> None: ...


class ThreadServerRunner:
    """Adapter around the existing ``MCPServerManager`` thread + uvicorn path."""

    def __init__(self, manager: MCPServerManager) -> None:
        self._manager = manager

    @property
    def manager(self) -> MCPServerManager:
        return self._manager

    def start(self, spec: ServerStartSpec) -> None:
        config = spec.configuration
        self._manager.set_variable_supplier(lambda: dict(spec.variables))
        self._manager.set_hidden_keys_supplier(lambda: set(spec.hidden_keys))
        self._manager.set_overridable_keys_supplier(
            lambda: set(spec.overridable_keys)
        )
        if config.server_type == "proxy":
            self._manager.start_proxy_server(
                port=config.port,
                upstream_url=config.upstream_url or "",
                upstream_transport=config.upstream_transport,
                headers=config.headers,
                host=config.host,
                name=config.name or config.id,
                timeout=config.timeout,
            )
        else:
            self._manager.start_server(config.port, spec.tools, config.host)

    def stop(self, timeout: float | None = None) -> bool:
        return self._manager.stop_server(timeout=timeout)

    def is_running(self) -> bool:
        return self._manager.is_running()

    def is_listening(self) -> bool:
        return self._manager.is_listening

    @property
    def last_start_error(self) -> str | None:
        return self._manager.last_start_error

    def update_tools(self, tools: list[Any]) -> bool:
        return self._manager.update_tools(tools)

    def update_variables(
        self,
        variables: dict[str, str],
        hidden_keys: set[str],
        overridable_keys: set[str],
    ) -> None:
        self._manager.set_variable_supplier(lambda: dict(variables))
        self._manager.set_hidden_keys_supplier(lambda: set(hidden_keys))
        self._manager.set_overridable_keys_supplier(
            lambda: set(overridable_keys)
        )


class ProcessServerRunner:
    """Adapter that translates registry lifecycle into supervisor calls."""

    def __init__(
        self,
        instance_id: str,
        supervisor: McpProcessSupervisor | None = None,
        *,
        on_unexpected_exit: Callable[[str, int | None], None] | None = None,
        stop_budget_s: float = DEFAULT_STOP_BUDGET_S,
    ) -> None:
        self._instance_id = instance_id
        self._supervisor = supervisor or McpProcessSupervisor(
            on_unexpected_exit=on_unexpected_exit,
            stop_budget_s=stop_budget_s,
        )
        self._listening = False
        self._start_error: str | None = None
        self._spec: ServerStartSpec | None = None

    @property
    def supervisor(self) -> McpProcessSupervisor:
        return self._supervisor

    @property
    def worker_id(self) -> str:
        """Return the supervisor identity, independent of the public server ID."""
        return self._instance_id

    @property
    def start_snapshot(self) -> ServerStartSpec:
        if self._spec is None:
            raise RuntimeError("MCP runner has no accepted start snapshot")
        return deepcopy(self._spec)

    def start(self, spec: ServerStartSpec) -> None:
        self._spec = deepcopy(spec)
        self._start_error = None
        self._listening = False
        config = spec.configuration
        try:
            self._supervisor.spawn_worker(
                self._instance_id,
                host=config.host,
                port=config.port,
                tools=list(spec.tools),
                variables=dict(spec.variables),
                hidden_keys=set(spec.hidden_keys),
                overridable_keys=set(spec.overridable_keys),
                name=config.name or config.id,
                server_type=config.server_type,
                upstream_url=config.upstream_url,
                upstream_transport=config.upstream_transport,
                headers=dict(config.headers),
                timeout=config.timeout,
            )
            self._listening = True
        except Exception as exc:
            self._start_error = type(exc).__name__
            self._listening = False
            logger.error(
                "mcp_process_runner_start_failed instance_id=%s error=%s",
                self._instance_id,
                type(exc).__name__,
            )
            raise

    def stop(self, timeout: float | None = None) -> bool:
        ok = self._supervisor.stop_worker(self._instance_id, timeout=timeout)
        self._listening = False
        return ok

    def is_running(self) -> bool:
        return (
            self._start_error is None
            and self._supervisor.is_alive(self._instance_id)
            and self._supervisor.state(self._instance_id) == "running"
        )

    def is_listening(self) -> bool:
        return self._listening and self.is_running()

    @property
    def last_start_error(self) -> str | None:
        return self._start_error or self._supervisor.last_error(
            self._instance_id
        )

    def update_tools(self, tools: list[Any]) -> bool:
        if not self._supervisor.update_tools(self._instance_id, tools):
            return False
        if self._spec is not None:
            self._spec.tools = deepcopy(list(tools))
        return True

    def update_variables(
        self,
        variables: dict[str, str],
        hidden_keys: set[str],
        overridable_keys: set[str],
    ) -> None:
        self._supervisor.update_variables(
            self._instance_id,
            variables,
            hidden_keys,
            overridable_keys,
        )
        if self._spec is not None:
            self._spec.variables = dict(variables)
            self._spec.hidden_keys = set(hidden_keys)
            self._spec.overridable_keys = set(overridable_keys)

    def send_debug_opcode(self, opcode: str) -> None:
        """Test-only IPC opcode (DEBUG_ABORT / DEBUG_HANG)."""
        self._supervisor.send_debug_opcode(self._instance_id, opcode)

    def worker_is_alive(self) -> bool:
        return self._supervisor.is_alive(self._instance_id)

    def mark_failed(self, message: str | None = None) -> None:
        """Host-side failed transition after unexpected child exit."""
        self._listening = False
        if message:
            self._start_error = message
