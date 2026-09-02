"""PYPOST-1179: deterministic repro for the scoped mypy baseline refresh."""

from __future__ import annotations

import pytest

from scripts.check_mypy_baseline import BaselineEntry, MypyError, _diff_errors, _parse_errors

pytestmark = pytest.mark.timeout(30)


STREAM_KEY = (
    "pypost/core/websocket_stream_export.py",
    "union-attr",
    "Item MessageStream has no attribute snapshot",
)
SETTINGS_KEYS = [
    (
        "pypost/ui/dialogs/settings_dialog.py",
        "assignment",
        'Incompatible types in assignment (expression has type "AppSettings", '
        'variable has type "None")',
    ),
    (
        "pypost/ui/dialogs/settings_dialog.py",
        "attr-defined",
        '"type[QDialogButtonBox]" has no attribute "Cancel"',
    ),
    (
        "pypost/ui/dialogs/settings_dialog.py",
        "attr-defined",
        '"type[QDialogButtonBox]" has no attribute "Save"',
    ),
    (
        "pypost/ui/dialogs/settings_dialog.py",
        "return-value",
        "Incompatible return value type (got \"None\", expected \"AppSettings\")",
    ),
]
NEW_SETTINGS_KEY = (
    "pypost/ui/dialogs/settings_dialog.py",
    "assignment",
    "AppSettings is incompatible with None",
)
UNRELATED_KEY = (
    "pypost/models/app_settings.py",
    "return-value",
    "unrelated fixture diagnostic",
)


def _current_output() -> str:
    return "\n".join(
        [
            *(
                f"{path}:42: error: {message} [{code}]"
                for path, code, message in SETTINGS_KEYS
            ),
            f"pypost/ui/dialogs/settings_dialog.py:99: error: {NEW_SETTINGS_KEY[2]} "
            f"[{NEW_SETTINGS_KEY[1]}]",
            f"pypost/models/app_settings.py:17: error: {UNRELATED_KEY[2]} "
            f"[{UNRELATED_KEY[1]}]",
        ],
    )


def test_named_baseline_reconciliation_reports_pre_refresh_drift() -> None:
    """Red before Step 4: the stale stream baseline and new UI error drift."""
    baseline = [BaselineEntry(*STREAM_KEY), *(BaselineEntry(*key) for key in SETTINGS_KEYS)]
    current = _parse_errors(_current_output())

    new_keys, fixed_keys = _diff_errors(current, baseline)

    assert fixed_keys == [STREAM_KEY]
    assert NEW_SETTINGS_KEY in new_keys
    assert UNRELATED_KEY in new_keys

    scoped_new = [key for key in new_keys if key[0].startswith("pypost/ui/dialogs/")]
    scoped_fixed = [key for key in fixed_keys if key[0].startswith("pypost/core/")]
    assert scoped_new == [NEW_SETTINGS_KEY]
    assert scoped_fixed == [STREAM_KEY]


def test_named_baseline_reconciliation_is_clean_after_refresh() -> None:
    """After refresh, named-path drift is empty and unrelated drift remains separate."""
    refreshed_baseline = [
        *(BaselineEntry(*key) for key in SETTINGS_KEYS),
        BaselineEntry(*NEW_SETTINGS_KEY),
    ]
    current = _parse_errors(_current_output())

    new_keys, fixed_keys = _diff_errors(current, refreshed_baseline)

    assert [key for key in new_keys if key[0].startswith("pypost/ui/dialogs/")] == []
    assert [key for key in fixed_keys if key[0].startswith("pypost/core/")] == []
    assert new_keys == [UNRELATED_KEY]
    assert fixed_keys == []
