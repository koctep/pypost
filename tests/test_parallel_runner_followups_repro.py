"""Red contract tests for the PYPOST-1153 parallel-runner follow-ups."""

from __future__ import annotations

import logging
import subprocess
import sys
from pathlib import Path
from typing import Any
from unittest.mock import patch

import pytest

import scripts.run_parallel_tests as runner
from tests.makefile_contract_helpers import makefile_target_recipe_body

pytestmark = pytest.mark.timeout(120)

REPO_ROOT = Path(__file__).resolve().parents[1]


def _required(name: str) -> Any:
    """Resolve an accepted architecture symbol so the old runner fails clearly."""
    return getattr(runner, name)


def _parse(args: list[str], repo_root: Path) -> Any:
    """Parse arguments through the public runner boundary."""
    return runner.CLIParser().parse_args(args, repo_root=repo_root)


def _coverage_manager(repo_root: Path) -> Any:
    """Construct the coverage manager while exercising its accepted API."""
    manager_type = _required("CoverageManager")
    try:
        return manager_type(
            repo_root=repo_root,
            cov_dir=repo_root / ".coverage_parallel",
            python_bin=Path(sys.executable),
        )
    except TypeError:
        return manager_type()


def _coverage_plan(
    repo_root: Path,
    *,
    sources: tuple[str, ...] | None = None,
    fail_under: int | None = None,
    reports: tuple[str, ...] = (),
) -> Any:
    """Prepare a plan through the architecture's request/plan boundary."""
    if not (repo_root / "pyproject.toml").exists():
        (repo_root / "pyproject.toml").write_text(
            "[tool.coverage.run]\nsource = ['pypost']\n\n"
            "[tool.coverage.report]\nfail_under = 70\n",
            encoding="utf-8",
        )
    request_type = _required("CoverageRequest")
    request = request_type(
        source_override=sources,
        fail_under_override=fail_under,
        report_specs=reports,
    )
    manager = _coverage_manager(repo_root)
    return manager.prepare(
        repo_root=repo_root,
        python_bin=Path(sys.executable),
        request=request,
    )


def _layout_and_unit(config: Any, repo_root: Path) -> tuple[Any, Any]:
    """Resolve one future dispatch unit without using a path-only worker API."""
    layout_type = _required("PytestArgvLayout")
    layout = layout_type.from_project(
        repo_root,
        config.original_argv,
        config.runner_spans,
    )
    discovery = _required("TestDiscovery")()
    discovered = discovery.discover(
        repo_root=repo_root,
        target_records=config.target_records,
    )
    assert not discovered.errors
    assert len(discovered.units) == 1
    return layout, discovered.units[0]


def _write_passing_test(workspace: Path) -> None:
    """Create one valid target so invalid values cannot hide behind empty discovery."""
    tests_dir = workspace / "tests"
    tests_dir.mkdir()
    (tests_dir / "test_ok.py").write_text(
        "import pytest\n"
        "pytestmark = pytest.mark.timeout(10)\n"
        "def test_ok():\n"
        "    assert True\n",
        encoding="utf-8",
    )


def _write_coverage_workspace(workspace: Path, *, cover_all: bool) -> None:
    """Create a deterministic package with either adequate or inadequate coverage."""
    package = workspace / "sample_pkg"
    tests_dir = workspace / "tests"
    package.mkdir()
    tests_dir.mkdir()
    (package / "__init__.py").write_text("", encoding="utf-8")
    (package / "values.py").write_text(
        "def first():\n    return 1\n\n"
        "def second():\n    return 2\n\n"
        "def third():\n    return 3\n\n"
        "def fourth():\n    return 4\n",
        encoding="utf-8",
    )
    calls = "first(), second(), third(), fourth()" if cover_all else "first(),"
    expected = "(1, 2, 3, 4)" if cover_all else "(1,)"
    imports = "first, second, third, fourth" if cover_all else "first"
    (tests_dir / "test_values.py").write_text(
        "import pytest\n"
        f"from sample_pkg.values import {imports}\n"
        "pytestmark = pytest.mark.timeout(10)\n"
        "def test_values():\n"
        f"    assert ({calls}) == {expected}\n",
        encoding="utf-8",
    )
    (workspace / "pyproject.toml").write_text(
        "[tool.coverage.run]\nsource = ['sample_pkg']\n\n"
        "[tool.coverage.report]\nfail_under = 95\n",
        encoding="utf-8",
    )


