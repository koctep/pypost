"""Attach agent-UI MCP to already-running desktop (PYPOST-1207 / PYPOST-1208)."""

from __future__ import annotations

import threading
import time
from pathlib import Path

import pytest
from PySide6.QtCore import QCoreApplication
from PySide6.QtWidgets import (
    QApplication,
    QComboBox,
    QLineEdit,
    QPushButton,
    QWidget,
)

from pypost.agent import ui_actions_mcp
from pypost.agent.attach_ipc import (
    ATTACH_PROTOCOL_VERSION,
    AgentUiAttachHost,
    AttachClientSession,
    AttachUnboundError,
    default_attach_endpoint,
)
from pypost.agent.ui_actions_mcp import main

pytestmark = pytest.mark.timeout(30)


def _pump_until(done: threading.Event, *, timeout_s: float = 10.0) -> None:
    deadline = time.monotonic() + timeout_s
    while not done.is_set():
        if time.monotonic() >= deadline:
            pytest.fail("timed out waiting for attach worker")
        QCoreApplication.processEvents()
        time.sleep(0.01)


def test_cli_accepts_attach_mode(capsys: pytest.CaptureFixture[str]) -> None:
    """Sidecar CLI must document and accept ``--attach`` mode."""
    with pytest.raises(SystemExit) as exc_info:
        main(["--help"])

    assert exc_info.value.code == 0
    help_text = capsys.readouterr().out
    assert "--attach" in help_text, (
        "CLI must accept attach mode (--attach); missing from --help"
    )


def test_attach_host_rejects_protocol_version_mismatch(qapp: QApplication) -> None:
    """Attach handshake must fail closed for an unsupported protocol version."""
    root = QWidget()
    host = AgentUiAttachHost(root)
    try:
        reply = host._handle_request(
            {
                "op": "handshake",
                "version": ATTACH_PROTOCOL_VERSION + 1,
            }
        )
    finally:
        root.close()

    assert reply["ok"] is False
    assert "version" in str(reply["error"])


