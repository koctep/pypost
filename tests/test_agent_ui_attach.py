"""PYPOST-1207: attach agent-UI MCP to already-running desktop."""

from __future__ import annotations

import threading
import time
from pathlib import Path

import pytest
from PySide6.QtCore import QCoreApplication
from PySide6.QtWidgets import QApplication, QPushButton, QWidget

from pypost.agent import ui_actions_mcp
from pypost.agent.attach_ipc import AgentUiAttachHost, AttachClientSession
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