def _set_coverage_threshold(workspace: Path, threshold: int) -> None:
    """Change only the project coverage policy in a fixture workspace."""
    config_path = workspace / "pyproject.toml"
    config = config_path.read_text(encoding="utf-8")
    config_path.write_text(
        "\n".join(
            f"fail_under = {threshold}" if line.startswith("fail_under =") else line
            for line in config.splitlines()
        )
        + "\n",
        encoding="utf-8",
    )


def _seed_make_workspace(workspace: Path, *, with_runner: bool) -> None:
    """Make the repository recipes runnable without installing a second environment."""
    (workspace / "Makefile").write_text(
        (REPO_ROOT / "Makefile").read_text(encoding="utf-8"),
        encoding="utf-8",
    )
    (workspace / "pyproject.toml").write_text(
        "[project]\nname = 'make-contract-fixture'\nversion = '0.0.0'\n",
        encoding="utf-8",
    )
    venv = workspace / ".venv"
    (venv / "bin").mkdir(parents=True)
    (venv / "bin" / "python").symlink_to(Path(sys.executable))
    version = f"{sys.version_info.major}.{sys.version_info.minor}"
    for stamp in (
        venv / f".initialized-{version}",
        venv / f".venv-test-{version}",
        venv / f".venv-otel-{version}",
    ):
        stamp.touch()
    if with_runner:
        scripts = workspace / "scripts"
        scripts.mkdir()
        (scripts / "run_parallel_tests.py").write_text(
            "import sys\n"
            "print('runner argv:', sys.argv[1:])\n"
            "raise SystemExit(3)\n",
            encoding="utf-8",
        )


def test_parser_replays_ordered_pytest_tokens_and_node_ids() -> None:
    """Remove runner options without moving or dropping pytest tokens."""
    args = [
        "--workers",
        "2",
        "-k",
        "selected",
        "tests/test_nodes.py::test_first",
        "--",
        "--workers",
        "tests/test_nodes.py::test_second",
    ]

    config = _parse(args, REPO_ROOT)

    assert tuple(config.original_argv) == tuple(args)
    assert tuple(config.pytest_argv) == (
        "-k",
        "selected",
        "tests/test_nodes.py::test_first",
        "--",
        "--workers",
        "tests/test_nodes.py::test_second",
    )
    assert config.pytest_argv[3] == "--"
    assert config.pytest_argv[4:] == [
        "--workers",
        "tests/test_nodes.py::test_second",
    ]
    assert config.runner_spans
    assert config.runner_spans[0].start == 0
    assert config.runner_spans[0].end == 2


def test_node_id_targets_group_into_one_dispatch_unit(tmp_path: Path) -> None:
    """Multiple node ids for one file run in one selected dispatch unit."""
    tests_dir = tmp_path / "tests"
    tests_dir.mkdir()
    (tests_dir / "test_nodes.py").write_text(
        "import pytest\n"
        "pytestmark = pytest.mark.timeout(10)\n"
        "def test_first():\n    assert True\n"
        "def test_second():\n    assert True\n"
        "def test_unselected():\n"
        "    assert False, 'the node-id selection was lost'\n",
        encoding="utf-8",
    )

    config = _parse(
        [
            "tests/test_nodes.py::test_first",
            "tests/test_nodes.py::test_second",
        ],
        tmp_path,
    )
    summary = runner.run_parallel_tests(config)

    assert summary.scheduled_units == 1
    assert summary.exit_code == 0
    assert summary.is_success
    test_results = [result for result in summary.results if result.kind == "test"]
    assert len(test_results) == 1
    assert test_results[0].status == "passed"


