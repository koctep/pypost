"""Convention lock: dialog-settle proofs use shared helper (PYPOST-936)."""

from __future__ import annotations

from pathlib import Path

import pytest

pytestmark = pytest.mark.timeout(10)

_TESTS_DIR = Path(__file__).resolve().parent
_DIALOG_SETTLE_MODULE = _TESTS_DIR / "test_agent_dialog_settle_e2e.py"
_HELPER_IMPORT = "from tests.helpers.agent_e2e_dialog_settle import"
_HELPER_CALL = "run_product_dialog_settle"


def _module_source(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def test_dialog_settle_module_uses_shared_modal_settle_helper() -> None:
    """Both product-dialog settle proofs must use run_product_dialog_settle."""
    assert _DIALOG_SETTLE_MODULE.is_file(), f"missing {_DIALOG_SETTLE_MODULE}"
    source = _module_source(_DIALOG_SETTLE_MODULE)

    if "agent_e2e_dialog_settle" not in source:
        pytest.fail(
            f"{_DIALOG_SETTLE_MODULE.name} must import from "
            "tests.helpers.agent_e2e_dialog_settle once a second proof exists "
            "(PYPOST-936)"
        )
    if _HELPER_IMPORT not in source:
        pytest.fail(
            f"{_DIALOG_SETTLE_MODULE.name} must import run_product_dialog_settle "
            "from tests.helpers.agent_e2e_dialog_settle"
        )

    call_count = source.count(_HELPER_CALL)
    if call_count < 2:
        pytest.fail(
            f"{_DIALOG_SETTLE_MODULE.name} must call {_HELPER_CALL} in both "
            f"dialog-settle proofs; found {call_count} call(s)"
        )

    if "QTimer.singleShot(" in source or "from PySide6.QtCore import QTimer" in source:
        pytest.fail(
            f"{_DIALOG_SETTLE_MODULE.name} must not inline QTimer.singleShot; "
            "use run_product_dialog_settle from tests.helpers.agent_e2e_dialog_settle"
        )
