"""Local IPC attach host/client for agent-UI MCP (PYPOST-1207).

Desktop process listens on a well-known AF_UNIX endpoint; the stdio sidecar
connects in ``--attach`` mode and dispatches the same ``ui_*`` catalog over
newline-delimited JSON. Local-only; no remote transport.
"""

from __future__ import annotations

import json
import logging
import os
import socket
import tempfile
import threading
from pathlib import Path
from typing import Any, Final, cast

from PySide6.QtCore import QObject, Qt, Signal, Slot
from PySide6.QtWidgets import QWidget

from pypost.agent.ui_actions import UiActionError
from pypost.agent.ui_drive import MainWindowUiDrive

logger = logging.getLogger(__name__)

ATTACH_PROTOCOL_VERSION: Final = 1
_ENV_ENDPOINT: Final = "PYPOST_AGENT_UI_ATTACH_ENDPOINT"
_DEFAULT_SOCK_NAME: Final = "pypost-agent-ui-attach.sock"


class AttachUnboundError(RuntimeError):
    """No desktop attach host is listening at the endpoint."""


def default_attach_endpoint() -> str:
    """Return the per-user well-known AF_UNIX path (override via env)."""
    override = os.environ.get(_ENV_ENDPOINT)
    if override:
        return override
    runtime = os.environ.get("XDG_RUNTIME_DIR")
    if runtime:
        return str(Path(runtime) / _DEFAULT_SOCK_NAME)
    return str(
        Path(tempfile.gettempdir())
        / f"pypost-agent-ui-attach-{os.getuid()}.sock"
    )


def _recv_line(sock: socket.socket) -> dict[str, Any]:
    buf = bytearray()
    while True:
        chunk = sock.recv(1)
        if not chunk:
            raise ConnectionError("attach peer closed")
        if chunk == b"\n":
            break
        buf.extend(chunk)
    return cast(dict[str, Any], json.loads(buf.decode("utf-8")))


def _send_line(sock: socket.socket, payload: dict[str, Any]) -> None:
    sock.sendall((json.dumps(payload) + "\n").encode("utf-8"))


class AttachClientSession:
    """Sidecar-side UiDriveSession that proxies ``ui_*`` over local IPC."""

    def __init__(
        self,
        endpoint: str | None = None,
        *,
        connect_timeout: float = 2.0,
    ) -> None:
        self._endpoint = endpoint or default_attach_endpoint()
        self._connect_timeout = connect_timeout
        self._sock: socket.socket | None = None
        self._lock = threading.Lock()

    @property
    def endpoint(self) -> str:
        return self._endpoint

    def connect(self) -> None:
        """Bind to a live desktop host or raise ``AttachUnboundError``."""
        if self._sock is not None:
            raise RuntimeError("AttachClientSession already connected")
        sock = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
        sock.settimeout(self._connect_timeout)
        try:
            sock.connect(self._endpoint)
            _send_line(
                sock,
                {"op": "handshake", "version": ATTACH_PROTOCOL_VERSION},
            )
            reply = _recv_line(sock)
        except OSError as exc:
            sock.close()
            logger.warning(
                "agent_ui_attach_bind_failed endpoint=%s reason=connect "
                "error=%s",
                self._endpoint,
                type(exc).__name__,
            )
            raise AttachUnboundError(
                f"attach unbound: no host at {self._endpoint!r}"
            ) from exc
        except (ConnectionError, json.JSONDecodeError, KeyError) as exc:
            sock.close()
            logger.warning(
                "agent_ui_attach_bind_failed endpoint=%s reason=handshake "
                "error=%s",
                self._endpoint,
                type(exc).__name__,
            )
            raise AttachUnboundError(
                f"attach unbound: handshake failed at {self._endpoint!r}"
            ) from exc
        if not reply.get("ok"):
            sock.close()
            logger.warning(
                "agent_ui_attach_bind_failed endpoint=%s reason=rejected",
                self._endpoint,
            )
            raise AttachUnboundError(
                f"attach unbound: host rejected handshake "
                f"at {self._endpoint!r}"
            )
        sock.settimeout(None)
        self._sock = sock
        logger.info(
            "agent_ui_attach_bound endpoint=%s",
            self._endpoint,
        )

    def detach(self) -> None:
        """Close the IPC binding; does not force the desktop host to exit."""
        sock = self._sock
        self._sock = None
        if sock is None:
            return
        try:
            with self._lock:
                try:
                    _send_line(sock, {"op": "detach"})
                    _recv_line(sock)
                except OSError:
                    pass
        finally:
            try:
                sock.close()
            except OSError:
                pass
        logger.info("agent_ui_attach_detached endpoint=%s", self._endpoint)

    def shutdown(self) -> None:
        """Alias for ``detach`` (spawn-session ``finally`` symmetry)."""
        self.detach()

    def _call(self, op: str, **kwargs: Any) -> None:
        sock = self._sock
        if sock is None:
            raise AttachUnboundError("attach unbound: not connected")
        request = {"op": op, **kwargs}
        with self._lock:
            _send_line(sock, request)
            reply = _recv_line(sock)
        if reply.get("ok"):
            return
        error = str(reply.get("error") or "attach ui action failed")
        raise UiActionError(error)

    def ui_click(self, widget_id: str, *, in_current_tab: bool = False) -> None:
        self._call(
            "ui_click",
            widget_id=widget_id,
            in_current_tab=in_current_tab,
        )

    def ui_fill(
        self,
        widget_id: str,
        text: str,
        *,
        in_current_tab: bool = False,
        via_key_clicks: bool = False,
        delay: int = -1,
    ) -> None:
        self._call(
            "ui_fill",
            widget_id=widget_id,
            text=text,
            in_current_tab=in_current_tab,
            via_key_clicks=via_key_clicks,
            delay=delay,
        )

    def ui_select(
        self,
        widget_id: str,
        option: str | int,
        *,
        in_current_tab: bool = False,
    ) -> None:
        payload: dict[str, Any] = {
            "widget_id": widget_id,
            "in_current_tab": in_current_tab,
        }
        if isinstance(option, int):
            payload["option_index"] = option
        else:
            payload["option"] = option
        self._call("ui_select", **payload)

    def ui_send_key(
        self,
        widget_id: str,
        key: str,
        *,
        modifiers: Qt.KeyboardModifier = Qt.KeyboardModifier.NoModifier,
        in_current_tab: bool = False,
    ) -> None:
        self._call(
            "ui_send_key",
            widget_id=widget_id,
            key=key,
            modifiers=int(modifiers.value),
            in_current_tab=in_current_tab,
        )


