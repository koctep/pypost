"""Failing repro tests for malformed WORKER_TIMEOUT diagnostic logging (PYPOST-1260)."""

from __future__ import annotations

import logging

import pytest

from scripts.run_parallel_tests import (
    RunnerValidationError,
    get_worker_timeout,
)

pytestmark = pytest.mark.timeout(30)

INVALID_TIMEOUT_ENV_VALUES = [
    "",
    "   ",
    "invalid",
    "abc",
    "0",
    "-5",
    "-10",
    "nan",
]


@pytest.mark.timeout(30)
@pytest.mark.parametrize("invalid_env", INVALID_TIMEOUT_ENV_VALUES)
def test_malformed_worker_timeout_env_emits_warning_with_cli_override(
    monkeypatch: pytest.MonkeyPatch,
    caplog: pytest.LogCaptureFixture,
    invalid_env: str,
) -> None:
    """When CLI override is provided, invalid env emits warning log and CLI takes precedence."""
    monkeypatch.setenv("WORKER_TIMEOUT", invalid_env)
    with caplog.at_level(logging.WARNING, logger="scripts.run_parallel_tests"):
        resolved = get_worker_timeout(45.0)

    assert resolved == 45.0
    warning_records = [
        rec
        for rec in caplog.records
        if rec.levelno == logging.WARNING
        and "invalid_worker_timeout_env" in rec.getMessage()
    ]
    assert len(warning_records) == 1, (
        f"Expected 1 diagnostic warning for WORKER_TIMEOUT={invalid_env!r}, "
        f"found {len(warning_records)}"
    )
    assert f"value={invalid_env!r}" in warning_records[0].getMessage()


@pytest.mark.timeout(30)
@pytest.mark.parametrize("invalid_env", INVALID_TIMEOUT_ENV_VALUES)
def test_malformed_worker_timeout_env_emits_warning_without_cli_override(
    monkeypatch: pytest.MonkeyPatch,
    caplog: pytest.LogCaptureFixture,
    invalid_env: str,
) -> None:
    """Without CLI override, invalid env raises RunnerValidationError and emits warning log."""
    monkeypatch.setenv("WORKER_TIMEOUT", invalid_env)
    with caplog.at_level(logging.WARNING, logger="scripts.run_parallel_tests"):
        with pytest.raises(RunnerValidationError):
            get_worker_timeout()

    warning_records = [
        rec
        for rec in caplog.records
        if rec.levelno == logging.WARNING
        and "invalid_worker_timeout_env" in rec.getMessage()
    ]
    assert len(warning_records) == 1, (
        f"Expected 1 diagnostic warning for WORKER_TIMEOUT={invalid_env!r}, "
        f"found {len(warning_records)}"
    )
    assert f"value={invalid_env!r}" in warning_records[0].getMessage()


@pytest.mark.timeout(30)
@pytest.mark.parametrize(
    ("env_val", "expected"),
    [
        ("45.0", 45.0),
        ("none", None),
        ("NONE", None),
        (None, 30.0),
    ],
)
def test_valid_or_unset_worker_timeout_env_emits_no_warning(
    monkeypatch: pytest.MonkeyPatch,
    caplog: pytest.LogCaptureFixture,
    env_val: str | None,
    expected: float | None,
) -> None:
    """Valid or unset WORKER_TIMEOUT environment variable emits no diagnostic warnings."""
    if env_val is not None:
        monkeypatch.setenv("WORKER_TIMEOUT", env_val)
    else:
        monkeypatch.delenv("WORKER_TIMEOUT", raising=False)

    with caplog.at_level(logging.WARNING, logger="scripts.run_parallel_tests"):
        resolved = get_worker_timeout()

    assert resolved == expected
    warning_records = [
        rec
        for rec in caplog.records
        if "invalid_worker_timeout_env" in rec.getMessage()
    ]
    assert len(warning_records) == 0, (
        f"Expected no diagnostic warnings for WORKER_TIMEOUT={env_val!r}, "
        f"found {len(warning_records)}"
    )
