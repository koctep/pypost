#!/usr/bin/env python3
"""Reproduction and baseline diagnostic harness for large-batch apply_theme segfault
(PYPOST-1117 / PYPOST-1212).

Spawns isolated child pytest processes to contrast:
- Full unpartitioned large-batch GUI test execution (~110 modules in 1 OS process).
- Bounded chunked batches (e.g. 15 modules per chunk).
- Single module execution.

Traps native signals (SIGSEGV/139), records stderr backtraces, and produces
structured JSON reports.
"""

from __future__ import annotations

import argparse
import datetime
import json
import os
import platform
import signal
import subprocess
import sys
import time
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parents[1]

# GUI module detection keywords
GUI_KEYWORDS = (
    "about_dialog",
    "agent_dialog",
    "agent_e2e",
    "agent_lifecycle",
    "agent_session",
    "agent_ui",
    "alert",
    "apply_settings",
    "code_editor",
    "collection_export_ui",
    "collection_import",
    "collection_item",
    "collection_storage",
    "collection_tree",
    "collections_presenter",
    "connection_dialog",
    "conftest_lazy_qt",
    "curl_import_dialog",
    "dialog",
    "doc_editor",
    "editor",
    "env",
    "environment",
    "flow",
    "graph_view",
    "history_panel",
    "history_tree",
    "json_highlighter",
    "main_window",
    "mcp_controls",
    "mcp_dialog",
    "mcp_server",
    "mcp_tools",
    "menu",
    "new_tab",
    "panel",
    "preferences",
    "presenter",
    "request",
    "response",
    "save_async_gc_probe",
    "settings",
    "sidebar",
    "status_bar",
    "style",
    "tab",
    "table",
    "theme",
    "toolbar",
    "tree",
    "ui",
    "view",
    "websocket_client_ui",
    "widget",
    "window",
)


def discover_gui_test_modules(repo_root: Path = REPO_ROOT) -> list[Path]:
    """Discover all GUI-related test files in tests/ directory."""
    tests_dir = repo_root / "tests"
    if not tests_dir.is_dir():
        return []

    gui_modules: list[Path] = []
    for test_file in sorted(tests_dir.glob("test_*.py")):
        name = test_file.stem.lower()
        if any(kw in name for kw in GUI_KEYWORDS):
            gui_modules.append(test_file.relative_to(repo_root))
    return gui_modules


def get_environment_info() -> dict[str, str]:
    """Collect OS, Python, and Qt environment metadata."""
    py_ver = sys.version.split()[0]
    os_info = f"{platform.system()} {platform.release()} {platform.machine()}"

    pyside6_ver = "unknown"
    qt_ver = "unknown"
    try:
        import PySide6
        pyside6_ver = PySide6.__version__
        qt_ver = getattr(PySide6.QtCore, "__version__", "unknown")
    except Exception:
        pass

    return {
        "os": os_info,
        "python_version": py_ver,
        "pyside6_version": pyside6_ver,
        "qt_version": qt_ver,
        "qpa_platform": os.environ.get("QT_QPA_PLATFORM", "offscreen"),
    }


def describe_returncode(returncode: int) -> tuple[int | None, str]:
    """Decode process returncode into signal number and human name."""
    if returncode >= 0:
        return None, f"exit code {returncode}"
    signum = -returncode
    try:
        sig_name = signal.Signals(signum).name
    except ValueError:
        sig_name = f"SIGNAL_{signum}"
    return signum, sig_name


def run_pytest_subprocess(
    test_files: list[str | Path],
    timeout_seconds: float = 180.0,
    repo_root: Path = REPO_ROOT,
    extra_args: list[str] | None = None,
) -> dict[str, Any]:
    """Run a list of test files in an isolated pytest subprocess."""
    str_files = [str(f) for f in test_files]
    cmd = [
        sys.executable,
        "-m",
        "pytest",
        *str_files,
        "-q",
        "--tb=short",
        "-o",
        "faulthandler_timeout=60",
    ]
    if extra_args:
        cmd.extend(extra_args)

    env = {
        **os.environ,
        "QT_QPA_PLATFORM": "offscreen",
        "PYTHONPATH": str(repo_root),
        "PYTHONFAULTHANDLER": "1",
    }

    start_time = time.monotonic()
    timed_out = False
    stdout = ""
    stderr = ""
    returncode = 0

    try:
        proc = subprocess.run(
            cmd,
            cwd=str(repo_root),
            env=env,
            capture_output=True,
            text=True,
            timeout=timeout_seconds,
            check=False,
        )
        returncode = proc.returncode
        stdout = proc.stdout
        stderr = proc.stderr
    except subprocess.TimeoutExpired as exc:
        timed_out = True
        returncode = -1
        stdout = (
            exc.stdout.decode("utf-8", errors="replace")
            if isinstance(exc.stdout, bytes)
            else (exc.stdout or "")
        )
        stderr = (
            exc.stderr.decode("utf-8", errors="replace")
            if isinstance(exc.stderr, bytes)
            else (exc.stderr or "")
        )

    duration = time.monotonic() - start_time
    signum, sig_name = describe_returncode(returncode)

    # Detect crash signatures in stderr / stdout
    crash_site = None
    crash_method = None
    combined_err = f"{stdout}\n{stderr}"
    if "apply_theme" in combined_err or "style_manager.py" in combined_err:
        crash_site = "pypost/ui/styles/style_manager.py"
        crash_method = "StyleManager.apply_theme"
    elif "QStyleFactory" in combined_err:
        crash_site = "QStyleFactory.create"
        crash_method = "QStyleFactory"

    return {
        "command": cmd,
        "test_count": len(str_files),
        "exit_code": returncode if returncode >= 0 else 128 + abs(returncode),
        "returncode": returncode,
        "signal": signum,
        "signal_name": sig_name if signum else None,
        "timed_out": timed_out,
        "duration_seconds": round(duration, 3),
        "crash_site": crash_site,
        "crash_method": crash_method,
        "stdout_tail": stdout[-2000:] if len(stdout) > 2000 else stdout,
        "stderr_tail": stderr[-2000:] if len(stderr) > 2000 else stderr,
    }


