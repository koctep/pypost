"""Integration and unit tests for parallel test runner orchestrator (PYPOST-1149)."""

from __future__ import annotations

import json
import logging
import os
import signal
import subprocess
import sys
import time
from pathlib import Path
from typing import Any
from unittest.mock import patch

import pytest

from scripts.run_parallel_tests import (
    CLIParser,
    CoverageManager,
    CoverageRequest,
    JsonReporter,
    NOTICE,
    PytestArgvLayout,
    RunnerConfig,
    RunResult,
    RunnerValidationError,
    RunSummary,
    SubprocessTestExecutor,
    TestDiscovery,
    TestResult,
    TestStatus,
    default_worker_count,
    get_worker_count,
    get_worker_timeout,
    kill_process_group,
    main,
    run_parallel_tests,
)

pytestmark = pytest.mark.timeout(60)


@pytest.fixture
def sample_test_workspace(tmp_path: Path) -> Path:
    """Create a temporary test workspace with sample test files."""
    tests_dir = tmp_path / "tests"
    tests_dir.mkdir(parents=True)

    # Passing test file 1
    (tests_dir / "test_alpha.py").write_text(
        "import pytest\n"
        "pytestmark = pytest.mark.timeout(10)\n"
        "def test_alpha_one():\n"
        "    assert 1 + 1 == 2\n"
        "def test_alpha_two():\n"
        "    assert True\n",
        encoding="utf-8",
    )

    # Passing test file 2
    (tests_dir / "test_beta.py").write_text(
        "import pytest\n"
        "pytestmark = pytest.mark.timeout(10)\n"
        "def test_beta_one():\n"
        "    assert 'hello'.upper() == 'HELLO'\n",
        encoding="utf-8",
    )

    # Helper non-test file (should not be discovered)
    (tests_dir / "helpers.py").write_text(
        "def helper_func():\n"
        "    return 42\n",
        encoding="utf-8",
    )

    return tmp_path


@pytest.fixture
def failing_test_workspace(tmp_path: Path) -> Path:
    """Create a workspace containing both passing and failing tests."""
    tests_dir = tmp_path / "tests"
    tests_dir.mkdir(parents=True)

    (tests_dir / "test_pass.py").write_text(
        "import pytest\n"
        "pytestmark = pytest.mark.timeout(10)\n"
        "def test_ok():\n"
        "    assert True\n",
        encoding="utf-8",
    )

    (tests_dir / "test_fail.py").write_text(
        "import pytest\n"
        "pytestmark = pytest.mark.timeout(10)\n"
        "def test_boom():\n"
        "    assert 1 == 2, 'Deliberate assertion failure for repro'\n",
        encoding="utf-8",
    )

    return tmp_path


def test_cli_parser_separates_runner_and_pytest_args() -> None:
    """CLIParser should extract runner flags and preserve pytest passthrough flags."""
    parser = CLIParser()
    config = parser.parse_args([
        "--workers", "4",
        "--cov",
        "--report-json", "reports/summary.json",
        "-k", "test_feature",
        "-m", "not slow",
        "-v",
        "tests/test_alpha.py",
    ])

    assert config.workers == 4
    assert config.enable_coverage is True
    assert config.report_json_path == Path("reports/summary.json")
    assert "-k" in config.pytest_args
    assert "test_feature" in config.pytest_args
    assert "-m" in config.pytest_args
    assert "not slow" in config.pytest_args
    assert "-v" in config.pytest_args
    assert "tests/test_alpha.py" in config.test_targets


def test_default_worker_count_io_tuned_policy(monkeypatch: pytest.MonkeyPatch) -> None:
    """PYPOST-1154: default oversubscribes modestly for I/O-bound subprocess pytest."""
    monkeypatch.delenv("WORKERS", raising=False)
    monkeypatch.delenv("PYTEST_WORKERS", raising=False)
    monkeypatch.setattr("os.cpu_count", lambda: 6)
    assert default_worker_count() == 8
    assert get_worker_count(cli_workers=None) == 8


def test_default_worker_count_policy_table(monkeypatch: pytest.MonkeyPatch) -> None:
    """PYPOST-1154: lock representative default worker counts."""
    cases = [(2, 4), (4, 6), (6, 8), (8, 10), (16, 16)]
    for cpu, expected in cases:
        monkeypatch.setattr("os.cpu_count", lambda c=cpu: c)
        assert default_worker_count() == expected


