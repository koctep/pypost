"""Process table and SIGTERM→SIGKILL reclamation for MCP workers (PYPOST-1439)."""

from __future__ import annotations

import logging
import multiprocessing
import os
import threading
import time
from dataclasses import dataclass, field
from typing import Any, Callable, Literal

from pypost.core.mcp_worker_ipc import encode_tools, make_message
from pypost.core.mcp_worker_process import worker_main

logger = logging.getLogger(__name__)

WorkerState = Literal["starting", "running", "failed", "stopped"]

# Aligned with adaptive join / evaluation §4.1.
DEFAULT_STOP_BUDGET_S = 2.0

# Same family as PYPOST_MCP_TEST_ECHO_VARS — must be set for DEBUG_* IPC.
_ALLOW_DEBUG_IPC_ENV = "PYPOST_MCP_ALLOW_DEBUG_IPC"


@dataclass
class _WorkerRecord:
    instance_id: str
    process: Any
    parent_conn: Any
    state: WorkerState = "starting"
    last_error: str | None = None
    started_event: threading.Event = field(default_factory=threading.Event)
    reader_stop: threading.Event = field(default_factory=threading.Event)
    reader_thread: threading.Thread | None = None


class McpProcessSupervisor:
    """Owns child PIDs, IPC pipes, and stop escalation for process-mode MCP."""

    def __init__(
        self,
        *,
        on_unexpected_exit: Callable[[str, int | None], None] | None = None,
        stop_budget_s: float = DEFAULT_STOP_BUDGET_S,
    ) -> None:
        self._ctx = multiprocessing.get_context("spawn")
        self._workers: dict[str, _WorkerRecord] = {}
        self._lock = threading.RLock()
        self._on_unexpected_exit = on_unexpected_exit
        self._stop_budget_s = stop_budget_s
        self._monitor_stop = threading.Event()
        self._monitor_thread = threading.Thread(
            target=self._monitor_loop,
            name="mcp-process-supervisor",
            daemon=True,
        )
        self._monitor_thread.start()

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
    ) -> None:
        """Spawn a headless worker and wait until STARTED or START_FAILED."""
        with self._lock:
            existing = self._workers.get(instance_id)
            if existing is not None and existing.process.is_alive():
                raise RuntimeError(
                    f"MCP worker already running for instance {instance_id}"
                )
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
        )
        self._send(instance_id, start_msg)
        self._wait_started(instance_id, timeout=start_timeout)

    def update_variables(
        self,
        instance_id: str,
        variables: dict[str, str],
        hidden_keys: set[str],
        overridable_keys: set[str],
    ) -> None:
        self._send(
            instance_id,
            make_message(
                "UPDATE_VARIABLES",
                variables=dict(variables),
                hidden_keys=list(hidden_keys),
                overridable_keys=list(overridable_keys),
            ),
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
            process = record.process
            parent_conn = record.parent_conn

        if process.is_alive():
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

        stopped_cleanly = not process.is_alive()
        logger.info(
            "mcp_worker_stop_finished instance_id=%s pid=%s alive=%s "
            "exitcode=%s",
            instance_id,
            process.pid,
            process.is_alive(),
            process.exitcode,
        )

        with self._lock:
            record = self._workers.pop(instance_id, None)
            if record is not None:
                record.state = "stopped"
        # Join reader / close Pipe outside the process-table lock so
        # _apply_ipc_message cannot deadlock waiting for the same lock.
        if record is not None:
            self._stop_reader(record)
        return stopped_cleanly

    def shutdown(self) -> None:
        self._monitor_stop.set()
        ids = list(self._workers.keys())
        for instance_id in ids:
            try:
                self.stop_worker(instance_id)
            except Exception:
                logger.exception(
                    "mcp_supervisor_shutdown_error instance_id=%s", instance_id
                )

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
        msg_type = message.get("type")
        with self._lock:
            record = self._workers.get(instance_id)
            if record is None:
                return
            if msg_type == "STARTED":
                record.state = "running"
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

    def _monitor_loop(self) -> None:
        """Watch child liveness only — never touch the Pipe (reader owns it)."""
        while not self._monitor_stop.wait(0.1):
            unexpected: list[tuple[str, int | None]] = []
            with self._lock:
                for instance_id, record in list(self._workers.items()):
                    if (
                        record.state in ("starting", "running")
                        and not record.process.is_alive()
                    ):
                        exitcode = record.process.exitcode
                        if record.state == "running":
                            record.state = "failed"
                            record.last_error = (
                                f"unexpected worker exit (exitcode={exitcode})"
                            )
                            unexpected.append((instance_id, exitcode))
                            logger.error(
                                "mcp_worker_unexpected_exit instance_id=%s "
                                "pid=%s exitcode=%s prior_state=running",
                                instance_id,
                                record.process.pid,
                                exitcode,
                            )
                        elif record.state == "starting":
                            record.state = "failed"
                            record.last_error = (
                                f"worker exited during start "
                                f"(exitcode={exitcode})"
                            )
                            record.started_event.set()
                            logger.error(
                                "mcp_worker_unexpected_exit instance_id=%s "
                                "pid=%s exitcode=%s prior_state=starting",
                                instance_id,
                                record.process.pid,
                                exitcode,
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
