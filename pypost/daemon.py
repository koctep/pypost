from __future__ import annotations

import argparse
import logging
import os
import signal
import sys
from collections.abc import Sequence

from PySide6.QtCore import QCoreApplication, QTimer

from pypost.core.daemon_config import (
    DaemonConfigurationError,
    resolve_daemon_paths,
    validate_daemon_paths,
)
from pypost.core.qt.daemon_runtime import DaemonRuntime

logger = logging.getLogger(__name__)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="pypost-daemon",
        description="Run PyPost MCP services without a graphical interface.",
    )
    parser.add_argument("--collections-dir", metavar="PATH")
    parser.add_argument("--environments-dir", metavar="PATH")
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    logging.basicConfig(level=logging.INFO, stream=sys.stderr)
    arguments = build_parser().parse_args(argv)
    try:
        paths = resolve_daemon_paths(
            cli_collections_dir=arguments.collections_dir,
            cli_environments_dir=arguments.environments_dir,
            environ=os.environ,
        )
        validate_daemon_paths(paths)
    except DaemonConfigurationError as exc:
        logger.error("daemon_configuration_failed %s", exc)
        return 1

    application = QCoreApplication.instance() or QCoreApplication(["pypost-daemon"])
    runtime = DaemonRuntime(paths)
    normal_termination = False

    def request_shutdown(_signal_number, _frame) -> None:
        nonlocal normal_termination
        normal_termination = True
        application.quit()

    previous_handlers = {
        signal_number: signal.signal(signal_number, request_shutdown)
        for signal_number in (signal.SIGINT, signal.SIGTERM)
    }
    heartbeat = QTimer()
    heartbeat.setInterval(500)
    heartbeat.timeout.connect(lambda: None)
    heartbeat.start()
    application.aboutToQuit.connect(runtime.shutdown)
    QTimer.singleShot(0, runtime.start)
    try:
        application.exec()
    finally:
        runtime.shutdown()
        heartbeat.stop()
        for signal_number, handler in previous_handlers.items():
            signal.signal(signal_number, handler)
    if normal_termination and runtime.exit_code == 0:
        return 0
    return runtime.exit_code


if __name__ == "__main__":
    raise SystemExit(main())
