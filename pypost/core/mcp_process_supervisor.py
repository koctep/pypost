"""Process table and SIGTERM→SIGKILL reclamation for MCP workers (PYPOST-1439)."""

from __future__ import annotations

import logging
import multiprocessing
import os
import threading
import time
import uuid
from copy import deepcopy
from dataclasses import dataclass, field
from typing import Any, Callable, Literal

from pypost.core.mcp_worker_ipc import (
    McpProtocolVersionError,
    encode_tools,
    make_message,
    validate_message_version,
)
from pypost.core.mcp_worker_process import worker_main
from pypost.models.settings import (
    McpHeartbeatPolicy,
    McpResourceLimitsPolicy,
    McpWorkerRestartPolicy,
)

logger = logging.getLogger(__name__)

WorkerState = Literal["starting", "running", "failed", "stopped"]


class McpAdmissionError(ValueError):
    """Raised when an MCP worker spawn or restart request violates admission limits."""


def get_process_rss_mb(pid: int) -> float | None:
    """Sample resident memory in megabytes from /proc/{pid}/status on Linux."""
    try:
        with open(f"/proc/{pid}/status", "r", encoding="utf-8") as f:
            for line in f:
                if line.startswith("VmRSS:"):
                    parts = line.split()
                    if len(parts) >= 2:
                        return float(parts[1]) / 1024.0
    except (FileNotFoundError, ProcessLookupError, PermissionError, OSError, ValueError):
        return None
    return None


# Aligned with adaptive join / evaluation §4.1.
DEFAULT_STOP_BUDGET_S = 2.0

# Same family as PYPOST_MCP_TEST_ECHO_VARS — must be set for DEBUG_* IPC.
_ALLOW_DEBUG_IPC_ENV = "PYPOST_MCP_ALLOW_DEBUG_IPC"


@dataclass
class _WorkerSpawnSpec:
    host: str
    port: int
    tools: list[Any]
    variables: dict[str, str]
    hidden_keys: set[str]
    overridable_keys: set[str]
    name: str | None = None
    start_timeout: float = 15.0
    server_type: Literal["local", "proxy"] = "local"
    upstream_url: str | None = None
    upstream_transport: Literal["streamable_http", "sse"] = "streamable_http"
    headers: dict[str, str] = field(default_factory=dict)
    timeout: float = 30.0


@dataclass
class _WorkerRecord:
    instance_id: str
    process: Any
    parent_conn: Any
    spec: _WorkerSpawnSpec | None = None
    state: WorkerState = "starting"
    last_error: str | None = None
    started_event: threading.Event = field(default_factory=threading.Event)
    reader_stop: threading.Event = field(default_factory=threading.Event)
    reader_thread: threading.Thread | None = None
    started_at: float | None = None
    retry_count: int = 0
    next_retry_deadline: float | None = None
    restarting: bool = False
    cancel_event: threading.Event = field(default_factory=threading.Event)
    last_rss_sample_at: float = 0.0
    soft_limit_warned: bool = False
    rss_mb: float | None = None
    last_heartbeat_sent_at: float = 0.0
    last_heartbeat_pong_at: float = 0.0
    pending_heartbeat_nonce: str | None = None
    pending_heartbeat_sent_at: float = 0.0