def test_attach_mode_does_not_call_agent_app_session_start(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Attach mode must not call ``AgentAppSession.start()`` (no silent spawn)."""
    start_calls: list[str] = []

    class TrackingSession:
        def __init__(self, *args: object, **kwargs: object) -> None:
            pass

        def start(self) -> None:
            start_calls.append("start")

        def shutdown(self) -> None:
            pass

    monkeypatch.setattr(ui_actions_mcp, "AgentAppSession", TrackingSession)
    monkeypatch.setattr(
        ui_actions_mcp.asyncio,
        "run",
        lambda *_a, **_k: None,
    )

    try:
        main(["--attach"])
    except SystemExit as exc:
        if exc.code == 2:
            pytest.fail(
                "--attach must be a recognized CLI option; "
                f"got argparse rejection (SystemExit {exc.code})"
            )
    except Exception:
        # Attach-fail without a host is acceptable; start must still be skipped.
        pass

    assert start_calls == [], (
        "attach mode must not call AgentAppSession.start() "
        f"(observed calls={start_calls!r})"
    )


def test_attach_without_host_fails_unbound_not_silent_spawn(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """No desktop host → attach fail (unbound); must not silently spawn."""
    start_calls: list[str] = []

    class TrackingSession:
        def __init__(self, *args: object, **kwargs: object) -> None:
            pass

        def start(self) -> None:
            start_calls.append("start")

        def shutdown(self) -> None:
            pass

    monkeypatch.setattr(ui_actions_mcp, "AgentAppSession", TrackingSession)

    def _forbid_serve(*_a: object, **_k: object) -> None:
        raise AssertionError(
            "stdio serve must not run when attach has no host"
        )

    monkeypatch.setattr(ui_actions_mcp.asyncio, "run", _forbid_serve)

    raised: BaseException | None = None
    try:
        main(["--attach"])
    except SystemExit as exc:
        raised = exc
        if exc.code == 2:
            pytest.fail(
                "--attach must be accepted by CLI; got argparse rejection "
                f"(SystemExit {exc.code})"
            )
        if exc.code in (0, None):
            pytest.fail(
                "attach without host must fail unbound (nonzero exit)"
            )
    except Exception as exc:
        raised = exc
    else:
        pytest.fail(
            "attach without host must fail (unbound), not succeed silently"
        )

    assert raised is not None
    assert start_calls == [], (
        "attach without host must not call AgentAppSession.start() "
        f"(observed calls={start_calls!r})"
    )


def test_attach_host_client_ui_click_round_trip(
    tmp_path: Path,
    qapp: QApplication,
) -> None:
    """Desktop host + attach client: ui_click runs on the live widget tree."""
    endpoint = str(tmp_path / "attach.sock")
    root = QWidget()
    button = QPushButton("Go", root)
    button.setObjectName("attach_probe_button")
    clicks: list[str] = []
    button.clicked.connect(lambda: clicks.append("clicked"))
    root.show()
    qapp.processEvents()

    host = AgentUiAttachHost(root, endpoint=endpoint)
    host.start()
    try:
        box: dict[str, object] = {}
        done = threading.Event()

        def worker() -> None:
            client = AttachClientSession(endpoint=endpoint)
            try:
                client.connect()
                client.ui_click("attach_probe_button")
                client.detach()
                box["ok"] = True
            except Exception as exc:
                box["error"] = exc
            finally:
                done.set()

        threading.Thread(target=worker, daemon=True).start()
        _pump_until(done)
        assert box.get("ok") is True, f"attach round-trip failed: {box!r}"
        assert clicks == ["clicked"]
    finally:
        host.stop()
        root.close()


def test_attach_detach_leaves_host_listening(
    tmp_path: Path,
    qapp: QApplication,
) -> None:
    """Detach closes the client binding; host remains available to re-bind."""
    endpoint = str(tmp_path / "attach-detach.sock")
    root = QWidget()
    root.show()
    qapp.processEvents()

    host = AgentUiAttachHost(root, endpoint=endpoint)
    host.start()
    try:
        box: dict[str, object] = {}
        done = threading.Event()

        def worker() -> None:
            first = AttachClientSession(endpoint=endpoint)
            second = AttachClientSession(endpoint=endpoint)
            try:
                first.connect()
                first.detach()
                second.connect()
                second.detach()
                box["ok"] = True
            except Exception as exc:
                box["error"] = exc
            finally:
                done.set()

        threading.Thread(target=worker, daemon=True).start()
        _pump_until(done)
        assert box.get("ok") is True, f"detach/rebind failed: {box!r}"
    finally:
        host.stop()
        root.close()


# ---------------------------------------------------------------------------
# PYPOST-1208 (ATTACH-3) — residual attach proofs (host+client / CLI)
# ---------------------------------------------------------------------------


def test_attach_host_client_ui_fill_sets_line_edit(
    tmp_path: Path,
    qapp: QApplication,
) -> None:
    """Desktop host + attach client: ui_fill sets fixture QLineEdit text."""
    endpoint = str(tmp_path / "attach-fill.sock")
    root = QWidget()
    line = QLineEdit(root)
    line.setObjectName("attach_probe_input")
    root.show()
    qapp.processEvents()

    host = AgentUiAttachHost(root, endpoint=endpoint)
    host.start()
    try:
        box: dict[str, object] = {}
        done = threading.Event()

        def worker() -> None:
            client = AttachClientSession(endpoint=endpoint)
            try:
                client.connect()
                client.ui_fill("attach_probe_input", "https://example.com")
                client.detach()
                box["ok"] = True
            except Exception as exc:
                box["error"] = exc
            finally:
                done.set()

        threading.Thread(target=worker, daemon=True).start()
        _pump_until(done)
        assert box.get("ok") is True, f"attach ui_fill failed: {box!r}"
        assert line.text() == "https://example.com"
    finally:
        host.stop()
        root.close()


def test_attach_host_client_ui_select_sets_combo(
    tmp_path: Path,
    qapp: QApplication,
) -> None:
    """Desktop host + attach client: ui_select selects fixture combo option."""
    endpoint = str(tmp_path / "attach-select.sock")
    root = QWidget()
    combo = QComboBox(root)
    combo.addItems(["GET", "POST", "PUT"])
    combo.setObjectName("attach_probe_combo")
    root.show()
    qapp.processEvents()

    host = AgentUiAttachHost(root, endpoint=endpoint)
    host.start()
    try:
        box: dict[str, object] = {}
        done = threading.Event()

        def worker() -> None:
            client = AttachClientSession(endpoint=endpoint)
            try:
                client.connect()
                client.ui_select("attach_probe_combo", "POST")
                client.detach()
                box["ok"] = True
            except Exception as exc:
                box["error"] = exc
            finally:
                done.set()

        threading.Thread(target=worker, daemon=True).start()
        _pump_until(done)
        assert box.get("ok") is True, f"attach ui_select failed: {box!r}"
        assert combo.currentText() == "POST"
    finally:
        host.stop()
        root.close()


def test_attach_host_client_ui_send_key_changes_text(
    tmp_path: Path,
    qapp: QApplication,
) -> None:
    """Desktop host + attach client: ui_send_key changes fixture text."""
    endpoint = str(tmp_path / "attach-send-key.sock")
    root = QWidget()
    line = QLineEdit("ab", root)
    line.setObjectName("attach_probe_keys")
    root.show()
    qapp.processEvents()

    host = AgentUiAttachHost(root, endpoint=endpoint)
    host.start()
    try:
        box: dict[str, object] = {}
        done = threading.Event()

        def worker() -> None:
            client = AttachClientSession(endpoint=endpoint)
            try:
                client.connect()
                client.ui_send_key("attach_probe_keys", "backspace")
                client.detach()
                box["ok"] = True
            except Exception as exc:
                box["error"] = exc
            finally:
                done.set()

        threading.Thread(target=worker, daemon=True).start()
        _pump_until(done)
        assert box.get("ok") is True, f"attach ui_send_key failed: {box!r}"
        assert line.text() == "a"
    finally:
        host.stop()
        root.close()


def test_attach_host_stop_unbinds_client(
    tmp_path: Path,
    qapp: QApplication,
) -> None:
    """After host.stop(), client cannot drive and new connect stays unbound."""
    endpoint = str(tmp_path / "attach-host-stop.sock")
    root = QWidget()
    root.show()
    qapp.processEvents()

    host = AgentUiAttachHost(root, endpoint=endpoint)
    host.start()
    try:
        box: dict[str, object] = {}
        done = threading.Event()
        stop_gate = threading.Event()

        def worker() -> None:
            client = AttachClientSession(endpoint=endpoint)
            try:
                client.connect()
                stop_gate.set()
                # Wait until host.stop() has torn down the peer.
                time.sleep(0.2)
                try:
                    client.ui_click("missing")
                    box["ui_error"] = None
                except Exception as exc:
                    box["ui_error"] = exc
                rebound = AttachClientSession(
                    endpoint=endpoint, connect_timeout=0.5
                )
                try:
                    rebound.connect()
                    box["rebind_ok"] = True
                except AttachUnboundError as exc:
                    box["rebind_error"] = exc
                box["ok"] = True
            except Exception as exc:
                box["error"] = exc
            finally:
                done.set()

        threading.Thread(target=worker, daemon=True).start()
        assert stop_gate.wait(timeout=5.0), "client never connected"
        host.stop()
        _pump_until(done)
        assert box.get("ok") is True, f"host-stop worker failed: {box!r}"
        assert box.get("ui_error") is not None, (
            "ui_* after host.stop must fail"
        )
        assert "rebind_error" in box, "rebind after host.stop must be unbound"
        assert not Path(endpoint).exists(), "socket path must be unlinked"
    finally:
        try:
            host.stop()
        except Exception:
            pass
        root.close()


def test_attach_sidecar_exit_leaves_host_listening(
    tmp_path: Path,
    qapp: QApplication,
) -> None:
    """Abrupt client socket close (sidecar gone); host still accepts rebind."""
    endpoint = str(tmp_path / "attach-sidecar-exit.sock")
    root = QWidget()
    root.show()
    qapp.processEvents()

    host = AgentUiAttachHost(root, endpoint=endpoint)
    host.start()
    try:
        box: dict[str, object] = {}
        done = threading.Event()

        def worker() -> None:
            first = AttachClientSession(endpoint=endpoint)
            second = AttachClientSession(endpoint=endpoint)
            try:
                first.connect()
                # Abrupt peer-gone (no detach op): close the AF_UNIX socket.
                sock = first._sock
                first._sock = None
                assert sock is not None
                sock.close()
                second.connect()
                second.detach()
                box["ok"] = True
            except Exception as exc:
                box["error"] = exc
            finally:
                done.set()

        threading.Thread(target=worker, daemon=True).start()
        _pump_until(done)
        assert box.get("ok") is True, f"sidecar-exit rebind failed: {box!r}"
    finally:
        host.stop()
        root.close()


def test_attach_endpoint_override_env_and_cli(
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    """Env override shapes default_attach_endpoint; CLI documents flag."""
    custom = "/tmp/pypost-attach-override-probe.sock"
    monkeypatch.setenv("PYPOST_AGENT_UI_ATTACH_ENDPOINT", custom)
    assert default_attach_endpoint() == custom

    monkeypatch.delenv("PYPOST_AGENT_UI_ATTACH_ENDPOINT", raising=False)
    monkeypatch.setenv("XDG_RUNTIME_DIR", "/tmp/pypost-xdg-runtime-probe")
    expected = "/tmp/pypost-xdg-runtime-probe/pypost-agent-ui-attach.sock"
    assert default_attach_endpoint() == expected

    with pytest.raises(SystemExit) as exc_info:
        main(["--help"])
    assert exc_info.value.code == 0
    help_text = capsys.readouterr().out
    assert "--attach-endpoint" in help_text
