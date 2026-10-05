"""Automated failing repro tests for PYPOST-1116.

Verifies that tests/_pytest_plugins/duration_report.py properly identifies xfail and
XPASS outcomes via the wasxfail attribute, avoiding misclassifying them as plain
skipped or passed, and avoids terminal summary crashes under -ra / -rs flags.
"""

from __future__ import annotations

import io
from typing import Any

import pytest
from _pytest.reports import TestReport
from _pytest.terminal import TerminalReporter

from tests._pytest_plugins import duration_report

pytestmark = pytest.mark.timeout(30)
pytest_plugins = ["pytester"]


def _build_report(
    *,
    outcome: str = "passed",
    when: str = "call",
    duration: float = 0.015,
    wasxfail: str | None = None,
    longrepr: Any = None,
) -> TestReport:
    """Create a TestReport instance for hook testing."""
    rep = TestReport(
        nodeid="tests/test_sample.py::test_case",
        location=("tests/test_sample.py", 1, "test_case"),
        keywords={},
        outcome=outcome,
        longrepr=longrepr,
        when=when,
        duration=duration,
    )
    if wasxfail is not None:
        rep.wasxfail = wasxfail
    return rep


@pytest.mark.timeout(30)
def test_pytest_report_teststatus_xfail_call_outcome() -> None:
    """An xfail call report must return category 'xfailed', letter 'x', and 'XFAIL [...]'."""
    rep = _build_report(
        outcome="skipped",
        when="call",
        duration=0.015,
        wasxfail="known bug in implementation",
    )
    res = duration_report.pytest_report_teststatus(rep, None)
    assert res is not None
    category, letter, word = res
    assert category == "xfailed"
    assert letter == "x"
    assert word == "XFAIL [15ms]"


@pytest.mark.timeout(30)
def test_pytest_report_teststatus_xpass_call_outcome() -> None:
    """An XPASS call report must return category 'xpassed', letter 'X', and 'XPASS [...]'."""
    rep = _build_report(
        outcome="passed",
        when="call",
        duration=0.015,
        wasxfail="bug unexpectedly passed",
    )
    res = duration_report.pytest_report_teststatus(rep, None)
    assert res is not None
    category, letter, word = res
    assert category == "xpassed"
    assert letter == "X"
    assert word == "XPASS [15ms]"


@pytest.mark.timeout(30)
def test_pytest_report_teststatus_plain_skipped_call_outcome() -> None:
    """A plain skip call report (without wasxfail) returns category 'skipped'."""
    rep = _build_report(
        outcome="skipped",
        when="call",
        duration=0.015,
    )
    res = duration_report.pytest_report_teststatus(rep, None)
    assert res is not None
    category, letter, word = res
    assert category == "skipped"
    assert letter == "s"
    assert word == "SKIPPED [15ms]"


@pytest.mark.timeout(30)
def test_pytest_report_teststatus_plain_passed_call_outcome() -> None:
    """A plain passed call report (without wasxfail) returns category 'passed'."""
    rep = _build_report(
        outcome="passed",
        when="call",
        duration=0.015,
    )
    res = duration_report.pytest_report_teststatus(rep, None)
    assert res is not None
    category, letter, word = res
    assert category == "passed"
    assert letter == "."
    assert word == "PASSED [15ms]"


@pytest.mark.timeout(30)
@pytest.mark.parametrize("when", ["setup", "teardown"])
@pytest.mark.parametrize("wasxfail", [None, "some reason"])
def test_pytest_report_teststatus_non_call_phases_return_none(
    when: str,
    wasxfail: str | None,
) -> None:
    """Non-call phases (setup, teardown) must return None to preserve native formatting."""
    rep = _build_report(
        outcome="passed",
        when=when,
        duration=0.005,
        wasxfail=wasxfail,
    )
    res = duration_report.pytest_report_teststatus(rep, None)
    assert res is None


@pytest.mark.timeout(30)
@pytest.mark.parametrize("reportchars", ["ra", "rs", "a", "s"])
def test_terminal_summary_xfail_report_no_crash(reportchars: str) -> None:
    """Verify TerminalReporter.short_test_summary with -ra / -rs does not crash on xfail."""
    config = pytest.Config.fromdictargs({"reportchars": reportchars}, [])
    output_buffer = io.StringIO()
    output_buffer.isatty = lambda: False
    reporter = TerminalReporter(config, output_buffer)

    rep = _build_report(
        outcome="skipped",
        when="call",
        duration=0.015,
        wasxfail="known defect",
        longrepr="AssertionError: test failed as expected",
    )
    res = duration_report.pytest_report_teststatus(rep, config)
    assert res is not None
    category, _, _ = res
    reporter.stats.setdefault(category, []).append(rep)

    # If misclassified as 'skipped', short_test_summary raises AssertionError
    # because rep.longrepr is not a 3-tuple (filepath, lineno, reason).
    reporter.short_test_summary()


@pytest.mark.timeout(30)
def test_duration_report_xfail_terminal_integration(pytester: pytest.Pytester) -> None:
    """Integration test verifying pytest -ra with xfail/xpass runs and summaries cleanly."""
    pytester.makepyfile(
        """
        import pytest

        @pytest.mark.xfail(strict=False, reason="known issue")
        def test_failing_xfail():
            assert False

        @pytest.mark.xfail(strict=False, reason="resolved issue")
        def test_passing_xpass():
            assert True

        def test_standard_pass():
            assert True
        """
    )
    result = pytester.runpytest(
        "-p", "tests._pytest_plugins.duration_report",
        "-v",
        "-ra",
        "-o", "addopts=",
    )
    assert result.ret == 0
    result.stdout.fnmatch_lines([
        "*XFAIL*test_failing_xfail*",
        "*XPASS*test_passing_xpass*",
        "*1 passed, 1 xfailed, 1 xpassed*",
    ])
