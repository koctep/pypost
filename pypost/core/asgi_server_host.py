"""Runs an ASGI app on uvicorn in a background thread.

The metrics endpoint and the MCP server both need the same thing: serve an ASGI
app off the GUI thread, stop it on demand, and rebind it to a different port when
settings change. They each grew their own copy of that plumbing and each copy
acquired different bugs, so it lives here once.
"""
import asyncio
import logging
import threading
from typing import Callable, Optional

import uvicorn

logger = logging.getLogger(__name__)

DEFAULT_JOIN_TIMEOUT = 2.0


class AsgiServerHost:
    def __init__(
        self,
        name: str,
        app_factory: Callable[[], object],
        log_level: str = "info",
        join_timeout: float = DEFAULT_JOIN_TIMEOUT,
    ):
        self._name = name
        self._app_factory = app_factory
        self._log_level = log_level
        self._join_timeout = join_timeout
        # Reentrant: start() calls stop() while already holding the lock.
        self._lock = threading.RLock()
        self._server: Optional[uvicorn.Server] = None
        self._thread: Optional[threading.Thread] = None
        self.host: Optional[str] = None
        self.port: Optional[int] = None

    @property
    def server(self) -> Optional[uvicorn.Server]:
        return self._server

    @property
    def thread(self) -> Optional[threading.Thread]:
        return self._thread

    def is_running(self) -> bool:
        thread = self._thread
        return thread is not None and thread.is_alive()

    def start(self, host: str, port: int) -> None:
        with self._lock:
            if self.is_running():
                self.stop()

            self.host = host
            self.port = port
            # Built here rather than inside the thread: a stop arriving before the
            # thread got that far would read None, skip should_exit, and leave the
            # server serving.
            self._server = self._build(host, port)
            self._thread = threading.Thread(
                target=self._serve, daemon=True, name=f"{self._name}-asgi",
            )
            self._thread.start()
            logger.info(
                "asgi_server_started name=%s host=%s port=%d", self._name, host, port,
            )

    def stop(self) -> None:
        with self._lock:
            if self._server is not None:
                self._server.should_exit = True

            thread = self._thread
            if thread is not None:
                thread.join(timeout=self._join_timeout)
                if thread.is_alive():
                    logger.warning(
                        "asgi_server_stop_timeout name=%s timeout=%.1f",
                        self._name, self._join_timeout,
                    )
                self._thread = None
                self._server = None
                logger.info("asgi_server_stopped name=%s", self._name)

    def restart(self, host: str, port: int) -> None:
        with self._lock:
            self.stop()
            self.start(host, port)

    def _build(self, host: str, port: int) -> uvicorn.Server:
        config = uvicorn.Config(
            app=self._app_factory(),
            host=host,
            port=port,
            loop="asyncio",
            log_level=self._log_level,
        )
        server = uvicorn.Server(config)
        # Signal handlers can only be installed from the main thread.
        server.install_signal_handlers = lambda: None
        return server

    def _serve(self) -> None:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        loop.run_until_complete(self._server.serve())
