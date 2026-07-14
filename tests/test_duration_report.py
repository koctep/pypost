"""Tests for duration_report pytest plugin (PYPOST-790)."""

from __future__ import annotations

import pytest

from tests._pytest_plugins.duration_report import format_duration

pytestmark = pytest.mark.timeout(10)


@pytest.mark.parametrize(
    ("seconds", "expected"),
    [
        (0.0, "0ms"),
        (0.004, "4ms"),
        (0.45, "450ms"),
        (0.999, "999ms"),
        (1.0, "1.00s"),
        (1.234, "1.23s"),
        (12.345, "12.35s"),
    ],
)
def test_format_duration(seconds: float, expected: str) -> None:
    assert format_duration(seconds) == expected
