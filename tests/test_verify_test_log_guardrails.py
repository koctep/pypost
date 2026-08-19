"""Unit tests for scripts/verify_test_log_guardrails.py (PYPOST-572)."""
from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

import pytest
import yaml

pytestmark = pytest.mark.timeout(30)

REPO_ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = REPO_ROOT / "scripts"
ALLOWLIST_PATH = REPO_ROOT / "tests" / "expected_log_allowlist.yaml"


def _load_guardrails_module():
    spec = importlib.util.spec_from_file_location(
        "verify_test_log_guardrails",
        SCRIPTS / "verify_test_log_guardrails.py",
    )
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    sys.modules["verify_test_log_guardrails"] = module
    spec.loader.exec_module(module)
    return module


guardrails = _load_guardrails_module()


def _sample_log(*error_lines: str) -> list[str]:
    header = [
        "tests/test_retry.py::TestBodyErrorNonRetryable::test_body_error_not_retried PASSED",
    ]
    return header + list(error_lines)


@pytest.mark.timeout(30)
def test_load_allowlist_reads_baseline_and_rules() -> None:
    allowlist = guardrails.load_allowlist(ALLOWLIST_PATH)
    assert allowlist.baseline_error_count == 146
    assert allowlist.error_margin == 5
    assert len(allowlist.rules) >= 20
    assert any(
        rule.logger == "pypost.core.request_service"
        and rule.message_prefix == "request_execution_failed"
        for rule in allowlist.rules
    )


@pytest.mark.timeout(30)
def test_allowed_error_lines_pass_verification() -> None:
    allowlist = guardrails.load_allowlist(ALLOWLIST_PATH)
    lines = _sample_log(
        "20:30:26 ERROR pypost.core.request_service: "
        "request_execution_failed method=GET url='http://x'",
        "20:30:27 ERROR pypost.core.qt.worker: RequestWorker unexpected error: boom",
    )
    result = guardrails.verify_log_lines(lines, allowlist)
    assert result.unknown_errors == ()
    assert result.count_exceeded is False


@pytest.mark.timeout(30)
def test_unknown_error_lines_fail_verification() -> None:
    allowlist = guardrails.load_allowlist(ALLOWLIST_PATH)
    lines = _sample_log(
        "20:30:26 ERROR pypost.core.request_service: "
        "request_execution_failed method=GET url='http://x'",
        "20:30:26 ERROR pypost.core.unknown_module: totally_unexpected_failure detail=boom",
    )
    result = guardrails.verify_log_lines(lines, allowlist)
    assert len(result.unknown_errors) == 1
    assert result.unknown_errors[0]["logger"] == "pypost.core.unknown_module"


@pytest.mark.timeout(30)
def test_error_count_above_baseline_plus_margin_fails() -> None:
    data = yaml.safe_load(ALLOWLIST_PATH.read_text(encoding="utf-8"))
    data["baseline_error_count"] = 1
    data["error_margin"] = 0
    allowlist = guardrails.Allowlist(
        baseline_error_count=1,
        error_margin=0,
        rules=tuple(
            guardrails.AllowlistRule(
                message_prefix=str(rule["message_prefix"]),
                logger=rule.get("logger"),
            )
            for rule in data["rules"]
        ),
    )
    lines = _sample_log(
        "20:30:26 ERROR pypost.core.request_service: request_execution_failed x=1",
        "20:30:26 ERROR pypost.core.qt.worker: RequestWorker unexpected error: a",
        "20:30:26 ERROR pypost.core.qt.worker: RequestWorker unexpected error: b",
    )
    result = guardrails.verify_log_lines(lines, allowlist)
    assert result.error_count == 3
    assert result.count_exceeded is True
    assert result.max_allowed == 1


@pytest.mark.timeout(30)
def test_message_prefix_only_rule_matches_any_logger() -> None:
    allowlist = guardrails.Allowlist(
        baseline_error_count=10,
        error_margin=5,
        rules=(guardrails.AllowlistRule(message_prefix="shared_failure_event"),),
    )
    lines = _sample_log(
        "20:30:26 ERROR pypost.core.alpha: shared_failure_event detail=1",
        "20:30:26 ERROR pypost.core.beta: shared_failure_event detail=2",
    )
    result = guardrails.verify_log_lines(lines, allowlist)
    assert result.unknown_errors == ()


@pytest.mark.timeout(30)
def test_main_exits_nonzero_on_unknown_errors(tmp_path: Path) -> None:
    log_file = tmp_path / "pytest.log"
    log_file.write_text(
        "20:30:26 ERROR pypost.core.unknown: surprise failure\n",
        encoding="utf-8",
    )
    assert guardrails.main.__module__  # keep reference for coverage
    argv = ["verify_test_log_guardrails.py", str(log_file)]
    old_argv = sys.argv
    try:
        sys.argv = argv
        exit_code = guardrails.main()
    finally:
        sys.argv = old_argv
    assert exit_code == 1
