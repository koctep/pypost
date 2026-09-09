"""Regression coverage for the isolated environment-dialog crash harness."""

from __future__ import annotations

import os
import signal

import pytest

from scripts.repro_environment_dialog_wayland import classify_process_result, run_harness

pytestmark = pytest.mark.timeout(60)


@pytest.mark.parametrize(
    ("returncode", "timed_out", "expected"),
    [
        (0, False, ("passed", None)),
        (2, False, ("failed", None)),
        (-signal.SIGSEGV, False, ("signal_exit", "SIGSEGV")),
        (-1, True, ("timeout", None)),
    ],
)
def test_process_result_classification(returncode, timed_out, expected) -> None:
    assert classify_process_result(returncode, timed_out=timed_out) == expected


def test_repeated_empty_cell_clicks_exit_normally_offscreen() -> None:
    report = run_harness(
        qpa_platform="offscreen",
        cycles=10,
        timeout_seconds=20,
    )

    assert report["status"] == "passed", report
    assert report["returncode"] == 0
    assert '"cell_widgets": [false, false]' in report["stdout_tail"]


@pytest.mark.wayland
def test_repeated_empty_cell_clicks_exit_normally_on_wayland() -> None:
    if os.environ.get("PYPOST_RUN_WAYLAND_TESTS") != "1":
        pytest.skip("set PYPOST_RUN_WAYLAND_TESTS=1 to enable the Wayland subprocess smoke")
    if not os.environ.get("WAYLAND_DISPLAY"):
        pytest.skip("WAYLAND_DISPLAY is not available")

    report = run_harness(
        qpa_platform="wayland",
        cycles=100,
        timeout_seconds=30,
        capture_native_backtrace=True,
    )

    assert report["status"] == "passed", report
    assert report["returncode"] == 0