def execute_harness(
    mode: str = "full",
    batch_size: int = 15,
    timeout_seconds: float = 180.0,
    quiet: bool = False,
    output_json: Path | None = None,
) -> dict[str, Any]:
    """Execute reproduction harness according to selected mode."""
    gui_modules = discover_gui_test_modules()
    env_info = get_environment_info()

    if not quiet:
        print(f"Discovered {len(gui_modules)} GUI test modules.")
        print(f"Mode: {mode}, Timeout: {timeout_seconds}s")

    timestamp = datetime.datetime.now(datetime.timezone.utc).isoformat()
    report: dict[str, Any] = {
        "timestamp": timestamp,
        "environment": env_info,
        "execution": {
            "mode": mode,
            "total_modules": len(gui_modules),
        },
    }

    if mode == "single":
        target = gui_modules[0] if gui_modules else Path("tests/test_about_dialog.py")
        if not quiet:
            print(f"Running single module: {target}")
        result = run_pytest_subprocess([target], timeout_seconds=timeout_seconds)
        report["execution"].update(result)
        report["status"] = "passed" if result["returncode"] == 0 else "failed"

    elif mode == "bounded":
        if not quiet:
            print(f"Running bounded batches (chunk size: {batch_size})")
        chunks = [gui_modules[i : i + batch_size] for i in range(0, len(gui_modules), batch_size)]
        batch_results = []
        all_passed = True
        total_duration = 0.0

        for idx, chunk in enumerate(chunks):
            if not quiet:
                print(f"  Executing batch {idx + 1}/{len(chunks)} ({len(chunk)} modules)...")
            res = run_pytest_subprocess(chunk, timeout_seconds=timeout_seconds)
            batch_results.append(res)
            total_duration += res["duration_seconds"]
            if res["returncode"] != 0:
                all_passed = False
                if not quiet:
                    print(f"  Batch {idx + 1} exited non-zero: {res['returncode']}")

        report["execution"]["batch_count"] = len(chunks)
        report["execution"]["batch_size"] = batch_size
        report["execution"]["duration_seconds"] = round(total_duration, 3)
        report["execution"]["all_batches_passed"] = all_passed
        report["execution"]["batches"] = batch_results
        report["status"] = "passed" if all_passed else "failed"

    else:  # mode == "full"
        if not quiet:
            print(f"Running full unmitigated batch ({len(gui_modules)} modules) in 1 process...")
        res = run_pytest_subprocess(gui_modules, timeout_seconds=timeout_seconds)
        report["execution"].update(res)
        report["execution"]["batch_count"] = 1
        is_segfault = (res["signal"] == signal.SIGSEGV or res["exit_code"] in (139, -11))
        if res["returncode"] != 0:
            report["status"] = "reproduced" if is_segfault else "crashed_or_failed"
        else:
            report["status"] = "passed_cleanly"

    if output_json:
        output_json.parent.mkdir(parents=True, exist_ok=True)
        with open(output_json, "w", encoding="utf-8") as f:
            json.dump(report, f, indent=2)
        if not quiet:
            print(f"Report written to {output_json}")

    return report


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Reproduction harness for large-batch apply_theme segfault"
    )
    parser.add_argument(
        "--mode",
        choices=["full", "bounded", "single"],
        default="full",
        help="Execution mode: full (~110 modules), bounded (chunked batches), single (one module)",
    )
    parser.add_argument(
        "--batch-size",
        type=int,
        default=15,
        help="Batch size for bounded mode (default: 15)",
    )
    parser.add_argument(
        "--timeout",
        type=float,
        default=180.0,
        help="Subprocess timeout in seconds (default: 180.0)",
    )
    parser.add_argument(
        "--output-json",
        type=Path,
        default=None,
        help="Path to write structured JSON report",
    )
    parser.add_argument(
        "--quiet",
        action="store_true",
        help="Suppress output except errors",
    )

    args = parser.parse_args()
    report = execute_harness(
        mode=args.mode,
        batch_size=args.batch_size,
        timeout_seconds=args.timeout,
        quiet=args.quiet,
        output_json=args.output_json,
    )

    if not args.quiet:
        print("\n=== Execution Summary ===")
        print(f"Status: {report.get('status')}")
        exec_info = report.get("execution", {})
        if "exit_code" in exec_info:
            print(f"Exit Code: {exec_info.get('exit_code')}")
        if "signal_name" in exec_info and exec_info.get("signal_name"):
            print(f"Signal: {exec_info.get('signal_name')}")
        if "duration_seconds" in exec_info:
            print(f"Duration: {exec_info.get('duration_seconds')}s")

    return 0 if report.get("status") in ("passed", "passed_cleanly") else 1


if __name__ == "__main__":
    sys.exit(main())
