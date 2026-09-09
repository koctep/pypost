#!/usr/bin/env python3
"""Run the environment-table click regression in an isolated Qt process.

The parent process classifies normal exits, timeouts, and native signals.  Qt is
imported only by the child so a native crash cannot take down pytest or another
caller.  On a signal exit, ``--native-backtrace`` can repeat the child under
gdb and include a bounded backtrace in the JSON report.
"""

from __future__ import annotations

import argparse
import json
import os
import platform
import shutil
import signal
import subprocess
import sys
import time
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_STREAM_LIMIT = 16_000


def _tail(value: str, limit: int) -> str:
    return value if len(value) <= limit else value[-limit:]


def _signal_name(returncode: int) -> str | None:
    if returncode >= 0:
        return None
    try:
        return signal.Signals(-returncode).name
    except ValueError:
        return f"SIGNAL_{-returncode}"


def classify_process_result(returncode: int, *, timed_out: bool) -> tuple[str, str | None]:
    """Classify a child result without conflating a timeout with a signal."""
    if timed_out:
        return "timeout", None
    if returncode < 0:
        return "signal_exit", _signal_name(returncode)
    if returncode == 0:
        return "passed", None
    return "failed", None


def _expired_stream(value: str | bytes | None) -> str:
    if isinstance(value, bytes):
        return value.decode(errors="replace")
    return value or ""


def _child_command(cycles: int) -> list[str]:
    return [
        sys.executable,
        str(Path(__file__).resolve()),
        "--child",
        "--cycles",
        str(cycles),
    ]


def _run_native_backtrace(
    child_command: list[str],
    *,
    env: dict[str, str],
    timeout_seconds: float,
    stream_limit: int,
) -> dict[str, Any]:
    gdb = shutil.which("gdb")
    if gdb is None:
        return {"status": "unavailable", "reason": "gdb not found"}

    command = [
        gdb,
        "--quiet",
        "--batch",
        "-ex",
        "set pagination off",
        "-ex",
        "run",
        "-ex",
        "thread apply all bt 30",
        "--args",
        *child_command,
    ]
    try:
        result = subprocess.run(
            command,
            cwd=REPO_ROOT,
            env=env,
            capture_output=True,
            text=True,
            timeout=timeout_seconds,
            check=False,
        )
    except subprocess.TimeoutExpired as exc:
        stdout = _expired_stream(exc.stdout)
        stderr = _expired_stream(exc.stderr)
        return {
            "status": "timeout",
            "stdout_tail": _tail(stdout or "", stream_limit),
            "stderr_tail": _tail(stderr or "", stream_limit),
        }

    combined = f"{result.stdout}\n{result.stderr}"
    return {
        "status": "captured" if "received signal" in combined else "not_reproduced",
        "returncode": result.returncode,
        "output_tail": _tail(combined, stream_limit),
    }


def run_harness(
    *,
    qpa_platform: str,
    cycles: int,
    timeout_seconds: float,
    stream_limit: int = DEFAULT_STREAM_LIMIT,
    capture_native_backtrace: bool = False,
) -> dict[str, Any]:
    """Execute the GUI scenario and return a structured classification."""
    child_command = _child_command(cycles)
    env = {
        **os.environ,
        "PYTHONPATH": str(REPO_ROOT),
        "PYTHONFAULTHANDLER": "1",
        "QT_QPA_PLATFORM": qpa_platform,
    }
    started = time.monotonic()

    try:
        completed = subprocess.run(
            child_command,
            cwd=REPO_ROOT,
            env=env,
            capture_output=True,
            text=True,
            timeout=timeout_seconds,
            check=False,
        )
        returncode = completed.returncode
        stdout = completed.stdout
        stderr = completed.stderr
        timed_out = False
    except subprocess.TimeoutExpired as exc:
        returncode = -1
        stdout = _expired_stream(exc.stdout)
        stderr = _expired_stream(exc.stderr)
        timed_out = True

    status, signal_name = classify_process_result(returncode, timed_out=timed_out)

    report: dict[str, Any] = {
        "status": status,
        "returncode": returncode,
        "exit_code": 128 + (-returncode) if returncode < 0 else returncode,
        "signal": signal_name,
        "timed_out": timed_out,
        "duration_seconds": round(time.monotonic() - started, 3),
        "cycles": cycles,
        "environment": {
            "python": platform.python_version(),
            "qpa_requested": qpa_platform,
            "wayland_display": os.environ.get("WAYLAND_DISPLAY"),
        },
        "stdout_tail": _tail(stdout or "", stream_limit),
        "stderr_tail": _tail(stderr or "", stream_limit),
    }
    if status == "signal_exit" and capture_native_backtrace:
        report["native_backtrace"] = _run_native_backtrace(
            child_command,
            env=env,
            timeout_seconds=timeout_seconds,
            stream_limit=stream_limit,
        )
    return report