@pytest.mark.parametrize("target", ["tests/does-not-exist.py", "tests/no_match_*.py"])
def test_missing_explicit_target_is_actionable_validation_failure(
    tmp_path: Path,
    target: str,
    caplog: pytest.LogCaptureFixture,
) -> None:
    """An unresolved target fails before a worker is scheduled."""
    config = _parse([target], tmp_path)

    with (
        caplog.at_level(logging.INFO, logger=runner.__name__),
        patch.object(runner.concurrent.futures, "ThreadPoolExecutor") as pool,
    ):
        summary = runner.run_parallel_tests(config)

    pool.assert_not_called()
    assert summary.scheduled_units == 0
    assert summary.exit_code == 2
    assert not summary.is_success
    assert len(summary.results) == 1
    result = summary.results[0]
    assert result.kind == "validation"
    assert result.status == "invalid"
    assert result.exit_code == 2
    assert result.error_code
    assert target in result.message
    assert "target" in result.message.lower() or "file" in result.message.lower()
    completed = [
        record.getMessage()
        for record in caplog.records
        if "parallel_test_run_completed" in record.getMessage()
    ]
    validation = [
        record.getMessage()
        for record in caplog.records
        if "parallel_test_validation_failed" in record.getMessage()
    ]
    assert len(validation) == 1
    assert len(completed) == 1
    validation_run_id = validation[0].split("run_id=", 1)[1].split(" ", 1)[0]
    completed_run_id = completed[0].split("run_id=", 1)[1].split(" ", 1)[0]
    assert completed_run_id == validation_run_id
    assert "total_files=0" in completed[0]
    assert "scheduled_units=0" in completed[0]
    assert "outcome=failed" in completed[0]
    assert "failure_phase=discovery" in completed[0]
    assert "failure_code=" in completed[0]


def test_coverage_prepare_rejection_emits_correlated_terminal_event(
    tmp_path: Path,
    caplog: pytest.LogCaptureFixture,
) -> None:
    """Coverage configuration rejection emits one correlated zero-work completion event."""
    _write_passing_test(tmp_path)
    (tmp_path / "pyproject.toml").write_text(
        "[tool.coverage.report]\nfail_under = 'not-an-integer'\n",
        encoding="utf-8",
    )
    config = _parse(["--cov=sample_pkg", "tests/test_ok.py"], tmp_path)

    with caplog.at_level(logging.INFO, logger=runner.__name__):
        summary = runner.run_parallel_tests(config)

    assert summary.exit_code == 2
    assert summary.total_files == 0
    assert summary.scheduled_units == 0
    validation = [
        record.getMessage()
        for record in caplog.records
        if "parallel_test_validation_failed" in record.getMessage()
    ]
    completed = [
        record.getMessage()
        for record in caplog.records
        if "parallel_test_run_completed" in record.getMessage()
    ]
    assert len(validation) == 1
    assert len(completed) == 1
    validation_run_id = validation[0].split("run_id=", 1)[1].split(" ", 1)[0]
    completed_run_id = completed[0].split("run_id=", 1)[1].split(" ", 1)[0]
    assert completed_run_id == validation_run_id
    assert "phase=coverage_prepare" in validation[0]
    assert "code=invalid_coverage_config" in validation[0]
    assert "total_files=0" in completed[0]
    assert "scheduled_units=0" in completed[0]
    assert "outcome=failed" in completed[0]
    assert "failure_phase=coverage_prepare" in completed[0]
    assert "failure_code=invalid_coverage_config" in completed[0]


def test_coverage_prepare_cleans_root_fragments(tmp_path: Path) -> None:
    """Coverage setup removes stale fragments that could pollute a Make validation run."""
    (tmp_path / "pyproject.toml").write_text(
        "[tool.coverage.run]\nsource = ['sample_pkg']\n",
        encoding="utf-8",
    )
    for name in (".coverage.worker-a", ".coverage.worker-b"):
        (tmp_path / name).write_text("stale", encoding="utf-8")

    manager = _coverage_manager(tmp_path)
    manager.prepare(request=_required("CoverageRequest")())

    assert not list(tmp_path.glob(".coverage.*"))


def test_empty_default_discovery_is_not_a_success(tmp_path: Path) -> None:
    """A zero-file selection is represented as an invalid result, not green."""
    config = _parse([], tmp_path)
    summary = runner.run_parallel_tests(config)

    assert summary.scheduled_units == 0
    assert summary.exit_code == 2
    assert not summary.is_success
    assert summary.results[0].kind == "validation"
    assert summary.results[0].status == "invalid"
    assert summary.results[0].message


@pytest.mark.parametrize("workers", ["0", "-1", "not-an-integer"])
def test_invalid_worker_cli_value_fails_without_work(
    tmp_path: Path,
    workers: str,
    capsys: pytest.CaptureFixture[str],
) -> None:
    """Invalid worker input returns 2 with guidance and never runs tests."""
    _write_passing_test(tmp_path)
    with patch.object(runner, "run_parallel_tests") as run:
        assert runner.main(
            ["--workers", workers, "tests/test_ok.py"],
            repo_root=tmp_path,
        ) == 2

    run.assert_not_called()
    diagnostics = capsys.readouterr().err.lower()
    assert "workers" in diagnostics
    assert workers.lower() in diagnostics
    assert "positive" in diagnostics or "greater" in diagnostics


