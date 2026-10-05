"""Automated failing repro tests for PYPOST-1258.

Verifies the presence and completeness of dedicated CLI tests for
`scripts/audit_baseline_metrics.py` and `scripts/audit_dialogs_inventory.py`.

Prior to Step 4 implementation of `tests/test_audit_scripts_cli.py`, this test suite
fails with ModuleNotFoundError.
"""

from __future__ import annotations

import importlib
from typing import Any

import pytest

pytestmark = pytest.mark.timeout(30)

EXPECTED_BASELINE_METRICS_TESTS = (
    "test_default_prints_markdown_to_stdout",
    "test_json_export_writes_file",
    "test_markdown_export_creates_parent_and_file",
    "test_combined_json_and_markdown",
    "test_check_clean_returns_zero",
    "test_check_violation_returns_one_and_writes_stderr",
    "test_invalid_argument_exits_code_two",
    "test_missing_option_argument_exits_code_two",
)

EXPECTED_DIALOGS_INVENTORY_TESTS = (
    "test_default_prints_tsv_to_stdout",
    "test_markdown_flag_prints_table",
    "test_json_flag_prints_valid_json",
    "test_check_clean_returns_zero_and_reports_ok",
    "test_check_missing_report_returns_one",
    "test_check_missing_dialog_returns_one",
    "test_invalid_argument_exits_code_two",
    "test_unexpected_positional_arg_exits_code_two",
)


def _load_audit_scripts_cli_module() -> Any:
    """Import and return the dedicated audit scripts CLI test module."""
    return importlib.import_module("tests.test_audit_scripts_cli")


@pytest.mark.timeout(30)
def test_audit_scripts_cli_module_exists() -> None:
    """Verify that tests.test_audit_scripts_cli exists and exports primary test classes."""
    cli_test_module = _load_audit_scripts_cli_module()
    assert hasattr(cli_test_module, "TestAuditBaselineMetricsCLI"), (
        "tests.test_audit_scripts_cli must define TestAuditBaselineMetricsCLI"
    )
    assert hasattr(cli_test_module, "TestAuditDialogsInventoryCLI"), (
        "tests.test_audit_scripts_cli must define TestAuditDialogsInventoryCLI"
    )


@pytest.mark.timeout(30)
def test_audit_baseline_metrics_cli_test_suite_complete() -> None:
    """Verify that TestAuditBaselineMetricsCLI implements all contract test methods."""
    cli_test_module = _load_audit_scripts_cli_module()
    cls = getattr(cli_test_module, "TestAuditBaselineMetricsCLI")
    for method_name in EXPECTED_BASELINE_METRICS_TESTS:
        assert hasattr(cls, method_name), (
            f"TestAuditBaselineMetricsCLI missing required test method: {method_name}"
        )
        assert callable(getattr(cls, method_name)), (
            f"TestAuditBaselineMetricsCLI.{method_name} must be a callable test method"
        )


@pytest.mark.timeout(30)
def test_audit_dialogs_inventory_cli_test_suite_complete() -> None:
    """Verify that TestAuditDialogsInventoryCLI implements all contract test methods."""
    cli_test_module = _load_audit_scripts_cli_module()
    cls = getattr(cli_test_module, "TestAuditDialogsInventoryCLI")
    for method_name in EXPECTED_DIALOGS_INVENTORY_TESTS:
        assert hasattr(cls, method_name), (
            f"TestAuditDialogsInventoryCLI missing required test method: {method_name}"
        )
        assert callable(getattr(cls, method_name)), (
            f"TestAuditDialogsInventoryCLI.{method_name} must be a callable test method"
        )