def test_worker_count_precedence(monkeypatch: pytest.MonkeyPatch) -> None:
    """Worker count precedence: CLI arg > WORKERS env > PYTEST_WORKERS env > default policy."""
    monkeypatch.delenv("WORKERS", raising=False)
    monkeypatch.delenv("PYTEST_WORKERS", raising=False)

    # 1. Fallback to default_worker_count()
    default_workers = get_worker_count(cli_workers=None)
    assert default_workers == default_worker_count()

    # 2. PYTEST_WORKERS env var
    monkeypatch.setenv("PYTEST_WORKERS", "6")
    assert get_worker_count(cli_workers=None) == 6

    # 3. WORKERS env var takes precedence over PYTEST_WORKERS
    monkeypatch.setenv("WORKERS", "8")
    assert get_worker_count(cli_workers=None) == 8

    # 4. Explicit CLI arg takes highest precedence
    assert get_worker_count(cli_workers=2) == 2


@pytest.mark.parametrize(
    ("cli_timeout", "env_timeout", "expected"),
    [
        (45.0, "60.0", 45.0),
        (None, "60.0", 60.0),
        (None, None, 30.0),
    ],
)
def test_get_worker_timeout_precedence(
    monkeypatch: pytest.MonkeyPatch,
    cli_timeout: float | None,
    env_timeout: str | None,
    expected: float,
) -> None:
    """Worker timeout precedence: CLI arg > WORKER_TIMEOUT env > default 30.0."""
    if env_timeout is not None:
        monkeypatch.setenv("WORKER_TIMEOUT", env_timeout)
    else:
        monkeypatch.delenv("WORKER_TIMEOUT", raising=False)
    assert get_worker_timeout(cli_timeout) == expected


@pytest.mark.parametrize("invalid_cli", [0.0, -5.0, -1.0])
@pytest.mark.parametrize("env_timeout", ["45.0", None])
def test_get_worker_timeout_rejects_invalid_cli_values(
    monkeypatch: pytest.MonkeyPatch,
    invalid_cli: float,
    env_timeout: str | None,
) -> None:
    """Invalid CLI timeout values are rejected rather than silently replaced."""
    if env_timeout is not None:
        monkeypatch.setenv("WORKER_TIMEOUT", env_timeout)
    else:
        monkeypatch.delenv("WORKER_TIMEOUT", raising=False)
    with pytest.raises(RunnerValidationError):
        get_worker_timeout(invalid_cli)


@pytest.mark.parametrize(
    "invalid_env",
    ["", "   ", "-10.0", "0", "invalid", "abc"],
)
@pytest.mark.parametrize(
    ("cli_timeout", "expected"),
    [
        (None, 30.0),
        (42.0, 42.0),
    ],
)
def test_get_worker_timeout_rejects_invalid_env_values(
    monkeypatch: pytest.MonkeyPatch,
    invalid_env: str,
    cli_timeout: float | None,
    expected: float,
) -> None:
    """Invalid environment timeout values are rejected unless CLI takes precedence."""
    monkeypatch.setenv("WORKER_TIMEOUT", invalid_env)
    if cli_timeout is None:
        with pytest.raises(RunnerValidationError):
            get_worker_timeout(cli_timeout)
    else:
        assert get_worker_timeout(cli_timeout) == expected


def test_cli_parser_worker_timeout_flags(monkeypatch: pytest.MonkeyPatch) -> None:
    """CLIParser parses --worker-timeout in space and equals formats."""
    monkeypatch.delenv("WORKER_TIMEOUT", raising=False)
    parser = CLIParser()

    # a) ["--worker-timeout", "42"] -> config.worker_timeout == 42.0
    config_space = parser.parse_args(["--worker-timeout", "42"])
    assert config_space.worker_timeout == 42.0

    # b) ["--worker-timeout=42"] -> config.worker_timeout == 42.0
    config_equals = parser.parse_args(["--worker-timeout=42"])
    assert config_equals.worker_timeout == 42.0

    with pytest.raises(RunnerValidationError):
        parser.parse_args(["--worker-timeout"])


def test_discovery_finds_all_test_files(sample_test_workspace: Path) -> None:
    """TestDiscovery finds test_*.py files and ignores non-test modules."""
    files = TestDiscovery.discover_test_files(
        repo_root=sample_test_workspace,
        targets=["tests"],
    )
    filenames = [f.name for f in files]
    assert "test_alpha.py" in filenames
    assert "test_beta.py" in filenames
    assert "helpers.py" not in filenames