class McpProcessSupervisor:
    """Owns child PIDs, IPC pipes, and stop escalation for process-mode MCP."""

    def __init__(
        self,
        *,
        on_unexpected_exit: Callable[[str, int | None], None] | None = None,
        on_worker_restarting: Callable[[str, int, float, int | None], None] | None = None,
        on_worker_restarted: Callable[[str, int], None] | None = None,
        restart_policy: McpWorkerRestartPolicy | None = None,
        resource_limits: McpResourceLimitsPolicy | None = None,
        heartbeat_policy: McpHeartbeatPolicy | None = None,
        rss_sampler: Callable[[int], float | None] | None = None,
        stop_budget_s: float = DEFAULT_STOP_BUDGET_S,
    ) -> None:
        self._ctx = multiprocessing.get_context("spawn")
        self._workers: dict[str, _WorkerRecord] = {}
        self._lock = threading.RLock()
        self._on_unexpected_exit = on_unexpected_exit
        self._on_worker_restarting = on_worker_restarting
        self._on_worker_restarted = on_worker_restarted
        self._restart_policy = (
            restart_policy.model_copy()
            if restart_policy is not None
            else McpWorkerRestartPolicy()
        )
        self._resource_limits = (
            resource_limits.model_copy()
            if resource_limits is not None
            else McpResourceLimitsPolicy()
        )
        self._heartbeat_policy = (
            heartbeat_policy.model_copy()
            if heartbeat_policy is not None
            else McpHeartbeatPolicy()
        )
        self._memory_sampler: Callable[[int], float | None] = (
            rss_sampler if rss_sampler is not None else get_process_rss_mb
        )
        self._stop_budget_s = stop_budget_s
        self._monitor_stop = threading.Event()
        self._monitor_thread = threading.Thread(
            target=self._monitor_loop,
            name="mcp-process-supervisor",
            daemon=True,
        )
        self._monitor_thread.start()

    @property
    def restart_policy(self) -> McpWorkerRestartPolicy:
        return self._restart_policy

    @property
    def resource_limits(self) -> McpResourceLimitsPolicy:
        return self._resource_limits

    @property
    def heartbeat_policy(self) -> McpHeartbeatPolicy:
        return self._heartbeat_policy

    def _check_admission(self, instance_id: str, is_restart: bool = False) -> None:
        policy = self._resource_limits
        with self._lock:
            # Active workers are those in starting/running states or currently restarting.
            # When checking admission for a restarting worker, exclude itself.
            other_active = [
                r for iid, r in self._workers.items()
                if iid != instance_id and (r.state in ("starting", "running") or r.restarting)
            ]
            active_count = len(other_active) + 1  # including the candidate worker

            if policy.max_process_workers > 0 and active_count > policy.max_process_workers:
                action = "restart" if is_restart else "spawn"
                reason = (
                    f"Cannot {action} worker '{instance_id}': "
                    f"active worker limit ({policy.max_process_workers}) reached"
                )
                if not is_restart:
                    logger.warning(
                        "mcp_worker_spawn_admission_rejected instance_id=%s reason=%s",
                        instance_id,
                        reason,
                    )
                raise McpAdmissionError(reason)

            if policy.max_total_rss_mb > 0.0:
                # Sum RSS of active workers (or default estimate if not sampled yet)
                current_rss = 0.0
                for r in other_active:
                    if r.rss_mb is not None:
                        current_rss += r.rss_mb
                    else:
                        current_rss += policy.default_worker_rss_estimate_mb
                projected_mb = current_rss + policy.default_worker_rss_estimate_mb
                if projected_mb > policy.max_total_rss_mb:
                    action = "restart" if is_restart else "spawn"
                    reason = (
                        f"Cannot {action} worker '{instance_id}': "
                        f"projected memory budget ({projected_mb:.1f} MB) "
                        f"exceeds maximum ({policy.max_total_rss_mb:.1f} MB)"
                    )
                    if not is_restart:
                        logger.warning(
                            "mcp_worker_spawn_admission_rejected instance_id=%s reason=%s",
                            instance_id,
                            reason,
                        )
                    raise McpAdmissionError(reason)

    def is_restarting(self, instance_id: str) -> bool:
        with self._lock:
            record = self._workers.get(instance_id)
            return bool(record is not None and record.restarting)

    def retry_count(self, instance_id: str) -> int:
        with self._lock:
            record = self._workers.get(instance_id)
            return 0 if record is None else record.retry_count

    def spawn_worker(
        self,
        instance_id: str,
        *,
        host: str,
        port: int,
        tools: list[Any],
        variables: dict[str, str],
        hidden_keys: set[str],
        overridable_keys: set[str],
        name: str | None = None,
        start_timeout: float = 15.0,
        server_type: Literal["local", "proxy"] = "local",
        upstream_url: str | None = None,
        upstream_transport: Literal["streamable_http", "sse"] = "streamable_http",
        headers: dict[str, str] | None = None,
        timeout: float = 30.0,
    ) -> None:
        """Spawn a headless worker and wait until STARTED or START_FAILED."""
        spec = _WorkerSpawnSpec(
            host=host,
            port=port,
            tools=deepcopy(list(tools)),
            variables=dict(variables),
            hidden_keys=set(hidden_keys),
            overridable_keys=set(overridable_keys),
            name=name,
            start_timeout=start_timeout,
            server_type=server_type,
            upstream_url=upstream_url,
            upstream_transport=upstream_transport,
            headers=dict(headers or {}),
            timeout=timeout,
        )
        with self._lock:
            existing = self._workers.get(instance_id)
            if existing is not None and existing.process.is_alive():
                raise RuntimeError(
                    f"MCP worker already running for instance {instance_id}"
                )
            self._check_admission(instance_id, is_restart=False)
            parent_conn, child_conn = self._ctx.Pipe(duplex=True)
            process = self._ctx.Process(
                target=worker_main,
                args=(child_conn,),
                name=f"mcp-worker-{instance_id}",
                daemon=False,
            )
            record = _WorkerRecord(
                instance_id=instance_id,
                process=process,
                parent_conn=parent_conn,
                spec=spec,
            )
            self._workers[instance_id] = record
            process.start()
            logger.info(
                "mcp_worker_spawned instance_id=%s pid=%s host=%s port=%d "
                "tool_count=%d",
                instance_id,
                process.pid,
                host,
                port,
                len(tools),
            )
            # Parent owns parent_conn; close child's end in parent after start.
            try:
                child_conn.close()
            except Exception:
                pass
            self._start_reader(record)

        start_msg = make_message(
            "START",
            host=host,
            port=port,
            name=name or instance_id,
            tools=encode_tools(tools),
            variables=dict(variables),
            hidden_keys=list(hidden_keys),
            overridable_keys=list(overridable_keys),
            server_type=server_type,
            upstream_url=upstream_url,
            upstream_transport=upstream_transport,
            headers=dict(headers or {}),
            timeout=timeout,
        )
        self._send(instance_id, start_msg)
        try:
            self._wait_started(instance_id, timeout=start_timeout)
        except Exception:
            self.stop_worker(instance_id)
            raise

    def update_tools(self, instance_id: str, tools: list[Any]) -> bool:
        """Send UPDATE_TOOLS to a running worker; return False if unavailable."""
        with self._lock:
            record = self._workers.get(instance_id)
            if record is None:
                return False
            if record.spec is not None:
                record.spec.tools = deepcopy(list(tools))
            if record.restarting:
                return True
            if (
                record.state != "running"
                or not record.process.is_alive()
            ):
                return False
            conn = record.parent_conn
        try:
            payload = make_message("UPDATE_TOOLS", tools=encode_tools(tools))
            conn.send(payload)
            logger.debug(
                "mcp_worker_update_tools_sent instance_id=%s tool_count=%d",
                instance_id,
                len(tools),
            )
            return True
        except (BrokenPipeError, OSError, EOFError, ValueError, TypeError):
            logger.warning(
                "mcp_worker_update_tools_send_failed instance_id=%s",
                instance_id,
            )
            return False

    def update_variables(
        self,
        instance_id: str,
        variables: dict[str, str],
        hidden_keys: set[str],
        overridable_keys: set[str],
    ) -> None:
        with self._lock:
            record = self._workers.get(instance_id)
            if record is None:
                raise KeyError(f"Unknown MCP worker: {instance_id}")
            if record.spec is not None:
                record.spec.variables = dict(variables)
                record.spec.hidden_keys = set(hidden_keys)
                record.spec.overridable_keys = set(overridable_keys)
            if (
                record.restarting
                or record.state != "running"
                or not record.process.is_alive()
            ):
                return
            conn = record.parent_conn
        try:
            conn.send(
                make_message(
                    "UPDATE_VARIABLES",
                    variables=dict(variables),
                    hidden_keys=list(hidden_keys),
                    overridable_keys=list(overridable_keys),
                )
            )
        except (BrokenPipeError, OSError, EOFError):
            logger.warning(
                "mcp_worker_update_variables_send_failed instance_id=%s",
                instance_id,
            )

    def send_debug_opcode(self, instance_id: str, opcode: str) -> None:
        """Send a test-only DEBUG_* opcode to the child.

        Rejected unless ``PYPOST_MCP_ALLOW_DEBUG_IPC=1`` is set in this process.
        """
        if opcode not in ("DEBUG_ABORT", "DEBUG_HANG"):
            raise ValueError(f"Unsupported debug opcode: {opcode}")
        if os.environ.get(_ALLOW_DEBUG_IPC_ENV) != "1":
            raise RuntimeError(
                f"{_ALLOW_DEBUG_IPC_ENV}=1 required to send {opcode}"
            )
        self._send(instance_id, make_message(opcode))  # type: ignore[arg-type]

    def is_alive(self, instance_id: str) -> bool:
        with self._lock:
            record = self._workers.get(instance_id)
            if record is None:
                return False
            return bool(record.process.is_alive())

    def state(self, instance_id: str) -> WorkerState | None:
        with self._lock:
            record = self._workers.get(instance_id)
            return None if record is None else record.state

    def last_error(self, instance_id: str) -> str | None:
        with self._lock:
            record = self._workers.get(instance_id)
            return None if record is None else record.last_error

    def stop_worker(
        self,
        instance_id: str,
        timeout: float | None = None,
    ) -> bool:
        """STOP → join → terminate → kill within the stop budget."""
        budget = self._stop_budget_s if timeout is None else timeout
        deadline = time.monotonic() + budget
        with self._lock:
            record = self._workers.get(instance_id)
            if record is None:
                return True
            record.cancel_event.set()
            record.next_retry_deadline = None
            if record.restarting:
                logger.info(
                    "mcp_worker_restart_cancelled instance_id=%s attempt=%d "
                    "reason=operator_stop",
                    instance_id,
                    record.retry_count,
                )
                record.restarting = False
            process = record.process
            parent_conn = record.parent_conn

        if process is not None and process.is_alive():
            logger.info(
                "mcp_worker_stop_requested instance_id=%s pid=%s budget_s=%.3f",
                instance_id,
                process.pid,
                budget,
            )
            try:
                parent_conn.send(make_message("STOP"))
            except (BrokenPipeError, OSError, EOFError):
                pass

            remaining = max(0.0, deadline - time.monotonic())
            process.join(timeout=remaining)

            if process.is_alive():
                logger.warning(
                    "mcp_worker_terminate instance_id=%s pid=%s signal=SIGTERM",
                    instance_id,
                    process.pid,
                )
                try:
                    process.terminate()
                except Exception:
                    pass
                remaining = max(0.0, deadline - time.monotonic())
                process.join(timeout=max(remaining, 0.05))

            if process.is_alive():
                logger.warning(
                    "mcp_worker_kill instance_id=%s pid=%s signal=SIGKILL",
                    instance_id,
                    process.pid,
                )
                try:
                    process.kill()
                except Exception:
                    pass
                remaining = max(0.0, deadline - time.monotonic())
                process.join(timeout=max(remaining, 0.05))

        stopped_cleanly = process is None or not process.is_alive()
        logger.info(
            "mcp_worker_stop_finished instance_id=%s pid=%s alive=%s "
            "exitcode=%s",
            instance_id,
            process.pid if process is not None else None,
            process.is_alive() if process is not None else False,
            process.exitcode if process is not None else None,
        )

        with self._lock:
            if stopped_cleanly:
                record = self._workers.pop(instance_id, None)
            else:
                record.state = "failed"
                record.last_error = "worker stop deadline exceeded"
                return False
            if record is not None:
                record.state = "stopped"
        # Join reader / close Pipe outside the process-table lock so
        # _apply_ipc_message cannot deadlock waiting for the same lock.
        if record is not None:
            self._stop_reader(record)
        return stopped_cleanly

    def shutdown(self) -> None:
        self._monitor_stop.set()
        with self._lock:
            for record in self._workers.values():
                record.cancel_event.set()
                record.next_retry_deadline = None
                if record.restarting:
                    logger.info(
                        "mcp_worker_restart_cancelled instance_id=%s "
                        "attempt=%d reason=supervisor_shutdown",
                        record.instance_id,
                        record.retry_count,
                    )
                    record.restarting = False
        ids = list(self._workers.keys())
        for instance_id in ids:
            try:
                self.stop_worker(instance_id)
            except Exception:
                logger.exception(
                    "mcp_supervisor_shutdown_error instance_id=%s", instance_id
                )
        if (
            self._monitor_thread.is_alive()
            and threading.current_thread() != self._monitor_thread
        ):
            self._monitor_thread.join(timeout=1.0)

    def _send(self, instance_id: str, message: dict[str, Any]) -> None:
        with self._lock:
            record = self._workers.get(instance_id)
            if record is None:
                raise KeyError(f"Unknown MCP worker: {instance_id}")
            conn = record.parent_conn
        try:
            conn.send(message)
        except (BrokenPipeError, OSError, EOFError) as exc:
            raise RuntimeError(
                f"IPC send failed for MCP worker {instance_id}"
            ) from exc

    def _wait_started(self, instance_id: str, timeout: float) -> None:
        """Wait for STARTED/START_FAILED via the dedicated reader (no Pipe drain)."""
        deadline = time.monotonic() + timeout
        while time.monotonic() < deadline:
            with self._lock:
                record = self._workers.get(instance_id)
                if record is None:
                    raise RuntimeError(f"MCP worker vanished: {instance_id}")
                if record.state == "running":
                    return
                if record.state == "failed":
                    raise RuntimeError(
                        record.last_error or f"MCP worker failed: {instance_id}"
                    )
                if not record.process.is_alive() and record.state == "starting":
                    exitcode = record.process.exitcode
                    record.state = "failed"
                    record.last_error = (
                        f"worker exited during start (exitcode={exitcode})"
                    )
                    raise RuntimeError(record.last_error)
                started_event = record.started_event
            remaining = deadline - time.monotonic()
            if remaining <= 0:
                break
            started_event.wait(timeout=min(0.1, remaining))
        raise TimeoutError(
            f"MCP worker {instance_id} did not report STARTED within {timeout}s"
        )

    def _start_reader(self, record: _WorkerRecord) -> None:
        """Start a dedicated demux thread that alone owns poll+recv on the Pipe."""
        thread = threading.Thread(
            target=self._reader_loop,
            args=(record.instance_id, record.parent_conn, record.reader_stop),
            name=f"mcp-ipc-reader-{record.instance_id}",
            daemon=True,
        )
        record.reader_thread = thread
        thread.start()

    def _stop_reader(self, record: _WorkerRecord) -> None:
        """Signal stop and join; must not run while holding ``_lock``."""
        record.reader_stop.set()
        # Closing the Pipe unblocks poll/recv so join cannot stall forever.
        try:
            record.parent_conn.close()
        except Exception:
            pass
        thread = record.reader_thread
        if thread is not None and thread.is_alive():
            thread.join(timeout=1.0)
        record.reader_thread = None

    def _reader_loop(
        self,
        instance_id: str,
        conn: Any,
        stop_event: threading.Event,
    ) -> None:
        """Single-threaded Pipe ownership: poll+recv never races another drain."""
        while not stop_event.is_set():
            try:
                if not conn.poll(0.1):
                    continue
                message = conn.recv()
            except (EOFError, OSError, BrokenPipeError):
                break
            except Exception:
                logger.exception(
                    "mcp_ipc_reader_error instance_id=%s", instance_id
                )
                break
            self._apply_ipc_message(instance_id, message)

    def _apply_ipc_message(self, instance_id: str, message: Any) -> None:
        if not isinstance(message, dict):
            return
        try:
            validate_message_version(message)
        except McpProtocolVersionError as exc:
            logger.error(
                "mcp_supervisor_ipc_version_rejected instance_id=%s received_v=%s "
                "supported=%s error=%s",
                instance_id,
                getattr(exc, "received_v", None),
                getattr(exc, "supported_versions", None),
                exc,
            )
            with self._lock:
                record = self._workers.get(instance_id)
                if record is None:
                    return
                if record.state == "starting":
                    record.state = "failed"
                    record.last_error = (
                        f"Incompatible IPC protocol version: {exc}"
                    )
                    record.started_event.set()
            return
        msg_type = message.get("type")
        with self._lock:
            record = self._workers.get(instance_id)
            if record is None:
                return
            if msg_type == "STARTED":
                record.state = "running"
                record.started_at = time.monotonic()
                record.started_event.set()
                logger.info(
                    "mcp_worker_started instance_id=%s pid=%s",
                    instance_id,
                    record.process.pid,
                )
            elif msg_type == "START_FAILED":
                record.state = "failed"
                record.last_error = str(
                    message.get("message") or "start failed"
                )
                record.started_event.set()
                logger.error(
                    "mcp_worker_start_failed instance_id=%s pid=%s error=%s",
                    instance_id,
                    record.process.pid,
                    record.last_error,
                )
            elif msg_type == "ACK":
                logger.debug(
                    "mcp_worker_ipc_ack instance_id=%s pid=%s correlating=%s",
                    instance_id,
                    record.process.pid,
                    message.get("correlating"),
                )
            elif msg_type == "WORKER_ERROR":
                logger.error(
                    "mcp_worker_ipc_error instance_id=%s pid=%s message=%s",
                    instance_id,
                    record.process.pid,
                    message.get("message"),
                )
            elif msg_type == "HEARTBEAT_PONG":
                received_nonce = message.get("nonce")
                if (
                    record.pending_heartbeat_nonce is not None
                    and received_nonce == record.pending_heartbeat_nonce
                ):
                    now_ts = time.monotonic()
                    latency_s = (
                        now_ts - record.pending_heartbeat_sent_at
                        if record.pending_heartbeat_sent_at > 0.0
                        else 0.0
                    )
                    record.pending_heartbeat_nonce = None
                    record.pending_heartbeat_sent_at = 0.0
                    record.last_heartbeat_pong_at = now_ts
                    logger.debug(
                        "mcp_worker_heartbeat_pong instance_id=%s pid=%s latency_s=%.4f",
                        instance_id,
                        record.process.pid if record.process else None,
                        latency_s,
                    )
                else:
                    logger.warning(
                        "mcp_worker_heartbeat_pong_mismatch instance_id=%s expected=%s got=%s",
                        instance_id,
                        record.pending_heartbeat_nonce,
                        received_nonce,
                    )

    def _monitor_loop(self) -> None:
        """Watch child liveness, reset windows, and backoff retries."""
        while not self._monitor_stop.wait(0.05):
            now = time.monotonic()
            unexpected: list[tuple[str, int | None]] = []
            restarting_events: list[tuple[str, int, float, int | None]] = []
            restart_attempts: list[_WorkerRecord] = []
            readers_to_stop: list[_WorkerRecord] = []

            with self._lock:
                for instance_id, record in list(self._workers.items()):
                    # 1. Reset window check for running workers
                    if (
                        record.state == "running"
                        and record.started_at is not None
                        and (now - record.started_at)
                        >= self._restart_policy.healthy_reset_window_s
                        and record.retry_count > 0
                    ):
                        prev_count = record.retry_count
                        uptime_s = now - record.started_at
                        record.retry_count = 0
                        pid = record.process.pid if record.process else None
                        logger.info(
                            "mcp_worker_restart_counter_reset instance_id=%s "
                            "pid=%s uptime_s=%.2f previous_retry_count=%d",
                            instance_id,
                            pid,
                            uptime_s,
                            prev_count,
                        )

                    # 2. Check if a restarting worker's backoff deadline has elapsed
                    if (
                        record.restarting
                        and record.next_retry_deadline is not None
                        and now >= record.next_retry_deadline
                        and not record.cancel_event.is_set()
                    ):
                        record.next_retry_deadline = None
                        restart_attempts.append(record)

                    # 3. Check for unexpected exits
                    if (
                        record.state in ("starting", "running")
                        and not record.restarting
                        and record.process is not None
                        and not record.process.is_alive()
                    ):
                        exitcode = record.process.exitcode
                        if record.state == "starting":
                            # Initial start failure (FR7)
                            record.state = "failed"
                            record.last_error = (
                                f"worker exited during start (exitcode={exitcode})"
                            )
                            record.started_event.set()
                            logger.error(
                                "mcp_worker_unexpected_exit instance_id=%s "
                                "pid=%s exitcode=%s prior_state=starting",
                                instance_id,
                                record.process.pid,
                                exitcode,
                            )
                        elif record.state == "running":
                            # Crashed from running state
                            if (
                                not self._restart_policy.enabled
                                or record.retry_count
                                >= self._restart_policy.max_retries
                            ):
                                record.state = "failed"
                                record.last_error = (
                                    f"unexpected worker exit (exitcode={exitcode})"
                                )
                                if (
                                    self._restart_policy.enabled
                                    and record.retry_count
                                    >= self._restart_policy.max_retries
                                ):
                                    logger.error(
                                        "mcp_worker_restart_exhausted "
                                        "instance_id=%s attempts=%d "
                                        "max_retries=%d exitcode=%s",
                                        instance_id,
                                        record.retry_count,
                                        self._restart_policy.max_retries,
                                        exitcode,
                                    )
                                else:
                                    logger.error(
                                        "mcp_worker_unexpected_exit "
                                        "instance_id=%s pid=%s exitcode=%s "
                                        "prior_state=running",
                                        instance_id,
                                        record.process.pid,
                                        exitcode,
                                    )
                                unexpected.append((instance_id, exitcode))
                                readers_to_stop.append(record)
                            else:
                                record.retry_count += 1
                                delay_s = self._restart_policy.backoff_for_attempt(
                                    record.retry_count
                                )
                                record.next_retry_deadline = now + delay_s
                                record.restarting = True
                                record.state = "starting"
                                record.cancel_event.clear()
                                record.started_event.clear()
                                logger.info(
                                    "mcp_worker_restart_scheduled "
                                    "instance_id=%s attempt=%d max_retries=%d "
                                    "delay_s=%.2f exitcode=%s",
                                    instance_id,
                                    record.retry_count,
                                    self._restart_policy.max_retries,
                                    delay_s,
                                    exitcode,
                                )
                                restarting_events.append(
                                    (
                                        instance_id,
                                        record.retry_count,
                                        delay_s,
                                        exitcode,
                                    )
                                )
                                readers_to_stop.append(record)

                    # 4. Periodic memory sampling and ceiling enforcement
                    if (
                        record.state == "running"
                        and not record.restarting
                        and record.process is not None
                        and record.process.is_alive()
                    ):
                        pid = record.process.pid
                        if (
                            pid is not None
                            and (now - record.last_rss_sample_at)
                            >= self._resource_limits.memory_sample_interval_s
                        ):
                            record.last_rss_sample_at = now
                            rss = self._memory_sampler(pid)
                            record.rss_mb = rss
                            if rss is not None:
                                if (
                                    self._resource_limits.soft_memory_limit_mb > 0.0
                                    and rss >= self._resource_limits.soft_memory_limit_mb
                                ):
                                    if not record.soft_limit_warned:
                                        logger.warning(
                                            "mcp_worker_memory_warning instance_id=%s pid=%d "
                                            "rss_mb=%.1f soft_limit_mb=%.1f",
                                            instance_id,
                                            pid,
                                            rss,
                                            self._resource_limits.soft_memory_limit_mb,
                                        )
                                        record.soft_limit_warned = True
                                elif (
                                    self._resource_limits.soft_memory_limit_mb > 0.0
                                    and rss < self._resource_limits.soft_memory_limit_mb
                                ):
                                    record.soft_limit_warned = False

                                if (
                                    self._resource_limits.hard_memory_limit_mb > 0.0
                                    and rss >= self._resource_limits.hard_memory_limit_mb
                                ):
                                    logger.error(
                                        "mcp_worker_memory_exceeded instance_id=%s pid=%d "
                                        "rss_mb=%.1f hard_limit_mb=%.1f",
                                        instance_id,
                                        pid,
                                        rss,
                                        self._resource_limits.hard_memory_limit_mb,
                                    )
                                    record.state = "failed"
                                    record.last_error = "memory_limit_exceeded"
                                    record.restarting = False
                                    record.cancel_event.set()
                                    record.next_retry_deadline = None
                                    proc_to_kill = record.process
                                    try:
                                        if proc_to_kill.is_alive():
                                            proc_to_kill.terminate()
                                            proc_to_kill.join(timeout=0.2)
                                            if proc_to_kill.is_alive():
                                                proc_to_kill.kill()
                                                proc_to_kill.join(timeout=0.2)
                                    except Exception:
                                        pass
                                    readers_to_stop.append(record)
                                    unexpected.append((instance_id, proc_to_kill.exitcode))

                    # 5. Active HEARTBEAT watchdog checks
                    if (
                        self._heartbeat_policy.enabled
                        and record.state == "running"
                        and not record.restarting
                        and record.process is not None
                        and record.process.is_alive()
                    ):
                        if (
                            record.pending_heartbeat_nonce is not None
                            and (now - record.pending_heartbeat_sent_at)
                            > self._heartbeat_policy.timeout_s
                        ):
                            logger.error(
                                "mcp_worker_heartbeat_timeout instance_id=%s pid=%s "
                                "timeout_s=%.2f",
                                instance_id,
                                record.process.pid,
                                self._heartbeat_policy.timeout_s,
                            )
                            proc_to_kill = record.process
                            try:
                                if proc_to_kill.is_alive():
                                    proc_to_kill.terminate()
                                    proc_to_kill.join(timeout=0.2)
                                    if proc_to_kill.is_alive():
                                        proc_to_kill.kill()
                                        proc_to_kill.join(timeout=0.2)
                            except Exception:
                                pass
                            record.pending_heartbeat_nonce = None
                            record.pending_heartbeat_sent_at = 0.0
                            record.last_error = (
                                f"heartbeat timeout ({self._heartbeat_policy.timeout_s}s)"
                            )
                            exitcode = proc_to_kill.exitcode
                            if (
                                self._restart_policy.enabled
                                and record.retry_count < self._restart_policy.max_retries
                            ):
                                record.retry_count += 1
                                delay_s = self._restart_policy.backoff_for_attempt(
                                    record.retry_count
                                )
                                record.next_retry_deadline = now + delay_s
                                record.restarting = True
                                record.state = "starting"
                                record.cancel_event.clear()
                                record.started_event.clear()
                                logger.info(
                                    "mcp_worker_restart_scheduled instance_id=%s attempt=%d "
                                    "max_retries=%d delay_s=%.2f exitcode=%s "
                                    "reason=heartbeat_timeout",
                                    instance_id,
                                    record.retry_count,
                                    self._restart_policy.max_retries,
                                    delay_s,
                                    exitcode,
                                )
                                restarting_events.append(
                                    (
                                        instance_id,
                                        record.retry_count,
                                        delay_s,
                                        exitcode,
                                    )
                                )
                                readers_to_stop.append(record)
                            else:
                                record.state = "failed"
                                record.restarting = False
                                record.cancel_event.set()
                                record.next_retry_deadline = None
                                if (
                                    self._restart_policy.enabled
                                    and record.retry_count >= self._restart_policy.max_retries
                                ):
                                    logger.error(
                                        "mcp_worker_restart_exhausted instance_id=%s "
                                        "attempts=%d max_retries=%d exitcode=%s",
                                        instance_id,
                                        record.retry_count,
                                        self._restart_policy.max_retries,
                                        exitcode,
                                    )
                                unexpected.append((instance_id, exitcode))
                                readers_to_stop.append(record)
                        elif (
                            record.pending_heartbeat_nonce is None
                            and (
                                record.last_heartbeat_sent_at == 0.0
                                or (now - record.last_heartbeat_sent_at)
                                >= self._heartbeat_policy.interval_s
                            )
                        ):
                            nonce = uuid.uuid4().hex[:16]
                            record.pending_heartbeat_nonce = nonce
                            record.pending_heartbeat_sent_at = now
                            record.last_heartbeat_sent_at = now
                            try:
                                record.parent_conn.send(
                                    make_message("HEARTBEAT", nonce=nonce)
                                )
                            except (BrokenPipeError, OSError, EOFError, ValueError):
                                pass

            # Stop dead readers outside the lock
            for rec in readers_to_stop:
                self._stop_reader(rec)

            # Callbacks outside the lock
            for instance_id, attempt, delay_s, exitcode in restarting_events:
                if self._on_worker_restarting is not None:
                    try:
                        self._on_worker_restarting(
                            instance_id, attempt, delay_s, exitcode
                        )
                    except Exception:
                        logger.exception(
                            "mcp_supervisor_restarting_callback_error "
                            "instance_id=%s",
                            instance_id,
                        )

            for instance_id, exitcode in unexpected:
                if self._on_unexpected_exit is not None:
                    try:
                        self._on_unexpected_exit(instance_id, exitcode)
                    except Exception:
                        logger.exception(
                            "mcp_supervisor_unexpected_exit_callback_error "
                            "instance_id=%s",
                            instance_id,
                        )

            # Launch restart attempts asynchronously
            for rec in restart_attempts:
                threading.Thread(
                    target=self._attempt_restart,
                    args=(rec,),
                    name=f"mcp-restart-{rec.instance_id}",
                    daemon=True,
                ).start()

    def _attempt_restart(self, record: _WorkerRecord) -> None:
        instance_id = record.instance_id
        if record.cancel_event.is_set() or self._monitor_stop.is_set():
            return
        spec = record.spec
        if spec is None:
            return

        try:
            self._check_admission(instance_id, is_restart=True)
        except McpAdmissionError as err:
            logger.error(
                "mcp_worker_restart_admission_rejected instance_id=%s reason=%s",
                instance_id,
                err,
            )
            with self._lock:
                record.state = "failed"
                record.restarting = False
                record.last_error = str(err)
                record.next_retry_deadline = None
            if self._on_unexpected_exit is not None:
                try:
                    self._on_unexpected_exit(instance_id, None)
                except Exception:
                    logger.exception(
                        "mcp_supervisor_unexpected_exit_callback_error"
                    )
            return

        with self._lock:
            if record.cancel_event.is_set() or self._monitor_stop.is_set():
                return
            parent_conn, child_conn = self._ctx.Pipe(duplex=True)
            process = self._ctx.Process(
                target=worker_main,
                args=(child_conn,),
                name=f"mcp-worker-{instance_id}",
                daemon=False,
            )
            record.process = process
            record.parent_conn = parent_conn
            record.reader_stop = threading.Event()
            record.started_event.clear()
            try:
                process.start()
            except Exception as exc:
                logger.error(
                    "mcp_worker_restart_process_start_failed instance_id=%s error=%s",
                    instance_id,
                    exc,
                )
                self._handle_restart_failure(record, str(exc), None)
                return

            logger.info(
                "mcp_worker_spawned instance_id=%s pid=%s host=%s port=%d "
                "tool_count=%d",
                instance_id,
                process.pid,
                spec.host,
                spec.port,
                len(spec.tools),
            )
            try:
                child_conn.close()
            except Exception:
                pass
            self._start_reader(record)

        start_msg = make_message(
            "START",
            host=spec.host,
            port=spec.port,
            name=spec.name or instance_id,
            tools=encode_tools(spec.tools),
            variables=dict(spec.variables),
            hidden_keys=list(spec.hidden_keys),
            overridable_keys=list(spec.overridable_keys),
            server_type=spec.server_type,
            upstream_url=spec.upstream_url,
            upstream_transport=spec.upstream_transport,
            headers=dict(spec.headers),
            timeout=spec.timeout,
        )
        try:
            self._send(instance_id, start_msg)
        except Exception as exc:
            logger.error(
                "mcp_worker_restart_start_send_failed instance_id=%s error=%s",
                instance_id,
                exc,
            )
            self._handle_restart_failure(record, str(exc), None)
            return

        deadline = time.monotonic() + spec.start_timeout
        success = False
        fail_reason: str | None = None
        exitcode: int | None = None

        while time.monotonic() < deadline:
            if record.cancel_event.is_set() or self._monitor_stop.is_set():
                return
            with self._lock:
                if record.state == "running":
                    success = True
                    break
                if record.state == "failed":
                    fail_reason = record.last_error or "start failed"
                    break
                if not record.process.is_alive():
                    exitcode = record.process.exitcode
                    fail_reason = (
                        f"worker exited during restart (exitcode={exitcode})"
                    )
                    break
            record.started_event.wait(timeout=0.05)

        if record.cancel_event.is_set() or self._monitor_stop.is_set():
            return

        if success:
            with self._lock:
                record.state = "running"
                record.restarting = False
                record.started_at = time.monotonic()
                record.next_retry_deadline = None
                record.last_error = None
                record.last_heartbeat_sent_at = 0.0
                record.last_heartbeat_pong_at = 0.0
                record.pending_heartbeat_nonce = None
                record.pending_heartbeat_sent_at = 0.0
                pid = record.process.pid
                attempt = record.retry_count
            logger.info(
                "mcp_worker_restarted instance_id=%s pid=%s attempt=%d "
                "max_retries=%d",
                instance_id,
                pid,
                attempt,
                self._restart_policy.max_retries,
            )
            if self._on_worker_restarted is not None:
                try:
                    self._on_worker_restarted(instance_id, attempt)
                except Exception:
                    logger.exception(
                        "mcp_supervisor_worker_restarted_callback_error "
                        "instance_id=%s",
                        instance_id,
                    )
        else:
            if fail_reason is None:
                fail_reason = f"restart timed out after {spec.start_timeout}s"
            self._handle_restart_failure(record, fail_reason, exitcode)

    def _handle_restart_failure(
        self, record: _WorkerRecord, fail_reason: str, exitcode: int | None
    ) -> None:
        instance_id = record.instance_id
        scheduled: tuple[int, float] | None = None
        exhausted = False
        with self._lock:
            if record.cancel_event.is_set() or self._monitor_stop.is_set():
                return
            if record.retry_count < self._restart_policy.max_retries:
                record.retry_count += 1
                delay_s = self._restart_policy.backoff_for_attempt(
                    record.retry_count
                )
                record.next_retry_deadline = time.monotonic() + delay_s
                record.restarting = True
                record.state = "starting"
                record.started_event.clear()
                logger.info(
                    "mcp_worker_restart_scheduled instance_id=%s attempt=%d "
                    "max_retries=%d delay_s=%.2f exitcode=%s",
                    instance_id,
                    record.retry_count,
                    self._restart_policy.max_retries,
                    delay_s,
                    exitcode,
                )
                scheduled = (record.retry_count, delay_s)
            else:
                record.restarting = False
                record.state = "failed"
                record.last_error = fail_reason
                logger.error(
                    "mcp_worker_restart_exhausted instance_id=%s attempts=%d "
                    "max_retries=%d exitcode=%s",
                    instance_id,
                    record.retry_count,
                    self._restart_policy.max_retries,
                    exitcode,
                )
                exhausted = True

        self._stop_reader(record)

        if not exhausted and scheduled is not None:
            attempt, delay_s = scheduled
            if self._on_worker_restarting is not None:
                try:
                    self._on_worker_restarting(
                        instance_id, attempt, delay_s, exitcode
                    )
                except Exception:
                    logger.exception(
                        "mcp_supervisor_restarting_callback_error"
                    )
        elif exhausted:
            if self._on_unexpected_exit is not None:
                try:
                    self._on_unexpected_exit(instance_id, exitcode)
                except Exception:
                    logger.exception(
                        "mcp_supervisor_unexpected_exit_callback_error"
                    )
