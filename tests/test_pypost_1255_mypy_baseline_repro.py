"""Focused regression tests for the PYPOST-1255 mypy baseline increment."""

from __future__ import annotations

import pytest

from scripts.check_mypy_baseline import (
    BaselineEntry,
    MypyError,
    _diff_errors,
    _parse_errors,
    _run_mypy,
)

pytestmark = pytest.mark.timeout(60)

TARGET_KEY = (
    "pypost/core/alert_manager.py",
    "arg-type",
    'Argument 1 to "_webhook_log_target" has incompatible type "str | None"; '
    'expected "str"',
)


def test_alert_manager_webhook_log_target_diagnostic_is_retired() -> None:
    """Require the selected alert-manager diagnostic to disappear after Step 4."""
    _returncode, output = _run_mypy()
    current = _parse_errors(output)
    target_count = sum(
        (error.path, error.code, error.message) == TARGET_KEY for error in current
    )

    assert target_count == 0, (
        "The PYPOST-1255 target diagnostic must be absent after the narrow typing fix; "
        f"mypy currently emits {target_count} occurrence(s) for {TARGET_KEY!r}."
    )


def test_reconciliation_distinguishes_fixed_debt_from_new_model_error() -> None:
    """Keep a retired baseline key distinct from a synthetic new scoped diagnostic."""
    baseline = [
        BaselineEntry(path=TARGET_KEY[0], code=TARGET_KEY[1], message=TARGET_KEY[2]),
    ]
    synthetic_key = (
        "pypost/models/synthetic.py",
        "assignment",
        "Synthetic new diagnostic",
    )
    current = [
        MypyError(
            path=synthetic_key[0],
            line=12,
            code=synthetic_key[1],
            message=synthetic_key[2],
        ),
    ]

    new_keys, fixed_keys = _diff_errors(current, baseline)

    assert new_keys == [synthetic_key]
    assert fixed_keys == [TARGET_KEY]
