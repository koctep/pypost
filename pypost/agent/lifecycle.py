"""In-process PyPost launch → ready → shutdown for agents and smoke tests."""

from __future__ import annotations

import logging
import os
import socket
import tempfile
import time
from collections.abc import Callable
from pathlib import Path

from PySide6.QtCore import QCoreApplication
from PySide6.QtWidgets import QApplication

from pypost.main import ComposedApp, compose_app
from pypost.ui.main_window import MainWindow

logger = logging.getLogger(__name__)


def _free_port() -> int:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        sock.bind(("127.0.0.1", 0))
        return sock.getsockname()[1]


def _wait_until(
    condition: Callable[[], bool],
    *,
    timeout: float,
    interval: float = 0.05,
    message: str = "condition not met within timeout",
) -> None:
    """Pump Qt events until ``condition()`` is true or ``timeout`` elapses."""
    deadline = time.time() + timeout
    while time.time() < deadline:
        QCoreApplication.processEvents()
        if condition():
            return
        time.sleep(interval)
    raise TimeoutError(message)


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

    def start(self) -> AgentAppSession:
        """Launch, pump events until is_ui_ready, or raise TimeoutError."""
        if self._started:
            raise RuntimeError("AgentAppSession already started")

        if self._offscreen:
            os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

        self._app = QApplication.instance() or QApplication([])
        self._app.setApplicationName("PyPost")

        config_dir = self._config_dir or Path(self._make_temp_dir("pypost-agent-config-"))
        data_dir = self._data_dir or Path(self._make_temp_dir("pypost-agent-data-"))

        logger.info(
            "agent_session_start config_dir=%s data_dir=%s",
            config_dir,
            data_dir,
        )
        self._composed = compose_app(
            config_dir=config_dir,
            data_dir=data_dir,
            metrics_host="127.0.0.1",
            metrics_port=_free_port(),
            apply_log_level=False,
        )
        self._composed.window.show()
        QCoreApplication.processEvents()

        try:
            _wait_until(
                lambda: self._composed is not None
                and self._composed.window.is_ui_ready,
                timeout=self._ready_timeout,
                message=(
                    "MainWindow.is_ui_ready did not become true within "
                    f"{self._ready_timeout}s"
                ),
            )
        except TimeoutError:
            self.shutdown()
            raise

        self._started = True
        logger.info("agent_session_ready")
        return self

    def shutdown(self) -> None:
        """Request clean exit; stop background servers; release session resources."""
        if self._shut_down:
            return
        self._shut_down = True
        logger.info("agent_session_shutdown")

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
        logger.info("agent_session_shutdown_complete")

    def __enter__(self) -> AgentAppSession:
        return self.start()

    def __exit__(self, *exc: object) -> None:
        self.shutdown()

    def _make_temp_dir(self, prefix: str) -> str:
        td = tempfile.TemporaryDirectory(prefix=prefix)
        self._temp_dirs.append(td)
        return td.name