def _run_child(cycles: int) -> int:
    from PySide6.QtCore import Qt
    from PySide6.QtTest import QTest
    from PySide6.QtWidgets import QApplication

    from pypost.models.models import Environment
    from pypost.ui.dialogs.env_dialog import EnvironmentDialog

    app = QApplication.instance() or QApplication([])
    dialog = EnvironmentDialog(
        [Environment(name="Crash regression", variables={"EXISTING": "value"})],
        current_env_name="Crash regression",
    )
    dialog.show()
    app.processEvents()

    table = dialog.vars_table
    trailing_row = table.rowCount() - 1
    for _ in range(cycles):
        for column in (0, 1):
            index = table.model().index(trailing_row, column)
            point = table.visualRect(index).center()
            QTest.mouseDClick(
                table.viewport(),
                Qt.MouseButton.LeftButton,
                Qt.KeyboardModifier.NoModifier,
                point,
                1,
            )
            app.processEvents()
            QTest.mouseClick(
                table.viewport(),
                Qt.MouseButton.LeftButton,
                Qt.KeyboardModifier.NoModifier,
                point,
                1,
            )
            app.processEvents()

    print(  # noqa: T201 - CLI child diagnostic consumed by the parent harness
        json.dumps(
            {
                "qpa_actual": QApplication.platformName(),
                "cycles_completed": cycles,
                "cell_widgets": [
                    table.cellWidget(row, 2) is not None
                    for row in range(table.rowCount())
                ],
            }
        ),
        flush=True,
    )
    dialog.close()
    app.processEvents()
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Isolated EnvironmentDialog repeated-click crash regression",
    )
    parser.add_argument("--child", action="store_true", help=argparse.SUPPRESS)
    parser.add_argument("--qpa", default="wayland", choices=("wayland", "offscreen", "xcb"))
    parser.add_argument("--cycles", type=int, default=100)
    parser.add_argument("--timeout", type=float, default=30.0)
    parser.add_argument("--stream-limit", type=int, default=DEFAULT_STREAM_LIMIT)
    parser.add_argument("--native-backtrace", action="store_true")
    parser.add_argument("--report-json", type=Path)
    args = parser.parse_args()

    if args.child:
        return _run_child(args.cycles)
    if args.cycles < 1 or args.timeout <= 0 or args.stream_limit < 1:
        parser.error("cycles, timeout, and stream-limit must be positive")

    report = run_harness(
        qpa_platform=args.qpa,
        cycles=args.cycles,
        timeout_seconds=args.timeout,
        stream_limit=args.stream_limit,
        capture_native_backtrace=args.native_backtrace,
    )
    rendered = json.dumps(report, indent=2, ensure_ascii=False)
    print(rendered)  # noqa: T201 - CLI report output
    if args.report_json is not None:
        args.report_json.parent.mkdir(parents=True, exist_ok=True)
        args.report_json.write_text(f"{rendered}\n", encoding="utf-8")
    return 0 if report["status"] == "passed" else 1


if __name__ == "__main__":
    raise SystemExit(main())
