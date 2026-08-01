"""In-process PyPost launch → ready → shutdown for agents and smoke tests."""

from __future__ import annotations

import logging
import os
import socket
import tempfile
import time
from collections.abc import Callable
from pathlib import Path
from typing import Any

from PySide6.QtCore import QCoreApplication
from PySide6.QtWidgets import QApplication

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QWidget

from pypost.agent.ui_actions import (
    find_widget,
    ui_click,
    ui_fill,
    ui_select,
    ui_send_key,
)
from pypost.agent.ui_snapshot import capture_ui_snapshot
from pypost.agent.ui_wait import (
    DEFAULT_UI_WAIT_TIMEOUT_S,
    wait_for_enabled,
    wait_for_snapshot,
    wait_for_text,
    wait_for_widget,
    wait_until,
)
from pypost.main import ComposedApp, compose_app
from pypost.ui.main_window import MainWindow
from pypost.ui.widget_ids import REQUEST_TABS

logger = logging.getLogger(__name__)

# Optional best-effort dump callback (installed by agent e2e pytest plugin).
# Signature: hook(session, exc_type, exc) -> None
_FailureDumpHook = Callable[
    ["AgentAppSession", type[BaseException], BaseException],
    None,
]
_failure_dump_hook: _FailureDumpHook | None = None


def set_agent_session_failure_dump_hook(hook: _FailureDumpHook | None) -> None:
    """Install or clear the optional ``__exit__`` failure-dump callback."""
    global _failure_dump_hook
    _failure_dump_hook = hook


def _free_port() -> int:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        sock.bind(("127.0.0.1", 0))
        return sock.getsockname()[1]


