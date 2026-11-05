"""Headless MCP worker entrypoint for process-mode isolation (PYPOST-1439).

Must not import PySide6 / Qt — keep the child RSS near the evaluation baseline.
"""

from __future__ import annotations

import asyncio
import logging
import os
import sys
import threading
import time
from typing import Any

import uvicorn

from pypost.core.mcp_server_impl import MCPServerImpl
from pypost.core.mcp_worker_ipc import (
    decode_tools,
    make_message,
    message_type,
)
from pypost.core.server_bind import (
    drain_pending_tasks,
    format_bind_error,
)

logger = logging.getLogger(__name__)

# Same family as PYPOST_MCP_TEST_ECHO_VARS — production workers ignore DEBUG_*.
_ALLOW_DEBUG_IPC_ENV = "PYPOST_MCP_ALLOW_DEBUG_IPC"


def _debug_ipc_allowed() -> bool:
    return os.environ.get(_ALLOW_DEBUG_IPC_ENV) == "1"


class _SnapshotStore:
    """Mutable variable snapshots owned by the child process."""

    def __init__(
        self,
        variables: dict[str, str],
        hidden_keys: set[str],
        overridable_keys: set[str],
    ) -> None:
        self.variables = dict(variables)
        self.hidden_keys = set(hidden_keys)
        self.overridable_keys = set(overridable_keys)

    def update(
        self,
        variables: dict[str, str],
        hidden_keys: set[str],
        overridable_keys: set[str],
    ) -> None:
        self.variables = dict(variables)
        self.hidden_keys = set(hidden_keys)
        self.overridable_keys = set(overridable_keys)


def _run_uvicorn(
    impl: MCPServerImpl,
    host: str,
    port: int,
    stop_flag: dict[str, Any],
    conn: Any,
) -> None:
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    server_instance: uvicorn.Server | None = None
    try:
        app = impl.create_app()
        config = uvicorn.Config(
            app=app,
            host=host,
            port=port,
            loop="asyncio",
            log_config=None,
            log_level="warning",
        )
        server_instance = uvicorn.Server(config)
        # Supervisor owns SIGTERM/SIGKILL; child reacts to IPC STOP.
        # setattr: uvicorn 0.54+ uses capture_signals (no-op off main thread);
        # keep install_signal_handlers override for older uvicorn stubs/APIs.
        setattr(server_instance, "install_signal_handlers", lambda: None)

        original_startup = server_instance.startup

        async def startup_with_notify(sockets=None):
            await original_startup(sockets=sockets)
            try:
                conn.send(
                    make_message(
                        "STARTED",
                        pid=os.getpid(),
                        host=host,
                        port=port,
                    )
                )
            except (BrokenPipeError, OSError, EOFError):
                pass

        setattr(server_instance, "startup", startup_with_notify)

        # Expose for STOP handler.
        stop_flag["server"] = server_instance
        loop.run_until_complete(server_instance.serve())
    except OSError as exc:
        try:
            conn.send(
                make_message(
                    "START_FAILED",
                    message=format_bind_error(exc, host, port, "MCP server"),
                )
            )
        except (BrokenPipeError, OSError, EOFError):
            pass
    except Exception as exc:
        logger.exception("mcp_worker_start_failed")
        try:
            conn.send(
                make_message("START_FAILED", message=f"MCP worker failed: {exc}")
            )
        except (BrokenPipeError, OSError, EOFError):
            pass
    finally:
        drain_pending_tasks(loop)
        loop.close()


def worker_main(conn: Any) -> None:
    """Top-level spawn target: IPC control loop + uvicorn serving."""
    logging.basicConfig(level=logging.WARNING)
    store: _SnapshotStore | None = None
    hang_mode = False
    stop_flag: dict[str, Any] = {"stop": False, "server": None}
    serve_thread = None

    try:
        while True:
            if hang_mode:
                # Ignore STOP; wait for supervisor SIGKILL.
                time.sleep(3600)
                continue

            try:
                if not conn.poll(0.2):
                    continue
                message = conn.recv()
            except (EOFError, OSError, BrokenPipeError):
                break

            if not isinstance(message, dict):
                continue
            msg_type = message_type(message)

            if msg_type == "START":
                if store is not None:
                    continue
                variables = dict(message.get("variables") or {})
                hidden = set(message.get("hidden_keys") or [])
                overridable = set(message.get("overridable_keys") or [])
                store = _SnapshotStore(variables, hidden, overridable)
                tools = decode_tools(list(message.get("tools") or []))
                host = str(message.get("host") or "127.0.0.1")
                port = int(message.get("port") or 0)

                impl = MCPServerImpl(
                    name=str(message.get("name") or "pypost-mcp-worker"),
                    variable_supplier=lambda: dict(store.variables),
                    hidden_keys_supplier=lambda: set(store.hidden_keys),
                    overridable_keys_supplier=lambda: set(
                        store.overridable_keys
                    ),
                )
                impl.register_tools(tools)

                serve_thread = threading.Thread(
                    target=_run_uvicorn,
                    args=(impl, host, port, stop_flag, conn),
                    daemon=True,
                )
                serve_thread.start()

            elif msg_type == "UPDATE_VARIABLES":
                if store is None:
                    continue
                store.update(
                    dict(message.get("variables") or {}),
                    set(message.get("hidden_keys") or []),
                    set(message.get("overridable_keys") or []),
                )
                try:
                    conn.send(make_message("ACK", correlating="UPDATE_VARIABLES"))
                except (BrokenPipeError, OSError, EOFError):
                    pass

            elif msg_type == "HEARTBEAT":
                try:
                    conn.send(
                        make_message(
                            "HEARTBEAT_PONG",
                            nonce=message.get("nonce"),
                        )
                    )
                except (BrokenPipeError, OSError, EOFError):
                    pass

            elif msg_type == "STOP":
                if hang_mode:
                    continue
                stop_flag["stop"] = True
                server = stop_flag.get("server")
                if server is not None:
                    server.should_exit = True
                if serve_thread is not None:
                    serve_thread.join(timeout=1.5)
                try:
                    conn.send(make_message("EXITED"))
                except (BrokenPipeError, OSError, EOFError):
                    pass
                break

            elif msg_type == "DEBUG_ABORT":
                if not _debug_ipc_allowed():
                    logger.warning(
                        "mcp_worker_debug_opcode_rejected opcode=DEBUG_ABORT"
                    )
                    continue
                # Test-only fatal child exit without killing the host.
                os._exit(1)

            elif msg_type == "DEBUG_HANG":
                if not _debug_ipc_allowed():
                    logger.warning(
                        "mcp_worker_debug_opcode_rejected opcode=DEBUG_HANG"
                    )
                    continue
                hang_mode = True
                # Keep uvicorn running but ignore future STOP messages.

    except Exception:
        logger.exception("mcp_worker_fatal")
        try:
            conn.send(make_message("WORKER_ERROR", message="fatal worker error"))
        except Exception:
            pass
        raise
    finally:
        try:
            conn.close()
        except Exception:
            pass


if __name__ == "__main__":
    # Allow `python -m pypost.core.mcp_worker_process` debugging only.
    sys.stderr.write("mcp_worker_process is a spawn target, not a CLI\n")
    sys.exit(2)