def test_invalid_worker_environment_value_fails_without_work(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    """Invalid WORKERS input cannot fall back to a computed default."""
    _write_passing_test(tmp_path)
    monkeypatch.setenv("WORKERS", "not-an-integer")
    with patch.object(runner, "run_parallel_tests") as run:
        assert runner.main(["tests/test_ok.py"], repo_root=tmp_path) == 2

    run.assert_not_called()
    diagnostics = capsys.readouterr().err.lower()
    assert "workers" in diagnostics
    assert "not-an-integer" in diagnostics


@pytest.mark.parametrize("timeout", ["0", "-1", "NaN", "inf"])
def test_invalid_timeout_value_fails_without_work(
    tmp_path: Path,
    timeout: str,
    capsys: pytest.CaptureFixture[str],
) -> None:
    """Invalid timeout values fail early with actionable diagnostics."""
    _write_passing_test(tmp_path)
    with patch.object(runner, "run_parallel_tests") as run:
        assert runner.main(
            ["--worker-timeout", timeout, "tests/test_ok.py"],
            repo_root=tmp_path,
        ) == 2

    run.assert_not_called()
    diagnostics = capsys.readouterr().err.lower()
    assert "timeout" in diagnostics
    assert timeout.lower() in diagnostics
    assert "positive" in diagnostics or "finite" in diagnostics


def test_none_timeout_is_an_explicit_unbounded_mode() -> None:
    """The direct runner accepts ``none`` as deliberate no-timeout mode."""
    config = _parse(["--worker-timeout=none"], REPO_ROOT)
    assert config.worker_timeout is None


def _run_missing_runner_make(workspace: Path, target: str) -> subprocess.CompletedProcess[str]:
    """Execute the actual recipe branch with its runner script absent."""
    _seed_make_workspace(workspace, with_runner=False)
    return subprocess.run(
        ["make", "-s", target, "WORKERS=1"],
        cwd=workspace,
        capture_output=True,
        text=True,
        timeout=30,
    )


def test_make_recipes_select_runner_and_forward_contract_values() -> None:
    """Both standard recipes expose the worker, timeout, and pytest contracts."""
    makefile = (REPO_ROOT / "Makefile").read_text(encoding="utf-8")

    for target in ("test", "test-cov"):
        recipe = makefile_target_recipe_body(makefile, target)
        assert "scripts/run_parallel_tests.py" in recipe
        assert "--workers $(WORKERS)" in recipe
        assert "--worker-timeout $(WORKER_TIMEOUT)" in recipe
        assert "PYTEST_ARGS" in recipe
        assert "parallel runner unavailable" in recipe
        assert "python -m pytest" not in recipe


@pytest.mark.parametrize("target", ["test", "test-cov"])
def test_make_parallel_targets_fail_closed_without_runner(
    tmp_path: Path,
    target: str,
) -> None:
    """Missing runner scripts fail closed rather than invoking serial pytest."""
    result = _run_missing_runner_make(tmp_path, target)
    output = f"{result.stdout}\n{result.stderr}"

    assert result.returncode != 0
    assert "parallel runner unavailable" in output.lower()
    assert "python -m pytest" not in output


def test_make_test_cov_enables_coverage_and_propagates_failure(tmp_path: Path) -> None:
    """The coverage recipe selects the runner, enables coverage, and propagates failure."""
    _seed_make_workspace(tmp_path, with_runner=True)
    result = subprocess.run(
        [
            "make",
            "-s",
            "test-cov",
            "WORKERS=2",
            "WORKER_TIMEOUT=1",
            "PYTEST_ARGS=tests/test_ok.py",
        ],
        cwd=tmp_path,
        capture_output=True,
        text=True,
        timeout=30,
    )
    output = f"{result.stdout}\n{result.stderr}"

    assert result.returncode != 0
    assert "--cov" in output
    assert "'--workers', '2'" in output
    assert "'--worker-timeout', '1'" in output
    assert "tests/test_ok.py" in output
    assert "python -m pytest" not in output


def test_ci_summary_reads_coverage_policy_from_runner() -> None:
    """The CI summary must use the runner's configured threshold, not a duplicate literal."""
    workflow = (REPO_ROOT / ".github" / "workflows" / "test.yml").read_text(
        encoding="utf-8"
    )

    assert "THRESHOLD=70" not in workflow
    assert "CoverageManager" in workflow
    assert "_read_project_policy" in workflow
    assert "fail_under" in workflow


def test_coverage_flags_precede_sentinel_and_preserve_post_sentinel_tokens(
    tmp_path: Path,
) -> None:
    """Coverage flags are inserted before ``--`` without reordering its postlude."""
    _write_passing_test(tmp_path)
    config = _parse(
        [
            "--cov=sample_pkg",
            "-k",
            "test_ok",
            "--",
            "tests/test_ok.py",
        ],
        tmp_path,
    )
    layout = runner.PytestArgvLayout.from_project(
        tmp_path, config.original_argv, config.runner_spans
    )
    discovery = runner.TestDiscovery().discover(
        repo_root=tmp_path,
        target_records=config.target_records,
    )
    assert not discovery.errors
    plan = _coverage_plan(tmp_path, sources=("sample_pkg",))
    executor = runner.SubprocessTestExecutor(config)

    class _CompletedProcess:
        pid = 123
        returncode = 0

        def communicate(self, timeout: float | None) -> tuple[str, str]:
            return "", ""

    with patch(
        "scripts.run_parallel_tests.subprocess.Popen",
        return_value=_CompletedProcess(),
    ) as popen:
        executor.run_dispatch_unit(
            unit=discovery.units[0],
            layout=layout,
            all_target_records=config.target_records,
            index=1,
            total=1,
            coverage_plan=plan,
        )

    command = popen.call_args.args[0]
    sentinel = command.index("--")
    assert command[sentinel - 2 : sentinel] == ["--cov=sample_pkg", "--cov-report="]
    assert command[sentinel + 1 :] == ["tests/test_ok.py"]


def test_coverage_sentinel_target_executes_successfully(tmp_path: Path) -> None:
    """A coverage run keeps a post-sentinel target executable by the child pytest."""
    _write_coverage_workspace(tmp_path, cover_all=True)
    config = _parse(
        ["--cov=sample_pkg", "-k", "test_values", "--", "tests/test_values.py"],
        tmp_path,
    )

    summary = runner.run_parallel_tests(config)

    assert summary.exit_code == 0
    assert summary.is_success
    assert summary.results[0].status == "passed"
    assert summary.coverage_result is not None
    assert summary.coverage_result.status == "passed"


def test_unknown_option_with_target_like_value_fails_closed(tmp_path: Path) -> None:
    """An unknown option cannot silently turn an explicit target into its value."""
    _write_passing_test(tmp_path)

    with pytest.raises(runner.RunnerValidationError) as raised:
        _parse(["--plugin-option", "tests/test_ok.py"], tmp_path)

    assert raised.value.code == "ambiguous_passthrough"
    assert "tests/test_ok.py" in raised.value.message
    assert "--plugin-option" in raised.value.message


def test_attached_short_option_value_does_not_consume_following_target(
    tmp_path: Path,
) -> None:
    """Attached ``-k`` values leave the next explicit target available for discovery."""
    _write_passing_test(tmp_path)
    config = _parse(["-ktest_ok", "tests/test_ok.py"], tmp_path)

    assert config.pytest_args == ["-ktest_ok"]
    assert config.test_targets == ["tests/test_ok.py"]
    assert [record.raw_target for record in config.target_records] == ["tests/test_ok.py"]


def test_coverage_preserves_project_pytest_addopts(tmp_path: Path) -> None:
    """Intermediate coverage suppression does not disable project pytest filters."""
    _write_coverage_workspace(tmp_path, cover_all=True)
    (tmp_path / "pyproject.toml").write_text(
        "[tool.pytest.ini_options]\n"
        "addopts = ['-m', 'selected']\n"
        "markers = ['selected: coverage fixture selection']\n\n"
        "[tool.coverage.run]\nsource = ['sample_pkg']\n\n"
        "[tool.coverage.report]\nfail_under = 95\n",
        encoding="utf-8",
    )
    (tmp_path / "tests" / "test_values.py").write_text(
        "import pytest\n"
        "from sample_pkg.values import first, second, third, fourth\n\n"
        "@pytest.mark.selected\n"
        "def test_selected():\n"
        "    assert (first(), second(), third(), fourth()) == (1, 2, 3, 4)\n\n"
        "def test_unselected_would_fail():\n"
        "    assert False, 'project addopts filter was disabled'\n",
        encoding="utf-8",
    )
    config = _parse(["--cov=sample_pkg", "tests/test_values.py"], tmp_path)

    summary = runner.run_parallel_tests(config)

    assert summary.exit_code == 0
    assert summary.is_success
    assert summary.results[0].status == "passed"


def test_coverage_options_are_runner_owned_and_ordered() -> None:
    """Sources, reports, and thresholds are ordered aggregate metadata."""
    config = _parse(
        [
            "--cov=first_package",
            "--cov=second_package",
            "--cov-report",
            "term-missing",
            "--cov-report=html:reports/html",
            "--cov-fail-under",
            "88",
            "tests",
        ],
        REPO_ROOT,
    )

    assert tuple(config.coverage_sources) == ("first_package", "second_package")
    assert tuple(config.coverage_reports) == (
        "term-missing",
        "html:reports/html",
    )
    assert config.coverage_fail_under == 88
    assert config.pytest_args == []


def test_coverage_manager_does_not_expose_dead_worker_environment_api() -> None:
    """Worker environment creation belongs to the executor, not the manager."""
    assert not hasattr(_required("CoverageManager"), "get_env_for_worker")


def test_missing_coverage_fragments_are_an_aggregate_failure(tmp_path: Path) -> None:
    """Missing fragments produce a failed aggregate RunResult."""
    manager = _coverage_manager(tmp_path)
    plan = _coverage_plan(tmp_path)
    result = manager.combine(plan=plan)

    assert result.kind == "coverage"
    assert result.status == "failed"
    assert result.exit_code != 0
    assert result.message


def test_dispatch_plan_suppresses_worker_threshold_and_preserves_source(
    tmp_path: Path,
) -> None:
    """Dispatch uses plan metadata and never enforces aggregate policy in a worker."""
    _write_passing_test(tmp_path)
    config = _parse(
        ["--cov=sample_pkg", "tests/test_ok.py"],
        tmp_path,
    )
    layout, unit = _layout_and_unit(config, tmp_path)
    plan = _coverage_plan(
        tmp_path,
        sources=("sample_pkg",),
        fail_under=95,
    )
    executor = runner.SubprocessTestExecutor(config)

    class _CompletedProcess:
        pid = 123
        returncode = 0

        def communicate(self, timeout: float | None) -> tuple[str, str]:
            assert timeout == config.worker_timeout
            return "", ""

    with patch(
        "scripts.run_parallel_tests.subprocess.Popen",
        return_value=_CompletedProcess(),
    ) as popen:
        executor.run_dispatch_unit(
            unit=unit,
            layout=layout,
            all_target_records=config.target_records,
            index=1,
            total=1,
            coverage_plan=plan,
        )

    command = popen.call_args.args[0]
    assert "--cov=sample_pkg" in command
    assert "--cov-report=" in command
    assert "addopts=" not in command
    assert not any(arg.startswith("--cov-fail-under") for arg in command)


def test_coverage_source_override_and_explicit_threshold_are_in_plan(
    tmp_path: Path,
) -> None:
    """A cov source and threshold override reach aggregate configuration together."""
    plan = _coverage_plan(
        tmp_path,
        sources=("alternate_pkg",),
        fail_under=42,
        reports=("term-missing", "html:reports/html", "xml:reports/coverage.xml"),
    )

    assert plan.sources == ("alternate_pkg",)
    assert plan.fail_under == 42
    assert plan.report_specs == (
        "term-missing",
        "html:reports/html",
        "xml:reports/coverage.xml",
    )
    assert plan.aggregate_rcfile is not None
    rcfile_text = plan.aggregate_rcfile.read_text(encoding="utf-8")
    assert "alternate_pkg" in rcfile_text


@pytest.mark.parametrize(
    ("reports", "show_missing"),
    [
        (("term",), False),
        (("term-missing",), True),
        (("term-m",), True),
        (("html:reports/html",), False),
        (("xml:reports/coverage.xml",), False),
        (("term-missing", "html:reports/html", "xml:reports/coverage.xml"), True),
    ],
)
def test_coverage_report_mode_controls_missing_lines(
    tmp_path: Path,
    reports: tuple[str, ...],
    show_missing: bool,
) -> None:
    """Only missing-line terminal modes add ``coverage report -m``."""
    manager = _coverage_manager(tmp_path)
    plan = _coverage_plan(
        tmp_path,
        fail_under=42,
        reports=reports,
    )

    class _CompletedProcess:
        returncode = 0
        stdout = "coverage report ok"
        stderr = ""

    with patch(
        "scripts.run_parallel_tests.subprocess.run",
        return_value=_CompletedProcess(),
    ) as run:
        result = manager.report(plan=plan)

    assert result.kind == "coverage"
    assert result.status == "passed"
    commands = [call.args[0] for call in run.call_args_list]
    report_commands = [
        command for command in commands if command[2:4] == ["coverage", "report"]
    ]
    assert len(report_commands) == 1
    report_command = report_commands[0]
    assert ("-m" in report_command[4:]) is show_missing
    assert "--fail-under=42" in report_command
    if "html:reports/html" in reports:
        assert any("html" in command and "reports/html" in command for command in commands)
    if "xml:reports/coverage.xml" in reports:
        assert any(
            "xml" in command and "reports/coverage.xml" in command
            for command in commands
        )


def test_run_start_log_redacts_parameterized_target_values(
    tmp_path: Path,
    caplog: pytest.LogCaptureFixture,
) -> None:
    """Startup telemetry contains target counts, never node IDs or parameter values."""
    _write_passing_test(tmp_path)
    secret_value = "secret-token-value"
    config = _parse([f"tests/test_ok.py::test_ok[{secret_value}]"], tmp_path)

    with caplog.at_level(logging.INFO, logger=runner.__name__):
        runner.run_parallel_tests(config)

    messages = [record.getMessage() for record in caplog.records]
    started = next(message for message in messages if "parallel_test_run_started" in message)
    assert "target_selection=explicit" in started
    assert "target_count=1" in started
    assert "test_targets=" not in started
    assert secret_value not in "\n".join(messages)


@pytest.mark.parametrize(
    ("stdout", "stderr", "expected_code"),
    [
        (
            "Coverage failure: total of 88 is less than fail-under=95",
            "",
            "coverage_threshold",
        ),
        (
            "",
            "Couldn't read 'pyproject.toml' as a config file",
            "coverage_configuration",
        ),
        ("", "failed to generate coverage report", "coverage_report"),
    ],
)
def test_coverage_report_classifies_failure_output(
    tmp_path: Path,
    stdout: str,
    stderr: str,
    expected_code: str,
) -> None:
    """Report results distinguish explicit threshold shortfalls from other failures."""
    manager = _coverage_manager(tmp_path)
    plan = _coverage_plan(tmp_path, fail_under=95)

    class _CompletedProcess:
        returncode = 1

        def __init__(self) -> None:
            self.stdout = stdout
            self.stderr = stderr

    with patch(
        "scripts.run_parallel_tests.subprocess.run",
        return_value=_CompletedProcess(),
    ):
        result = manager.report(plan=plan)

    assert result.status == "failed"
    assert result.exit_code == 1
    assert result.error_code == expected_code


def test_coverage_report_command_failure_is_distinct_and_nonzero(
    tmp_path: Path,
) -> None:
    """A coverage process that cannot start is not reported as a threshold failure."""
    manager = _coverage_manager(tmp_path)
    plan = _coverage_plan(tmp_path, fail_under=95)

    with patch(
        "scripts.run_parallel_tests.subprocess.run",
        side_effect=OSError("secret-command-path"),
    ):
        result = manager.report(plan=plan)

    assert result.status == "failed"
    assert result.exit_code == 127
    assert result.error_code == "coverage_command"


def test_configured_coverage_threshold_rejects_below_threshold(tmp_path: Path) -> None:
    """Real aggregate coverage fails when project policy is not met."""
    _write_coverage_workspace(tmp_path, cover_all=False)
    config = _parse(
        ["--cov=sample_pkg", "tests/test_values.py"],
        tmp_path,
    )
    summary = runner.run_parallel_tests(config)

    assert summary.scheduled_units == 1
    assert summary.exit_code != 0
    assert not summary.is_success
    assert summary.coverage_result is not None
    assert summary.coverage_result.kind == "coverage"
    assert summary.coverage_result.status == "failed"
    assert "95" in summary.coverage_result.message


def test_configured_coverage_threshold_accepts_adequate_run(tmp_path: Path) -> None:
    """Real aggregate coverage succeeds when project policy is met."""
    _write_coverage_workspace(tmp_path, cover_all=True)
    config = _parse(
        ["--cov=sample_pkg", "tests/test_values.py"],
        tmp_path,
    )
    summary = runner.run_parallel_tests(config)

    assert summary.scheduled_units == 1
    assert summary.exit_code == 0
    assert summary.is_success
    assert summary.coverage_result is not None
    assert summary.coverage_result.status == "passed"


def test_project_coverage_threshold_change_controls_aggregate_result(
    tmp_path: Path,
) -> None:
    """Changing only project policy changes the real aggregate coverage outcome."""
    _write_coverage_workspace(tmp_path, cover_all=False)
    config = _parse(
        ["--cov=sample_pkg", "tests/test_values.py"],
        tmp_path,
    )

    _set_coverage_threshold(tmp_path, 0)
    passing = runner.run_parallel_tests(config)
    _set_coverage_threshold(tmp_path, 95)
    failing = runner.run_parallel_tests(config)

    assert passing.exit_code == 0
    assert passing.coverage_result is not None
    assert passing.coverage_result.status == "passed"
    assert failing.exit_code != 0
    assert failing.coverage_result is not None
    assert failing.coverage_result.status == "failed"
    assert "95" in failing.coverage_result.message


def test_explicit_coverage_threshold_override_takes_precedence(
    tmp_path: Path,
) -> None:
    """An explicit threshold overrides project policy in both directions."""
    _write_coverage_workspace(tmp_path, cover_all=False)

    project_failing = _parse(
        [
            "--cov=sample_pkg",
            "--cov-fail-under=0",
            "tests/test_values.py",
        ],
        tmp_path,
    )
    overridden_passing = runner.run_parallel_tests(project_failing)

    _set_coverage_threshold(tmp_path, 0)
    project_passing = _parse(
        [
            "--cov=sample_pkg",
            "--cov-fail-under=95",
            "tests/test_values.py",
        ],
        tmp_path,
    )
    overridden_failing = runner.run_parallel_tests(project_passing)

    assert overridden_passing.exit_code == 0
    assert overridden_passing.coverage_result is not None
    assert overridden_passing.coverage_result.status == "passed"
    assert overridden_failing.exit_code != 0
    assert overridden_failing.coverage_result is not None
    assert overridden_failing.coverage_result.status == "failed"
    assert "95" in overridden_failing.coverage_result.message


def _write_sleeping_test(workspace: Path, delay: float) -> None:
    """Create a bounded test file for timeout and no-timeout subprocess checks."""
    tests_dir = workspace / "tests"
    tests_dir.mkdir()
    (tests_dir / "test_sleep.py").write_text(
        "import time\n"
        "import pytest\n"
        "pytestmark = pytest.mark.timeout(10)\n"
        "def test_sleep():\n"
        f"    time.sleep({delay!r})\n"
        "    assert True\n",
        encoding="utf-8",
    )


def test_over_limit_worker_is_reported_as_timeout(tmp_path: Path) -> None:
    """A positive limit yields a timed-out result and non-successful summary."""
    _write_sleeping_test(tmp_path, 0.5)
    config = _parse(
        ["--worker-timeout=0.05", "tests/test_sleep.py"],
        tmp_path,
    )
    summary = runner.run_parallel_tests(config)

    assert summary.scheduled_units == 1
    assert summary.exit_code != 0
    assert not summary.is_success
    result = summary.results[0]
    assert result.status == "timed_out"
    assert result.exit_code != 0
    assert "timeout" in result.message.lower()


def test_none_worker_timeout_uses_unbounded_communication(tmp_path: Path) -> None:
    """The explicit no-timeout mode completes a test beyond tiny limits."""
    _write_sleeping_test(tmp_path, 0.1)
    config = _parse(
        ["--worker-timeout=none", "tests/test_sleep.py"],
        tmp_path,
    )
    summary = runner.run_parallel_tests(config)

    assert summary.scheduled_units == 1
    assert summary.exit_code == 0
    assert summary.is_success
    assert summary.results[0].status == "passed"
