"""Pytest plugin: per-test duration in verbose output and top-N slowest summary."""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from _pytest.reports import TestReport
    from _pytest.terminal import TerminalReporter

TOP_N = 5
_call_durations: list[tuple[str, float]] = []


def format_duration(seconds: float) -> str:
    """Human-readable duration for terminal output."""
    if seconds >= 1.0:
        return f"{seconds:.2f}s"
    return f"{int(round(seconds * 1000))}ms"


def pytest_runtest_logreport(report: TestReport) -> None:
    if report.when == "call":
        _call_durations.append((report.nodeid, report.duration))


def pytest_report_teststatus(report: TestReport, config):
    if report.when != "call":
        return None
    letters = {"passed": ".", "failed": "F", "skipped": "s", "error": "E"}
    letter = letters.get(report.outcome, "?")
    word = f"{report.outcome.upper()} [{format_duration(report.duration)}]"
    return report.outcome, letter, word


def pytest_terminal_summary(
    terminalreporter: TerminalReporter,
    exitstatus: int,
    config,
) -> None:
    if not _call_durations:
        return
    terminalreporter.write_sep("=", f"top {TOP_N} slowest tests")
    for nodeid, duration in sorted(_call_durations, key=lambda item: -item[1])[:TOP_N]:
        terminalreporter.write_line(f"{format_duration(duration):>8}  {nodeid}")