class AgentAppSession:
    """In-process PyPost lifecycle for agents and smoke tests.

    Does not call ``QApplication.exec()``. Ready wait pumps events until
    ``window.is_ui_ready`` is true.
    """

    def __init__(
        self,
        *,
        offscreen: bool = True,
        config_dir: Path | None = None,
        data_dir: Path | None = None,
        ready_timeout: float = 30.0,
    ) -> None:
        self._offscreen = offscreen
        self._config_dir = config_dir
        self._data_dir = data_dir
        self._ready_timeout = ready_timeout
        self._temp_dirs: list[tempfile.TemporaryDirectory[str]] = []
        self._app: QApplication | None = None
        self._composed: ComposedApp | None = None
        self._metrics_port: int | None = None
        self._started = False
        self._shut_down = False

    @property
    def app(self) -> QApplication:
        if self._app is None:
            raise RuntimeError("AgentAppSession has not been started")
        return self._app

    @property
    def window(self) -> MainWindow:
        if self._composed is None:
            raise RuntimeError("AgentAppSession has not been started")
        return self._composed.window

    @property
    def metrics_port(self) -> int:
        """Ephemeral metrics bind port chosen for this session (set in ``start``)."""
        if self._metrics_port is None:
            raise RuntimeError("AgentAppSession has not been started")
        return self._metrics_port

    def start(self) -> AgentAppSession:
        """Launch, pump events until is_ui_ready, or raise TimeoutError."""
        if self._started:
            raise RuntimeError("AgentAppSession already started")
        # Prior failed start sets _shut_down; clear so this attempt can clean up.
        self._shut_down = False

        if self._offscreen:
            os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

        self._app = QApplication.instance() or QApplication([])
        self._app.setApplicationName("PyPost")

        config_dir = self._config_dir or Path(self._make_temp_dir("pypost-agent-config-"))
        data_dir = self._data_dir or Path(self._make_temp_dir("pypost-agent-data-"))
        metrics_port = _free_port()
        self._metrics_port = metrics_port

        logger.info(
            "agent_session_started offscreen=%s ready_timeout_s=%s "
            "metrics_port=%s config_dir=%s data_dir=%s",
            str(self._offscreen).lower(),
            self._ready_timeout,
            metrics_port,
            config_dir,
            data_dir,
        )
        launch_started = time.monotonic()
        try:
            composed = compose_app(
                config_dir=config_dir,
                data_dir=data_dir,
                metrics_host="127.0.0.1",
                metrics_port=metrics_port,
                apply_log_level=False,
            )
            self._composed = composed
            composed.window.show()
            QCoreApplication.processEvents()

            ready_wait_started = time.monotonic()
            try:
                wait_until(
                    lambda: composed.window.is_ui_ready,
                    timeout=self._ready_timeout,
                    message=(
                        "MainWindow.is_ui_ready did not become true within "
                        f"{self._ready_timeout}s"
                    ),
                    condition_name="is_ui_ready",
                )
            except TimeoutError:
                waited_ms = int((time.monotonic() - ready_wait_started) * 1000)
                logger.warning(
                    "agent_session_ready_timeout ready_timeout_s=%s waited_ms=%s "
                    "metrics_port=%s",
                    self._ready_timeout,
                    waited_ms,
                    metrics_port,
                )
                raise

            ready_ms = int((time.monotonic() - ready_wait_started) * 1000)
            launch_ms = int((time.monotonic() - launch_started) * 1000)
            self._started = True
            logger.info(
                "agent_session_ready ready_ms=%s launch_ms=%s metrics_port=%s",
                ready_ms,
                launch_ms,
                metrics_port,
            )
            return self
        except BaseException:
            # Any mid-start failure (compose, show, ready wait, timeout) must
            # release temps + metrics; shutdown() is idempotent.
            self.shutdown()
            raise

    def shutdown(self) -> None:
        """Request clean exit; stop background servers; release session resources."""
        if self._shut_down:
            return
        self._shut_down = True
        shutdown_started = time.monotonic()
        logger.info(
            "agent_session_shutdown_started metrics_port=%s started=%s",
            self._metrics_port,
            str(self._started).lower(),
        )

        composed = self._composed
        if composed is not None:
            try:
                if composed.mcp_manager.is_running():
                    composed.mcp_manager.stop_server()
            except Exception:
                logger.exception("agent_session_mcp_stop_failed")
            try:
                composed.window.handle_exit()
            except Exception:
                logger.exception("agent_session_handle_exit_failed")
            try:
                composed.window.close()
            except Exception:
                logger.exception("agent_session_window_close_failed")
            try:
                composed.metrics.stop_server()
            except Exception:
                logger.exception("agent_session_metrics_stop_failed")
            QCoreApplication.processEvents()

        self._composed = None
        for td in self._temp_dirs:
            try:
                td.cleanup()
            except Exception:
                logger.exception("agent_session_temp_cleanup_failed")
        self._temp_dirs.clear()
        shutdown_ms = int((time.monotonic() - shutdown_started) * 1000)
        logger.info(
            "agent_session_shutdown_completed shutdown_ms=%s metrics_port=%s",
            shutdown_ms,
            self._metrics_port,
        )

    def __enter__(self) -> AgentAppSession:
        return self.start()

    def __exit__(
        self,
        exc_type: type[BaseException] | None,
        exc: BaseException | None,
        tb: object,
    ) -> None:
        # Direct constructions: dump while the session is still started.
        # Fixture path keeps makereport (yield teardown sees exc_type=None).
        if (
            _failure_dump_hook is not None
            and exc_type is not None
            and exc is not None
            and issubclass(exc_type, Exception)
            and self._started
            and not self._shut_down
        ):
            try:
                _failure_dump_hook(self, exc_type, exc)
            except Exception as dump_exc:  # noqa: BLE001 — never mask the test failure
                logger.warning(
                    "agent_session_failure_dump_hook_failed error=%s",
                    type(dump_exc).__name__,
                )
        self.shutdown()

    def ui_snapshot(self) -> dict[str, Any]:
        """Return a structured visible-UI snapshot; requires a started session."""
        return capture_ui_snapshot(self.window)

    def current_request_tab(self) -> QWidget:
        """Return the active request tab widget (scoped lookup root).

        Per-tab role ids (URL, Send, …) are shared across tabs; resolve them
        under this widget instead of the main window (PYPOST-851).
        """
        tabs = find_widget(self.window, REQUEST_TABS)
        current = tabs.currentWidget()
        if current is None:
            raise RuntimeError("No current request tab")
        return current

    def find_in_current_tab(self, widget_id: str) -> QWidget:
        """Resolve ``widget_id`` under the active request tab."""
        return find_widget(self.current_request_tab(), widget_id)

    def _action_root(self, *, in_current_tab: bool) -> QWidget:
        return self.current_request_tab() if in_current_tab else self.window

    def ui_click(self, widget_id: str, *, in_current_tab: bool = False) -> None:
        """Left-click a named widget under the main window (or current tab)."""
        ui_click(self._action_root(in_current_tab=in_current_tab), widget_id)

    def ui_fill(
        self,
        widget_id: str,
        text: str,
        *,
        in_current_tab: bool = False,
        via_key_clicks: bool = False,
    ) -> None:
        """Fill a named text input under the main window (or current tab)."""
        ui_fill(
            self._action_root(in_current_tab=in_current_tab),
            widget_id,
            text,
            via_key_clicks=via_key_clicks,
        )

    def ui_select(
        self,
        widget_id: str,
        option: str | int,
        *,
        in_current_tab: bool = False,
    ) -> None:
        """Select by display text or index on a named combo, list, or tree."""
        ui_select(
            self._action_root(in_current_tab=in_current_tab),
            widget_id,
            option,
        )

    def ui_send_key(
        self,
        widget_id: str,
        key: str,
        *,
        modifiers: Qt.KeyboardModifier = Qt.KeyboardModifier.NoModifier,
        in_current_tab: bool = False,
    ) -> None:
        """Send a key (with optional modifiers) to a named widget."""
        ui_send_key(
            self._action_root(in_current_tab=in_current_tab),
            widget_id,
            key,
            modifiers=modifiers,
        )

    def wait_until(
        self,
        condition: Callable[[], bool],
        *,
        timeout: float = DEFAULT_UI_WAIT_TIMEOUT_S,
        message: str = "condition not met within timeout",
        condition_name: str = "predicate",
    ) -> None:
        """Pump events until ``condition()`` is true (session still started)."""
        self._require_started()
        wait_until(
            condition,
            timeout=timeout,
            message=message,
            condition_name=condition_name,
        )

    def wait_for_widget(
        self,
        widget_id: str,
        *,
        timeout: float = DEFAULT_UI_WAIT_TIMEOUT_S,
    ) -> QWidget:
        """Wait until a named widget exists under the main window."""
        self._require_started()
        return wait_for_widget(self.window, widget_id, timeout=timeout)

    def wait_for_enabled(
        self,
        widget_id: str,
        *,
        timeout: float = DEFAULT_UI_WAIT_TIMEOUT_S,
    ) -> QWidget:
        """Wait until a named widget is visible and enabled."""
        self._require_started()
        return wait_for_enabled(self.window, widget_id, timeout=timeout)

    def wait_for_text(
        self,
        widget_id: str,
        expected: str | Callable[[str], bool],
        *,
        timeout: float = DEFAULT_UI_WAIT_TIMEOUT_S,
    ) -> QWidget:
        """Wait until a named widget's text matches ``expected``."""
        self._require_started()
        return wait_for_text(self.window, widget_id, expected, timeout=timeout)

    def wait_for_snapshot(
        self,
        predicate: Callable[[dict[str, Any]], bool],
        *,
        timeout: float = DEFAULT_UI_WAIT_TIMEOUT_S,
    ) -> dict[str, Any]:
        """Wait until a UI snapshot satisfies ``predicate``."""
        self._require_started()
        return wait_for_snapshot(self.window, predicate, timeout=timeout)

    def _require_started(self) -> None:
        if not self._started or self._composed is None:
            raise RuntimeError("AgentAppSession has not been started")

    def _make_temp_dir(self, prefix: str) -> str:
        td = tempfile.TemporaryDirectory(prefix=prefix)
        self._temp_dirs.append(td)
        return td.name
