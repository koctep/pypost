"""Unit tests for scripts/parse_test_log_inventory.py (PYPOST-665)."""

from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

import pytest

_SCRIPTS = Path(__file__).resolve().parents[1] / "scripts"
_SPEC = importlib.util.spec_from_file_location(
    "parse_test_log_inventory",
    _SCRIPTS / "parse_test_log_inventory.py",
)
assert _SPEC and _SPEC.loader
_inventory = importlib.util.module_from_spec(_SPEC)
sys.modules["parse_test_log_inventory"] = _inventory
_SPEC.loader.exec_module(_inventory)


@pytest.mark.timeout(30)
def test_classify_group_marks_audited_presenter_loggers_expected() -> None:
    assert (
        _inventory.classify_group(
            "pypost.ui.presenters.collection_tree_actions",
            "collection_item_delete_failed item_type=collection",
        )
        == "expected"
    )
    assert (
        _inventory.classify_group(
            "pypost.ui.presenters.tabs_presenter",
            "request_error error_msg=connection refused",
        )
        == "expected"
    )


@pytest.mark.timeout(30)
def test_classify_group_marks_request_service_retry_errors_expected() -> None:
    assert (
        _inventory.classify_group(
            "pypost.core.request_service",
            "request_execution_failed method=GET url=http://example.com",
        )
        == "expected"
    )