def test_discovery_resolves_explicit_target_files(sample_test_workspace: Path) -> None:
    """TestDiscovery accepts specific test file targets."""
    target_file = sample_test_workspace / "tests" / "test_alpha.py"
    files = TestDiscovery.discover_test_files(
        repo_root=sample_test_workspace,
        targets=[str(target_file)],
    )
    assert len(files) == 1
    assert files[0].name == "test_alpha.py"


def test_data_models_and_classes_instantiable(tmp_path: Path) -> None:
    """Verify data structures and helper class APIs."""
    result = TestResult(
        test_file="tests/test_dummy.py",
        status=TestStatus.PASSED,
        exit_code=0,
        duration_seconds=0.1,
        stdout="ok",
        stderr="",
    )
    assert result.status == TestStatus.PASSED

    summary = RunSummary(
        total_files=1,
        passed_files=1,
        failed_files=0,
        skipped_files=0,
        total_wall_clock_seconds=0.1,
        cumulative_duration_seconds=0.1,
        worker_count=1,
        slowest_files=[("tests/test_dummy.py", 0.1)],
        results=[result],
    )
    assert summary.is_success is True

    cov_mgr = CoverageManager(repo_root=tmp_path, cov_dir=tmp_path / ".cov")
    plan = cov_mgr.prepare(request=CoverageRequest())
    assert (tmp_path / ".cov").is_dir()
    assert plan.worker_data_dir.is_dir()

    config = RunnerConfig(
        workers=1,
        enable_coverage=False,
        report_json_path=None,
        test_targets=[],
        pytest_args=[],
        repo_root=tmp_path,
        python_bin=Path(sys.executable),
    )
    executor = SubprocessTestExecutor(config)
    assert executor.config.workers == 1

    report_dict = JsonReporter.to_dict(summary)
    assert report_dict["summary"]["status"] == "passed"


