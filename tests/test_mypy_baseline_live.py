"""Live mypy baseline gate test (PYPOST-1241)."""

from __future__ import annotations

import sys

import pytest

import scripts.check_mypy_baseline as check_mypy_baseline
from scripts.check_mypy_baseline import (
    _diff_errors,
    _load_baseline,
    _parse_errors,
    _run_mypy,
)

pytestmark = pytest.mark.timeout(60)


def test_mypy_baseline_live_gate_passes(
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    """Assert that the live mypy baseline gate passes with zero new and zero fixed errors.

    Demonstrates the PYPOST-1241 defect: on current HEAD, live mypy generates
    33 new errors and 4 resolved baseline errors against mypy-baseline.json.
    check_mypy_baseline.main() exits with code 1 until type discrepancies
    are resolved and the baseline is reconciled.
    """
    _returncode, output = _run_mypy()
    current = _parse_errors(output)
    baseline = _load_baseline()
    new_keys, fixed_keys = _diff_errors(current, baseline)

    monkeypatch.setattr(sys, "argv", ["check_mypy_baseline.py"])
    exit_code = check_mypy_baseline.main()
    captured = capsys.readouterr()

    assert exit_code == 0, (
        f"check_mypy_baseline.main() returned exit code {exit_code} "
        f"(detected {len(new_keys)} new errors and {len(fixed_keys)} resolved baseline errors).\n"
        f"Stderr output:\n{captured.err}"
    )
    assert new_keys == [], f"Expected 0 new errors, found {len(new_keys)}"
    assert fixed_keys == [], f"Expected 0 resolved errors, found {len(fixed_keys)}"
