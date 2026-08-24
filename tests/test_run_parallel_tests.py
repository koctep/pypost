"""Integration and unit tests for parallel test runner orchestrator (PYPOST-1149)."""

from __future__ import annotations

import json
import logging
import sys
from pathlib import Path
from unittest.mock import patch

import pytest

from scripts.run_parallel_tests import (
    CLIParser,
    CoverageManager,
    JsonReporter,
    NOTICE,
    RunnerConfig,
    RunSummary,
    SubprocessTestExecutor,
    TestDiscovery,
    TestResult,
    TestStatus,
    get_worker_count,
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


def test_worker_count_precedence(monkeypatch: pytest.MonkeyPatch) -> None:
    """Worker count precedence: CLI arg > WORKERS env > PYTEST_WORKERS env > cpu_count."""
    monkeypatch.delenv("WORKERS", raising=False)
    monkeypatch.delenv("PYTEST_WORKERS", raising=False)

    # 1. Fallback to os.cpu_count() or 4
    default_workers = get_worker_count(cli_workers=None)
    assert default_workers >= 1

    # 2. PYTEST_WORKERS env var
    monkeypatch.setenv("PYTEST_WORKERS", "6")
    assert get_worker_count(cli_workers=None) == 6

    # 3. WORKERS env var takes precedence over PYTEST_WORKERS
    monkeypatch.setenv("WORKERS", "8")
    assert get_worker_count(cli_workers=None) == 8

    # 4. Explicit CLI arg takes highest precedence
    assert get_worker_count(cli_workers=2) == 2


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
    cov_mgr.prepare()
    assert (tmp_path / ".cov").is_dir()
    env = cov_mgr.get_env_for_worker(1)
    assert "COVERAGE_FILE" in env

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
    assert any("test_targets=tests" in message for message in messages)
    assert any(f"report_json={json_path}" in message for message in messages)


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
    )

    with (
        caplog.at_level(logging.WARNING),
        patch.object(
            CoverageManager,
            "combine_and_report",
            return_value=(False, "TOTAL 10%"),
        ),
    ):
        run_parallel_tests(config)

    warning_records = [
        record for record in caplog.records if record.levelno == logging.WARNING
    ]
    assert any(
        "coverage_threshold_failed" in record.getMessage()
        and "fail_under=70" in record.getMessage()
        for record in warning_records
    )