def test_parallel_runner_discovers_and_runs_passing_tests(
    sample_test_workspace: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    """Parallel runner executes all passing test files and returns exit code 0."""
    config = RunnerConfig(
        workers=2,
        enable_coverage=False,
        report_json_path=None,
        test_targets=["tests"],
        pytest_args=[],
        repo_root=sample_test_workspace,
        python_bin=Path(sys.executable),
    )

    summary = run_parallel_tests(config)
    captured = capsys.readouterr()

    assert summary.is_success is True
    assert summary.total_files == 2
    assert summary.passed_files == 2
    assert summary.failed_files == 0
    assert summary.skipped_files == 0
    assert summary.total_wall_clock_seconds > 0
    assert "PASSED" in captured.out


def test_parallel_runner_captures_failure_and_exit_code(
    failing_test_workspace: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    """Parallel runner captures failures, returns non-zero exit code and failure tracebacks."""
    config = RunnerConfig(
        workers=2,
        enable_coverage=False,
        report_json_path=None,
        test_targets=["tests"],
        pytest_args=[],
        repo_root=failing_test_workspace,
        python_bin=Path(sys.executable),
    )

    summary = run_parallel_tests(config)
    captured = capsys.readouterr()

    assert summary.is_success is False
    assert summary.total_files == 2
    assert summary.passed_files == 1
    assert summary.failed_files == 1
    assert "FAILURES" in captured.out
    assert "Deliberate assertion failure for repro" in captured.out


def test_parallel_runner_forwards_pytest_filters(
    sample_test_workspace: Path,
) -> None:
    """Parallel runner handles exit code 5 (no tests collected) as SKIPPED under -k filter."""
    config = RunnerConfig(
        workers=2,
        enable_coverage=False,
        report_json_path=None,
        test_targets=["tests"],
        pytest_args=["-k", "test_alpha_one"],
        repo_root=sample_test_workspace,
        python_bin=Path(sys.executable),
    )

    summary = run_parallel_tests(config)

    assert summary.is_success is True
    assert summary.passed_files == 1
    assert summary.skipped_files == 1
    assert summary.failed_files == 0


def test_parallel_runner_emits_json_report(
    sample_test_workspace: Path,
    tmp_path: Path,
) -> None:
    """Parallel runner emits valid JSON report matching the specified schema."""
    json_path = tmp_path / "report.json"
    config = RunnerConfig(
        workers=2,
        enable_coverage=False,
        report_json_path=json_path,
        test_targets=["tests"],
        pytest_args=[],
        repo_root=sample_test_workspace,
        python_bin=Path(sys.executable),
    )

    summary = run_parallel_tests(config)
    assert summary.is_success is True
    assert json_path.is_file()

    report_data = json.loads(json_path.read_text(encoding="utf-8"))
    assert "summary" in report_data
    assert "slowest_files" in report_data
    assert "results" in report_data

    assert report_data["summary"]["total_files"] == 2
    assert report_data["summary"]["passed_files"] == 2
    assert report_data["summary"]["failed_files"] == 0
    assert report_data["summary"]["status"] == "passed"
    assert len(report_data["results"]) == 2
    assert report_data["results"][0]["status"] in ("passed", "failed", "skipped")


def test_parallel_runner_top_5_slowest_reporting(
    sample_test_workspace: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    """Parallel runner prints top slowest files table sorted descending by duration."""
    config = RunnerConfig(
        workers=2,
        enable_coverage=False,
        report_json_path=None,
        test_targets=["tests"],
        pytest_args=[],
        repo_root=sample_test_workspace,
        python_bin=Path(sys.executable),
    )

    summary = run_parallel_tests(config)
    captured = capsys.readouterr()

    assert "TOP 5 SLOWEST FILES" in captured.out
    assert len(summary.slowest_files) <= 5
    if len(summary.slowest_files) > 1:
        assert summary.slowest_files[0][1] >= summary.slowest_files[1][1]


def test_parallel_runner_injects_qt_offscreen_env(
    tmp_path: Path,
) -> None:
    """Subprocess executor injects QT_QPA_PLATFORM=offscreen into worker environments."""
    tests_dir = tmp_path / "tests"
    tests_dir.mkdir(parents=True)

    # Test file that asserts QT_QPA_PLATFORM is offscreen
    (tests_dir / "test_qt_env.py").write_text(
        "import os\n"
        "import pytest\n"
        "pytestmark = pytest.mark.timeout(10)\n"
        "def test_qt_env():\n"
        "    assert os.environ.get('QT_QPA_PLATFORM') == 'offscreen'\n",
        encoding="utf-8",
    )

    config = RunnerConfig(
        workers=1,
        enable_coverage=False,
        report_json_path=None,
        test_targets=["tests"],
        pytest_args=[],
        repo_root=tmp_path,
        python_bin=Path(sys.executable),
    )

    summary = run_parallel_tests(config)
    assert summary.is_success is True
    assert summary.passed_files == 1


def test_parallel_runner_coverage_combine(
    tmp_path: Path,
) -> None:
    """Parallel runner executes with coverage, combines data files and generates reports."""
    tests_dir = tmp_path / "tests"
    pkg_dir = tmp_path / "mypkg"
    tests_dir.mkdir(parents=True)
    pkg_dir.mkdir(parents=True)

    (pkg_dir / "__init__.py").write_text("", encoding="utf-8")
    (pkg_dir / "core.py").write_text(
        "def compute(x: int) -> int:\n"
        "    if x > 0:\n"
        "        return x * 2\n"
        "    return 0\n",
        encoding="utf-8",
    )

    (tests_dir / "test_core.py").write_text(
        "import pytest\n"
        "from mypkg.core import compute\n"
        "pytestmark = pytest.mark.timeout(10)\n"
        "def test_compute():\n"
        "    assert compute(5) == 10\n",
        encoding="utf-8",
    )

    config = RunnerConfig(
        workers=2,
        enable_coverage=True,
        report_json_path=None,
        test_targets=["tests"],
        pytest_args=["--cov=mypkg"],
        repo_root=tmp_path,
        python_bin=Path(sys.executable),
    )

    summary = run_parallel_tests(config)
    assert summary.is_success is True


def test_main_cli_entrypoint(sample_test_workspace: Path) -> None:
    """main() entrypoint parses sys.argv, executes runner, and returns exit code."""
    exit_code = main([
        "--workers", "2",
        "-m", "not slow",
        "tests",
    ], repo_root=sample_test_workspace)

    assert exit_code == 0


def test_parallel_runner_logs_run_config(
    sample_test_workspace: Path,
    caplog: pytest.LogCaptureFixture,
) -> None:
    """run_parallel_tests logs workers, targets, coverage, and JSON path at start."""
    json_path = sample_test_workspace / "reports" / "summary.json"
    config = RunnerConfig(
        workers=2,
        enable_coverage=True,
        report_json_path=json_path,
        test_targets=["tests"],
        pytest_args=["-v"],
        repo_root=sample_test_workspace,
        python_bin=Path(sys.executable),
    )

    with caplog.at_level(logging.INFO):
        run_parallel_tests(config)

    messages = [record.getMessage() for record in caplog.records]
    assert any("parallel_test_run_started" in message for message in messages)
    assert any("workers=2" in message for message in messages)
    assert any("enable_coverage=True" in message for message in messages)
    assert any("target_selection=explicit" in message for message in messages)
    assert any("target_count=1" in message for message in messages)
    assert all("test_targets=" not in message for message in messages)
    assert any(f"report_json={json_path}" in message for message in messages)
    assert any("worker_timeout=30.0" in message for message in messages)


def test_parallel_runner_logs_failure_context(
    failing_test_workspace: Path,
    caplog: pytest.LogCaptureFixture,
) -> None:
    """Failed test files emit logger.error with file, exit code, and duration context."""
    config = RunnerConfig(
        workers=2,
        enable_coverage=False,
        report_json_path=None,
        test_targets=["tests"],
        pytest_args=[],
        repo_root=failing_test_workspace,
        python_bin=Path(sys.executable),
    )

    with caplog.at_level(logging.ERROR):
        run_parallel_tests(config)

    error_records = [
        record for record in caplog.records if record.levelno == logging.ERROR
    ]
    assert error_records
    assert any("test_file_failed" in record.getMessage() for record in error_records)
    assert any(
        "file=tests/test_fail.py" in record.getMessage()
        and "exit_code=" in record.getMessage()
        and "duration_seconds=" in record.getMessage()
        for record in error_records
    )


def test_parallel_runner_logs_run_summary(
    sample_test_workspace: Path,
    caplog: pytest.LogCaptureFixture,
) -> None:
    """run_parallel_tests logs aggregate completion metrics."""
    config = RunnerConfig(
        workers=2,
        enable_coverage=False,
        report_json_path=None,
        test_targets=["tests"],
        pytest_args=[],
        repo_root=sample_test_workspace,
        python_bin=Path(sys.executable),
    )

    with caplog.at_level(logging.INFO):
        run_parallel_tests(config)

    messages = [record.getMessage() for record in caplog.records]
    lifecycle_events = (
        "parallel_test_run_started",
        "test_discovery_started",
        "test_discovery_completed",
        "test_worker_pool_started",
        "test_worker_pool_completed",
        "parallel_test_run_completed",
    )
    for event in lifecycle_events:
        assert any(event in message for message in messages)

    run_ids = {
        message.split("run_id=", 1)[1].split(" ", 1)[0]
        for message in messages
        if "run_id=" in message
    }
    assert len(run_ids) == 1
    assert any("parallel_test_run_completed" in message for message in messages)
    assert any("total_files=2" in message for message in messages)
    assert any("passed=2" in message for message in messages)


def test_parallel_runner_logs_slowest_files_at_notice_level(
    sample_test_workspace: Path,
    caplog: pytest.LogCaptureFixture,
) -> None:
    """Top slowest files are logged at the custom NOTICE level."""
    config = RunnerConfig(
        workers=2,
        enable_coverage=False,
        report_json_path=None,
        test_targets=["tests"],
        pytest_args=[],
        repo_root=sample_test_workspace,
        python_bin=Path(sys.executable),
    )

    with caplog.at_level(NOTICE):
        run_parallel_tests(config)

    notice_records = [record for record in caplog.records if record.levelno == NOTICE]
    assert notice_records
    assert any("slowest_test_file" in record.getMessage() for record in notice_records)


def test_parallel_runner_logs_coverage_threshold_warning(
    sample_test_workspace: Path,
    caplog: pytest.LogCaptureFixture,
) -> None:
    """Coverage threshold failure emits logger.warning with fail_under context."""
    config = RunnerConfig(
        workers=1,
        enable_coverage=True,
        report_json_path=None,
        test_targets=["tests"],
        pytest_args=[],
        repo_root=sample_test_workspace,
        python_bin=Path(sys.executable),
        coverage_fail_under=42,
    )

    with (
        caplog.at_level(logging.WARNING),
        patch.object(
            CoverageManager,
            "report",
            return_value=RunResult(
                kind="coverage",
                status="failed",
                target=None,
                exit_code=1,
                duration_seconds=0.0,
                message="Coverage failure: total of 10 is less than fail-under=42",
                error_code="coverage_threshold",
            ),
        ),
    ):
        run_parallel_tests(config)

    warning_records = [
        record for record in caplog.records if record.levelno == logging.WARNING
    ]
    assert any(
        "coverage_threshold_failed" in record.getMessage()
        and "fail_under=42" in record.getMessage()
        for record in warning_records
    )


def test_parallel_runner_logs_validation_context_without_error_text(
    tmp_path: Path,
    caplog: pytest.LogCaptureFixture,
) -> None:
    """Validation telemetry identifies the phase without duplicating user input or output."""
    config = RunnerConfig(
        workers=0,
        enable_coverage=False,
        report_json_path=None,
        test_targets=["tests"],
        pytest_args=[],
        repo_root=tmp_path,
        python_bin=Path(sys.executable),
    )

    with caplog.at_level(logging.INFO):
        summary = run_parallel_tests(config)

    assert summary.exit_code == 2
    validation_records = [
        record
        for record in caplog.records
        if "parallel_test_validation_failed" in record.getMessage()
    ]
    assert len(validation_records) == 1
    message = validation_records[0].getMessage()
    assert "phase=configuration" in message
    assert "code=invalid_workers" in message
    assert "worker_count=0" in message
    assert "workers must be a positive integer" not in message
    completed_records = [
        record
        for record in caplog.records
        if "parallel_test_run_completed" in record.getMessage()
    ]
    assert len(completed_records) == 1
    completed_message = completed_records[0].getMessage()
    validation_run_id = message.split("run_id=", 1)[1].split(" ", 1)[0]
    completed_run_id = completed_message.split("run_id=", 1)[1].split(" ", 1)[0]
    assert completed_run_id == validation_run_id
    assert "total_files=0" in completed_message
    assert "passed=0" in completed_message
    assert "failed=0" in completed_message
    assert "scheduled_units=0" in completed_message
    assert "coverage_status=disabled" in completed_message
    assert "outcome=failed" in completed_message
    assert "failure_phase=configuration" in completed_message
    assert "failure_code=invalid_workers" in completed_message


def test_main_logs_cli_validation_phase(
    sample_test_workspace: Path,
    caplog: pytest.LogCaptureFixture,
) -> None:
    """CLI parsing failures emit one correlated terminal event without raw arguments."""
    sensitive_target = "tests/test_alpha.py::test_secret[customer-token]"
    with caplog.at_level(logging.INFO):
        exit_code = main(
            ["--workers", "0", sensitive_target],
            repo_root=sample_test_workspace,
        )

    assert exit_code == 2
    validation_records = [
        record
        for record in caplog.records
        if "parallel_test_validation_failed" in record.getMessage()
    ]
    assert len(validation_records) == 1
    message = validation_records[0].getMessage()
    assert "phase=cli_parse" in message
    assert "code=invalid_workers" in message
    assert "positive integer" not in message
    completed_records = [
        record
        for record in caplog.records
        if "parallel_test_run_completed" in record.getMessage()
    ]
    assert len(completed_records) == 1
    completed_message = completed_records[0].getMessage()
    completed_run_id = completed_message.split("run_id=", 1)[1].split(" ", 1)[0]
    validation_run_id = message.split("run_id=", 1)[1].split(" ", 1)[0]
    assert completed_run_id == validation_run_id
    assert "total_files=0" in completed_message
    assert "passed=0" in completed_message
    assert "failed=0" in completed_message
    assert "skipped=0" in completed_message
    assert "scheduled_units=0" in completed_message
    assert "outcome=failed" in completed_message
    assert "failure_phase=cli_parse" in completed_message
    assert "failure_code=invalid_workers" in completed_message
    assert sensitive_target not in message
    assert sensitive_target not in completed_message


def test_parallel_runner_logs_coverage_lifecycle(
    sample_test_workspace: Path,
    caplog: pytest.LogCaptureFixture,
) -> None:
    """Coverage runs expose preparation, aggregation, and report outcomes as scalar events."""
    config = RunnerConfig(
        workers=1,
        enable_coverage=True,
        report_json_path=None,
        test_targets=["tests"],
        pytest_args=[],
        repo_root=sample_test_workspace,
        python_bin=Path(sys.executable),
    )

    with caplog.at_level(logging.INFO):
        summary = run_parallel_tests(config)

    assert summary.coverage_result is not None
    messages = [record.getMessage() for record in caplog.records]
    assert any("coverage_collection_prepared" in message for message in messages)
    assert any("coverage_aggregation_started" in message for message in messages)
    assert any("coverage_aggregation_completed" in message for message in messages)
    assert any("coverage_report_started" in message for message in messages)
    assert any("coverage_report_completed" in message for message in messages)
    assert all("stdout=" not in message and "stderr=" not in message for message in messages)


def test_coverage_aggregation_failure_is_structured(
    tmp_path: Path,
    caplog: pytest.LogCaptureFixture,
) -> None:
    """Missing coverage fragments identify aggregation failure without report payloads."""
    manager = CoverageManager(
        repo_root=tmp_path,
        cov_dir=tmp_path / ".coverage_parallel",
        python_bin=Path(sys.executable),
        run_id="coverage-test",
    )
    plan = manager.prepare(request=CoverageRequest())

    with caplog.at_level(logging.ERROR):
        result = manager.combine(plan=plan)

    assert result.error_code == "coverage_no_data"
    messages = [record.getMessage() for record in caplog.records]
    assert any(
        "coverage_aggregation_failed" in message
        and "reason=no_data" in message
        and "data_file_count=0" in message
        and "run_id=coverage-test" in message
        for message in messages
    )


@pytest.mark.timeout(10)
def test_hung_worker_under_timeout_yields_timed_out(
    tmp_path: Path,
    caplog: pytest.LogCaptureFixture,
) -> None:
    """Hung worker under short worker_timeout yields TIMED_OUT and failed run.

    Mocks ``subprocess.Popen`` communicate raising ``TimeoutExpired`` so the suite stays
    bounded while asserting status, structured ``worker_timeout`` log, and
    non-success summary.
    """
    tests_dir = tmp_path / "tests"
    tests_dir.mkdir(parents=True)
    (tests_dir / "test_hang.py").write_text(
        "import pytest\n"
        "import time\n"
        "pytestmark = pytest.mark.timeout(10)\n"
        "def test_never_finishes():\n"
        "    time.sleep(120)\n",
        encoding="utf-8",
    )

    config = RunnerConfig(
        workers=1,
        enable_coverage=False,
        report_json_path=None,
        test_targets=["tests/test_hang.py"],
        pytest_args=[],
        repo_root=tmp_path,
        python_bin=Path(sys.executable),
        worker_timeout=1.0,
    )

    class FakePopen:
        def __init__(self, *args: Any, **kwargs: Any) -> None:
            self.pid = 99999
            self.returncode = -9

        def communicate(self, *args: Any, **kwargs: Any) -> tuple[str, str]:
            if kwargs.get("timeout") is not None:
                raise subprocess.TimeoutExpired(cmd=["test"], timeout=float(kwargs["timeout"]))
            return ("", "")

        def kill(self) -> None:
            pass

    with (
        caplog.at_level(logging.WARNING),
        patch(
            "scripts.run_parallel_tests.subprocess.Popen",
            side_effect=FakePopen,
        ),
        patch(
            "scripts.run_parallel_tests.kill_process_group",
        ) as mock_kill_pg,
    ):
        summary = run_parallel_tests(config)

    assert mock_kill_pg.called
    assert mock_kill_pg.call_args.kwargs["run_id"]
    assert summary.is_success is False
    assert any(r.status == TestStatus.TIMED_OUT for r in summary.results)
    timeout_records = [
        record for record in caplog.records if "worker_timeout" in record.getMessage()
    ]
    assert timeout_records
    timeout_message = timeout_records[0].getMessage()
    assert "timeout_seconds=" in timeout_message
    assert "duration_seconds=" in timeout_message
    assert "exit_code=-9" in timeout_message
    assert "run_id=" in timeout_message


@pytest.mark.timeout(15)
def test_worker_timeout_terminates_grandchild_process_group(tmp_path: Path) -> None:
    """A worker timeout must terminate grandchild processes spawned in its group."""
    tests_dir = tmp_path / "tests"
    tests_dir.mkdir(parents=True)
    pid_file = tmp_path / "grandchild.pid"

    test_file = tests_dir / "test_hang_with_grandchild.py"
    test_file.write_text(
        "import subprocess\n"
        "import sys\n"
        "import time\n"
        "from pathlib import Path\n"
        "\n"
        "def test_hang():\n"
        f"    pid_file = Path({str(pid_file)!r})\n"
        "    proc = subprocess.Popen([sys.executable, '-c', 'import time; time.sleep(30)'])\n"
        "    pid_file.write_text(str(proc.pid), encoding='utf-8')\n"
        "    time.sleep(30)\n",
        encoding="utf-8",
    )

    config = CLIParser().parse_args(
        [
            "--workers=1",
            "--worker-timeout=1",
            "-o",
            "addopts=",
            str(test_file),
        ],
        repo_root=tmp_path,
    )
    executor = SubprocessTestExecutor(config)
    layout = PytestArgvLayout.from_project(
        tmp_path, config.original_argv, config.runner_spans
    )
    discovery = TestDiscovery().discover(
        repo_root=tmp_path, target_records=config.target_records
    )
    assert not discovery.errors
    assert len(discovery.units) == 1

    grandchild_pid: int | None = None
    try:
        result = executor.run_dispatch_unit(
            unit=discovery.units[0],
            layout=layout,
            all_target_records=discovery.records,
            index=1,
            total=1,
            coverage_plan=None,
        )
        assert result.status == "timed_out"

        assert pid_file.exists(), (
            f"Grandchild PID file was not created; stdout={result.stdout} stderr={result.stderr}"
        )
        grandchild_pid = int(pid_file.read_text(encoding="utf-8").strip())

        # Desired behavior: grandchild process must be terminated upon worker timeout.
        deadline = time.perf_counter() + 1.0
        is_alive = True
        while time.perf_counter() < deadline:
            try:
                os.kill(grandchild_pid, 0)
                time.sleep(0.05)
            except (ProcessLookupError, OSError):
                is_alive = False
                break

        assert not is_alive, (
            f"Grandchild process {grandchild_pid} is still alive after worker timeout"
        )
    finally:
        if grandchild_pid is not None:
            try:
                os.kill(grandchild_pid, signal.SIGKILL)
            except (ProcessLookupError, OSError):
                pass


@pytest.mark.timeout(10)
def test_kill_process_group_posix() -> None:
    """kill_process_group calls os.killpg with SIGKILL on POSIX."""
    with (
        patch("sys.platform", "linux"),
        patch("os.getpgid", return_value=1234),
        patch("os.killpg") as mock_killpg,
    ):
        kill_process_group(1234, run_id="timeout-run")
        mock_killpg.assert_called_once_with(1234, signal.SIGKILL)


@pytest.mark.timeout(10)
def test_kill_process_group_posix_fallback_on_lookup_error() -> None:
    """kill_process_group uses pid directly if os.getpgid fails."""
    with (
        patch("sys.platform", "linux"),
        patch("os.getpgid", side_effect=ProcessLookupError),
        patch("os.killpg") as mock_killpg,
    ):
        kill_process_group(4321)
        mock_killpg.assert_called_once_with(4321, signal.SIGKILL)


@pytest.mark.timeout(10)
def test_kill_process_group_posix_suppresses_exceptions(
    caplog: pytest.LogCaptureFixture,
) -> None:
    """kill_process_group safely suppresses killpg errors and logs at debug level."""
    with (
        caplog.at_level(logging.DEBUG),
        patch("sys.platform", "linux"),
        patch("os.getpgid", return_value=1234),
        patch("os.killpg", side_effect=ProcessLookupError("No such process")),
    ):
        kill_process_group(1234, run_id="timeout-run")

    debug_records = [
        record for record in caplog.records if record.levelno == logging.DEBUG
    ]
    assert any(
        "kill_process_group killpg failed" in record.getMessage()
        for record in debug_records
    )
    assert all("run_id=timeout-run" in record.getMessage() for record in debug_records)


@pytest.mark.timeout(10)
def test_kill_process_group_win32() -> None:
    """kill_process_group calls os.kill with SIGTERM on Windows."""
    with (
        patch("sys.platform", "win32"),
        patch("os.kill") as mock_kill,
    ):
        kill_process_group(5678)
        mock_kill.assert_called_once_with(5678, signal.SIGTERM)
