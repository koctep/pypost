"""PYPOST-1117 / PYPOST-1212: Subprocess-based reproduction and baseline verification
for large-batch GUI apply_theme segmentation fault.

Background & Architecture (see ai-tasks/PYPOST-1214/20-architecture.md):
------------------------------------------------------------------------
Executing a large batch of GUI test modules (~110 modules) consecutively in a
single long-running OS process sharing the module-scoped QApplication instance
triggers a native segmentation fault (SIGSEGV / exit code 139 / returncode -11)
originating from StyleManager.apply_theme() (app.setStyle / QStyleFactory.create("Fusion")).

This module defines:
1. An empirical baseline test proving that single or bounded batches of GUI test
   modules execute cleanly (exit code 0).
2. The unmitigated large-batch mode remains available in the diagnostic harness,
   but is not a CI assertion because it intentionally reproduces the defect.
"""

from __future__ import annotations

import os
import signal
import subprocess
import sys
from pathlib import Path

import pytest

pytestmark = [
    pytest.mark.timeout(240),
    pytest.mark.slow,
]

_REPO_ROOT = Path(__file__).resolve().parents[1]

# Representative bounded subset of GUI modules known to pass cleanly
_BOUNDED_GUI_MODULES = [
    "tests/test_about_dialog.py",
    "tests/test_style_manager_theme.py",
    "tests/test_style_manager_appearance.py",
    "tests/test_tab_layout_regression.py",
]

# Core GUI test modules forming the large-batch surface
_LARGE_BATCH_GUI_PATTERNS = [
    "tests/test_main_window*.py",
    "tests/test_settings*.py",
    "tests/test_style*.py",
    "tests/test_env*.py",
    "tests/test_collection*.py",
    "tests/test_agent_dialog*.py",
    "tests/test_tabs*.py",
    "tests/test_mcp_*.py",
    "tests/test_about_dialog.py",
    "tests/test_alert_manager.py",
    "tests/test_code_editor*.py",
]


def _discover_batch_modules(repo_root: Path = _REPO_ROOT) -> list[str]:
    """Resolve matched GUI test files for the large-batch workload."""
    matched: list[str] = []
    seen: set[str] = set()
    for pattern in _LARGE_BATCH_GUI_PATTERNS:
        for p in sorted(repo_root.glob(pattern)):
            rel_str = str(p.relative_to(repo_root))
            if rel_str not in seen and p.is_file() and p.name != "test_gui_batch_segfault_repro.py":
                seen.add(rel_str)
                matched.append(rel_str)
    return matched


def _describe_returncode(returncode: int) -> str:
    """Render a subprocess return code, naming the signal for negative codes."""
    if returncode >= 0:
        return f"exit code {returncode}"
    raw_signum = -returncode
    try:
        name = signal.Signals(raw_signum).name
    except ValueError:
        name = "unknown signal"
    return f"killed by signal {raw_signum} ({name})"


def _run_isolated_pytest_batch(
    modules: list[str],
    timeout_s: float = 180.0,
    repo_root: Path = _REPO_ROOT,
) -> subprocess.CompletedProcess[str]:
    """Run specified test modules in a single isolated subprocess under offscreen QPA."""
    env = {
        **os.environ,
        "QT_QPA_PLATFORM": "offscreen",
        "PYTHONPATH": str(repo_root),
        "PYTHONFAULTHANDLER": "1",
    }
    cmd = [
        sys.executable,
        "-m",
        "pytest",
        *modules,
        "-q",
        "--tb=short",
        "-m",
        "not slow",
    ]
    return subprocess.run(
        cmd,
        cwd=repo_root,
        env=env,
        capture_output=True,
        text=True,
        timeout=timeout_s,
        check=False,
    )


def test_bounded_gui_batch_execution_passes_cleanly() -> None:
    """Verify that a bounded subset of GUI modules executes cleanly (exit code 0).

    This provides the empirical contrast: individual or small batches of GUI
    modules do not trigger the cumulative apply_theme / QStyleFactory segfault.
    """
    proc = _run_isolated_pytest_batch(_BOUNDED_GUI_MODULES, timeout_s=45.0)
    assert proc.returncode == 0, (
        f"Bounded GUI batch failed unexpectedly ({_describe_returncode(proc.returncode)}):\n"
        f"STDOUT:\n{proc.stdout[-2000:]}\n"
        f"STDERR:\n{proc.stderr[-2000:]}"
    )


def test_large_batch_gui_execution_uses_bounded_processes() -> None:
    """Execute the large GUI module workload in bounded isolated processes.

    The mitigation bounds QApplication lifetime by starting a fresh process for each
    chunk. The full unmitigated mode remains available for diagnosis but is not run as
    a normal regression assertion.
    """
    target_modules = _discover_batch_modules()
    assert len(target_modules) >= 10, (
        f"Expected at least 10 GUI test modules, found {len(target_modules)}"
    )

    try:
        chunks = [target_modules[i : i + 4] for i in range(0, len(target_modules), 4)]
        results = [
            _run_isolated_pytest_batch(chunk, timeout_s=180.0) for chunk in chunks
        ]
    except subprocess.TimeoutExpired as exc:
        stdout = exc.stdout or ""
        stderr = exc.stderr or ""
        pytest.fail(
            f"Large-batch GUI execution timed out after 180s.\n"
            f"STDOUT:\n{stdout[-1000:]}\n"
            f"STDERR:\n{stderr[-1000:]}"
        )

    failures = [(idx, proc) for idx, proc in enumerate(results, 1) if proc.returncode != 0]
    if failures:
        idx, proc = failures[0]
        desc = _describe_returncode(proc.returncode)
        pytest.fail(
            f"Bounded GUI batch {idx} failed with {desc}.\n"
            f"Modules tested ({len(target_modules)}): {target_modules[:10]} ...\n"
            f"STDERR:\n{proc.stderr[-2000:]}\nSTDOUT:\n{proc.stdout[-2000:]}"
        )