class _GuiActionBridge(QObject):
    """Marshal attach IPC actions onto the QApplication thread."""

    requested = Signal(object)

    def __init__(self) -> None:
        super().__init__()
        self.requested.connect(self._run, Qt.ConnectionType.QueuedConnection)

    @Slot(object)
    def _run(self, job: object) -> None:
        if callable(job):
            job()


class AgentUiAttachHost:
    """Desktop-side listener that runs ``ui_*`` on the live main window."""

    def __init__(
        self,
        window: QWidget,
        endpoint: str | None = None,
    ) -> None:
        self._endpoint = endpoint or default_attach_endpoint()
        self._drive = MainWindowUiDrive(window)
        self._bridge = _GuiActionBridge()
        self._server: socket.socket | None = None
        self._thread: threading.Thread | None = None
        self._stop = threading.Event()
        self._clients: list[socket.socket] = []
        self._clients_lock = threading.Lock()

    @property
    def endpoint(self) -> str:
        return self._endpoint

    def start(self) -> None:
        """Bind the AF_UNIX endpoint and accept clients in a daemon thread."""
        if self._thread is not None:
            raise RuntimeError("AgentUiAttachHost already started")
        path = Path(self._endpoint)
        server: socket.socket | None = None
        try:
            path.parent.mkdir(parents=True, exist_ok=True)
            if path.exists():
                path.unlink()
            server = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
            server.bind(self._endpoint)
            server.listen(5)
            server.settimeout(0.5)
        except OSError as exc:
            if server is not None:
                try:
                    server.close()
                except OSError:
                    pass
            logger.error(
                "agent_ui_attach_host_start_failed endpoint=%s error=%s",
                self._endpoint,
                type(exc).__name__,
            )
            raise
        self._server = server
        self._stop.clear()
        self._thread = threading.Thread(
            target=self._accept_loop,
            name="pypost-agent-ui-attach-host",
            daemon=True,
        )
        self._thread.start()
        logger.info("agent_ui_attach_host_started endpoint=%s", self._endpoint)

    def stop(self) -> None:
        """Stop accepting; close peers; remove the socket file."""
        self._stop.set()
        server = self._server
        self._server = None
        if server is not None:
            try:
                server.close()
            except OSError:
                pass
        with self._clients_lock:
            clients = list(self._clients)
            self._clients.clear()
        for client in clients:
            try:
                client.close()
            except OSError:
                pass
        thread = self._thread
        self._thread = None
        if thread is not None and thread.is_alive():
            thread.join(timeout=2.0)
        path = Path(self._endpoint)
        if path.exists():
            try:
                path.unlink()
            except OSError:
                pass
        logger.info("agent_ui_attach_host_stopped endpoint=%s", self._endpoint)

    def _accept_loop(self) -> None:
        assert self._server is not None
        while not self._stop.is_set():
            try:
                client, _addr = self._server.accept()
            except socket.timeout:
                continue
            except OSError:
                if self._stop.is_set():
                    break
                continue
            with self._clients_lock:
                self._clients.append(client)
                peer_count = len(self._clients)
            logger.info(
                "agent_ui_attach_client_accepted endpoint=%s peers=%d",
                self._endpoint,
                peer_count,
            )
            threading.Thread(
                target=self._serve_client,
                args=(client,),
                name="pypost-agent-ui-attach-client",
                daemon=True,
            ).start()

    def _serve_client(self, client: socket.socket) -> None:
        try:
            while not self._stop.is_set():
                try:
                    request = _recv_line(client)
                except (ConnectionError, OSError, json.JSONDecodeError):
                    break
                reply = self._handle_request(request)
                try:
                    _send_line(client, reply)
                except OSError:
                    break
                if request.get("op") == "detach":
                    break
        finally:
            try:
                client.close()
            except OSError:
                pass
            with self._clients_lock:
                if client in self._clients:
                    self._clients.remove(client)
                peer_count = len(self._clients)
            logger.info(
                "agent_ui_attach_client_closed endpoint=%s peers=%d",
                self._endpoint,
                peer_count,
            )

    def _handle_request(self, request: dict[str, Any]) -> dict[str, Any]:
        op = request.get("op")
        if op == "handshake":
            version = request.get("version")
            if version != ATTACH_PROTOCOL_VERSION:
                logger.warning(
                    "agent_ui_attach_handshake_rejected endpoint=%s "
                    "version=%s expected_version=%s",
                    self._endpoint,
                    version,
                    ATTACH_PROTOCOL_VERSION,
                )
                return {
                    "ok": False,
                    "error": (
                        "unsupported attach protocol version: "
                        f"{version!r}"
                    ),
                    "version": ATTACH_PROTOCOL_VERSION,
                }
            logger.info(
                "agent_ui_attach_handshake_ok endpoint=%s version=%s",
                self._endpoint,
                ATTACH_PROTOCOL_VERSION,
            )
            return {"ok": True, "version": ATTACH_PROTOCOL_VERSION}
        if op == "detach":
            logger.info(
                "agent_ui_attach_detach_received endpoint=%s",
                self._endpoint,
            )
            return {"ok": True}
        if op in ("ui_click", "ui_fill", "ui_select", "ui_send_key"):
            return self._run_on_gui(op, request)
        logger.warning(
            "agent_ui_attach_unknown_op endpoint=%s op=%s",
            self._endpoint,
            op,
        )
        return {"ok": False, "error": f"unknown op: {op!r}"}

    def _run_on_gui(self, op: str, request: dict[str, Any]) -> dict[str, Any]:
        widget_id = request.get("widget_id")
        logger.debug(
            "agent_ui_attach_ui_dispatch op=%s widget_id=%s "
            "in_current_tab=%s",
            op,
            widget_id,
            str(bool(request.get("in_current_tab", False))).lower(),
        )
        done = threading.Event()
        box: dict[str, Any] = {}

        def job() -> None:
            try:
                self._dispatch_ui(op, request)
                box["ok"] = True
            except Exception as exc:
                box["ok"] = False
                box["error"] = str(exc)
                box["error_type"] = type(exc).__name__
            finally:
                done.set()

        self._bridge.requested.emit(job)
        if not done.wait(timeout=30.0):
            logger.warning(
                "agent_ui_attach_ui_timeout op=%s widget_id=%s",
                op,
                widget_id,
            )
            return {"ok": False, "error": "attach ui action timed out"}
        if box.get("ok"):
            return {"ok": True}
        logger.info(
            "agent_ui_attach_ui_failed op=%s widget_id=%s error=%s",
            op,
            widget_id,
            box.get("error_type", "unknown"),
        )
        return {"ok": False, "error": box.get("error", "unknown error")}

    def _dispatch_ui(self, op: str, request: dict[str, Any]) -> None:
        in_tab = bool(request.get("in_current_tab", False))
        widget_id = str(request["widget_id"])
        if op == "ui_click":
            self._drive.ui_click(widget_id, in_current_tab=in_tab)
            return
        if op == "ui_fill":
            self._drive.ui_fill(
                widget_id,
                str(request["text"]),
                in_current_tab=in_tab,
                via_key_clicks=bool(request.get("via_key_clicks", False)),
                delay=int(request.get("delay", -1)),
            )
            return
        if op == "ui_select":
            if "option" in request and "option_index" in request:
                raise ValueError("Provide option or option_index, not both")
            if "option" in request:
                self._drive.ui_select(
                    widget_id, str(request["option"]), in_current_tab=in_tab
                )
                return
            if "option_index" in request:
                self._drive.ui_select(
                    widget_id,
                    int(request["option_index"]),
                    in_current_tab=in_tab,
                )
                return
            raise ValueError("ui_select requires option or option_index")
        if op == "ui_send_key":
            mods = Qt.KeyboardModifier(int(request.get("modifiers", 0)))
            self._drive.ui_send_key(
                widget_id,
                str(request["key"]),
                modifiers=mods,
                in_current_tab=in_tab,
            )
            return
        raise ValueError(f"Unhandled op: {op}")
