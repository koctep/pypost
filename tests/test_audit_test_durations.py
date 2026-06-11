"""Tests for scripts/audit_test_durations.py (PYPOST-573)."""

from __future__ import annotations

import pytest

from scripts.audit_test_durations import audit_durations

pytestmark = pytest.mark.timeout(30)


SAMPLE_DURATIONS = """\
============================= slowest durations ==============================
8.50s call tests/test_example.py::test_slow
1.00s call tests/test_example.py::test_fast
"""


def test_audit_warns_at_eighty_percent(tmp_path):
    tests_dir = tmp_path / "tests"
    tests_dir.mkdir()
    (tests_dir / "test_example.py").write_text(
        "import pytest\npytestmark = pytest.mark.timeout(10)\n"
        "def test_slow(): pass\ndef test_fast(): pass\n",
        encoding="utf-8",
    )
    durations_file = tmp_path / "durations.txt"
    durations_file.write_text(SAMPLE_DURATIONS, encoding="utf-8")

    warnings, failures, exit_code = audit_durations(durations_file, tests_dir)

    assert exit_code == 0
    assert not failures
    assert len(warnings) == 1
    assert "test_slow" in warnings[0]


def test_audit_fails_at_ninety_five_percent(tmp_path):
    tests_dir = tmp_path / "tests"
    tests_dir.mkdir()
    (tests_dir / "test_example.py").write_text(
        "import pytest\npytestmark = pytest.mark.timeout(10)\n"
        "def test_slow(): pass\n",
        encoding="utf-8",
    )
    durations_file = tmp_path / "durations.txt"
    durations_file.write_text(
        "============================= slowest durations ==============================\n"
        "9.60s call tests/test_example.py::test_slow\n",
        encoding="utf-8",
    )

    warnings, failures, exit_code = audit_durations(durations_file, tests_dir)

    assert exit_code == 1
    assert len(failures) == 1
    assert not warnings
