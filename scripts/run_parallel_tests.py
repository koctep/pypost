"""Parallel test runner orchestrator for PyPost (PYPOST-1149)."""

from __future__ import annotations

import argparse
import concurrent.futures
import glob
import json
import logging
import math
import os
import re
import shutil
import signal
import subprocess
import sys
import time
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import Any, Literal, Sequence
from uuid import uuid4

NOTICE = 25
logging.addLevelName(NOTICE, "NOTICE")

logger = logging.getLogger(__name__)

_COVERAGE_THRESHOLD_FAILURE = re.compile(
    r"\bcoverage\s+failure\b.*?\btotal\b.*?\b(?:is\s+)?less\s+than\s+"
    r"fail-under\s*=\s*\d+(?:\.\d+)?",
    re.IGNORECASE | re.DOTALL,
)
_COVERAGE_CONFIGURATION_FAILURE = re.compile(
    r"(?:\b(?:configuration|config(?:uration)?\s+file)\b.*?\b"
    r"(?:error|invalid|failed|cannot|could\s+not|couldn['’]?t|unable)\b|"
    r"\b(?:error|invalid|failed|cannot|could\s+not|couldn['’]?t|unable)\b.*?\b"
    r"(?:configuration|config(?:uration)?\s+file)\b)",
    re.IGNORECASE | re.DOTALL,
)


def _coverage_report_failure_code(output: str) -> str:
    """Classify a failed coverage report without guessing from configured policy."""
    if _COVERAGE_THRESHOLD_FAILURE.search(output):
        return "coverage_threshold"
    if _COVERAGE_CONFIGURATION_FAILURE.search(output):
        return "coverage_configuration"
    return "coverage_report"


def _log_validation_failure(
    error: RunnerValidationError,
    *,
    run_id: str,
    phase: str,
    worker_count: int | None,
) -> None:
    """Log safe scalar context for a fail-closed validation outcome.

    The actionable error text is printed by the CLI or stored in the result object.  Keeping
    it out of the structured event prevents arbitrary pytest arguments from being copied into
    logs while retaining the fields needed by CI log consumers.
    """
    logger.warning(
        "parallel_test_validation_failed run_id=%s phase=%s code=%s worker_count=%s "
        "target_supplied=%s",
        run_id,
        phase,
        error.code,
        worker_count,
        error.raw_target is not None,
    )


def _cleanup_root_coverage_fragments(repo_root: Path, *, run_id: str) -> None:
    """Remove coverage fragments emitted beside the project configuration."""
    cleanup_errors = 0
    for fragment in repo_root.glob(".coverage.*"):
        if not fragment.is_file():
            continue
        try:
            fragment.unlink()
        except OSError:
            cleanup_errors += 1
    if cleanup_errors:
        logger.warning(
            "coverage_fragment_cleanup_failed run_id=%s error_count=%d",
            run_id,
            cleanup_errors,
        )


def _configure_logging() -> None:
    logging.basicConfig(
        level=logging.INFO,
        format="%(levelname)s %(message)s",
        stream=sys.stderr,
    )


class TestStatus(str, Enum):
    """Execution status for a single test file."""

    PASSED = "passed"
    FAILED = "failed"
    SKIPPED = "skipped"
    TIMED_OUT = "timed_out"


RunStatus = Literal["passed", "failed", "skipped", "timed_out", "invalid"]


class RunnerValidationError(ValueError):
    """A user-input or discovery error that must stop the run before workers start."""

    def __init__(self, code: str, message: str, raw_target: str | None = None) -> None:
        super().__init__(message)
        self.code = code
        self.message = message
        self.raw_target = raw_target


@dataclass(frozen=True)
class ArgvSpan:
    """A half-open span in the original or replayed pytest argv."""

    start: int
    end: int
    role: Literal["runner", "pytest_option", "pytest_value", "target", "sentinel"]


@dataclass(frozen=True)
class TargetRecord:
    """One requested target, retaining its source span and optional node id."""

    raw_target: str
    file_path: Path
    node_id: str | None
    child_target: str
    argv_span: tuple[int, int] | None
    ordinal: int = 0


@dataclass(frozen=True)
class DispatchUnit:
    """One subprocess dispatch unit, grouped by backing test file."""

    file_path: Path
    records: tuple[TargetRecord, ...]
    target_spans: tuple[tuple[int, int], ...]


@dataclass(frozen=True)
class ValidationError:
    """Structured validation failure suitable for a user-facing result."""

    code: str
    message: str
    raw_target: str | None = None


@dataclass(frozen=True)
class DiscoveryResult:
    """Resolved records, grouped dispatch units, and any fail-closed errors."""

    records: tuple[TargetRecord, ...]
    units: tuple[DispatchUnit, ...]
    errors: tuple[ValidationError, ...]


@dataclass(frozen=True)
class RunResult:
    """Outcome of a test, validation, or aggregate coverage operation."""

    __test__ = False

    kind: Literal["test", "validation", "coverage"]
    status: RunStatus
    target: str | None
    exit_code: int
    duration_seconds: float
    message: str
    stdout: str = ""
    stderr: str = ""
    error_code: str | None = None

    @property
    def test_file(self) -> str:
        """Compatibility projection used by existing result consumers."""
        return self.target or ""


@dataclass(frozen=True)
class TestResult:
    """Compatibility constructor for the historical test result shape."""

    __test__ = False

    test_file: str
    status: TestStatus
    exit_code: int
    duration_seconds: float
    stdout: str
    stderr: str

    @property
    def kind(self) -> Literal["test"]:
        return "test"

    @property
    def target(self) -> str:
        return self.test_file

    @property
    def message(self) -> str:
        return self.stderr


@dataclass
class RunSummary:
    """Consolidated summary across all parallel test file executions."""

    total_files: int = 0
    passed_files: int = 0
    failed_files: int = 0
    skipped_files: int = 0
    total_wall_clock_seconds: float = 0.0
    cumulative_duration_seconds: float = 0.0
    worker_count: int = 0
    slowest_files: list[tuple[str, float]] = field(default_factory=list)
    results: list[RunResult | TestResult] = field(default_factory=list)
    scheduled_units: int | None = None
    coverage_result: RunResult | None = None
    exit_code: int | None = None

    @property
    def is_success(self) -> bool:
        """Return true only when work was scheduled and every phase passed."""
        if self.exit_code is not None:
            if self.scheduled_units is None or self.scheduled_units == 0:
                return False
            return self.exit_code == 0
        return self.total_files > 0 and self.failed_files == 0


@dataclass
class RunnerConfig:
    """Configuration for parallel test run."""

    workers: int
    enable_coverage: bool
    report_json_path: Path | None
    test_targets: list[str]
    pytest_args: list[str]
    repo_root: Path
    python_bin: Path
    worker_timeout: float | None = 30.0
    original_argv: tuple[str, ...] = ()
    pytest_argv: list[str] = field(default_factory=list)
    runner_spans: tuple[ArgvSpan, ...] = ()
    target_records: tuple[TargetRecord, ...] = ()
    coverage_sources: tuple[str, ...] | None = None
    coverage_reports: tuple[str, ...] = ()
    coverage_fail_under: int | None = None
    run_id: str = ""


@dataclass(frozen=True)
class CoverageRequest:
    """Coverage selections supplied by the caller."""

    source_override: tuple[str, ...] | None = None
    fail_under_override: int | None = None
    report_specs: tuple[str, ...] = ()


@dataclass(frozen=True)
class CoveragePlan:
    """Effective worker and aggregate coverage configuration for one run."""

    worker_data_dir: Path
    aggregate_rcfile: Path | None
    sources: tuple[str, ...] | None
    fail_under: int | None
    report_specs: tuple[str, ...]
    worker_rcfile: Path | None = None


def _load_pytest_option_schema(
    repo_root: Path,
    args: Sequence[str],
) -> dict[str, Any]:
    """Load pytest and plugin option actions for lossless argv tracing."""
    config: Any | None = None
    try:
        from _pytest.config import get_config

        config = get_config(args=list(args))
        config.invocation_params = config.InvocationParams(
            args=list(args), plugins=None, dir=repo_root
        )
        config._preparse(list(args), addopts=False)
        parser = config._parser._getparser()
        return {
            option: action
            for action in parser._actions
            for option in action.option_strings
        }
    except Exception as exc:
        raise RunnerValidationError(
            "pytest_schema_error",
            f"could not load pytest option schema: {exc}",
        ) from exc
    finally:
        if config is not None:
            config._ensure_unconfigure()


def default_worker_count() -> int:
    """Return tuned default worker count for subprocess pytest parallelism.

    Policy (PYPOST-1154): modest oversubscription for I/O-bound per-file subprocesses,
    with a ceiling to limit memory pressure from concurrent Qt-heavy workers.
    """
    cpu = max(1, os.cpu_count() or 4)
    return min(cpu + 2, 16)


def _positive_int(value: str, option: str) -> int:
    """Parse a positive integer and provide actionable runner guidance."""
    try:
        parsed = int(value)
    except (TypeError, ValueError) as exc:
        raise RunnerValidationError(
            "invalid_workers",
            f"{option} received {value!r}; workers must be a positive integer",
        ) from exc
    if parsed <= 0:
        raise RunnerValidationError(
            "invalid_workers",
            f"{option} received {value!r}; workers must be a positive integer",
        )
    return parsed


def get_worker_count(cli_workers: int | str | None = None) -> int:
    """Determine effective worker count following precedence rules.

    Precedence:
    1. Explicit CLI argument (--workers / -n)
    2. WORKERS environment variable
    3. PYTEST_WORKERS environment variable
    4. default_worker_count()
    """
    if cli_workers is not None:
        return _positive_int(str(cli_workers), "--workers")

    for variable in ("WORKERS", "PYTEST_WORKERS"):
        workers_env = os.environ.get(variable)
        if workers_env is not None:
            return _positive_int(workers_env.strip(), variable)

    return default_worker_count()


DEFAULT_WORKER_TIMEOUT = 30.0


def parse_worker_timeout(value: str | float | None, option: str) -> float | None:
    """Parse a finite positive timeout or the explicit ``none`` spelling."""
    if value is None:
        raise RunnerValidationError(
            "missing_timeout",
            f"{option} requires a value: use a positive finite number or 'none'",
        )
    if isinstance(value, str) and value.strip().lower() == "none":
        return None
    try:
        parsed = float(value)
    except (TypeError, ValueError) as exc:
        raise RunnerValidationError(
            "invalid_timeout",
            f"{option} received {value!r}; timeout must be positive and finite or 'none'",
        ) from exc
    if parsed <= 0 or not math.isfinite(parsed):
        raise RunnerValidationError(
            "invalid_timeout",
            f"{option} received {value!r}; timeout must be positive and finite or 'none'",
        )
    return parsed


def get_worker_timeout(cli_timeout: float | str | None = None) -> float | None:
    """Determine effective per-worker timeout following precedence rules.

    Precedence:
    1. Explicit CLI argument (--worker-timeout)
    2. WORKER_TIMEOUT environment variable
    3. DEFAULT_WORKER_TIMEOUT (30 seconds)
    """
    if cli_timeout is not None:
        return parse_worker_timeout(cli_timeout, "--worker-timeout")

    timeout_env = os.environ.get("WORKER_TIMEOUT")
    if timeout_env is not None:
        return parse_worker_timeout(timeout_env.strip(), "WORKER_TIMEOUT")

    return DEFAULT_WORKER_TIMEOUT


def _coverage_threshold(value: str) -> int:
    """Validate an aggregate coverage threshold percentage."""
    try:
        threshold = int(value)
    except (TypeError, ValueError) as exc:
        raise RunnerValidationError(
            "invalid_coverage_threshold",
            f"--cov-fail-under received {value!r}; use an integer from 0 through 100",
        ) from exc
    if not 0 <= threshold <= 100:
        raise RunnerValidationError(
            "invalid_coverage_threshold",
            f"--cov-fail-under received {value!r}; use an integer from 0 through 100",
        )
    return threshold


def _validate_report_spec(spec: str) -> None:
    """Validate one pytest-cov compatible aggregate report specification."""
    if spec == "":
        return
    format_name, separator, destination = spec.partition(":")
    formats = {"term", "term-missing", "term-m", "html", "xml", "json", "lcov", "annotate"}
    if format_name not in formats or (separator and not destination):
        raise RunnerValidationError(
            "invalid_coverage_report",
            f"unsupported --cov-report value {spec!r}; use FORMAT or FORMAT:DEST",
        )


def _registered_action_for_token(
    token: str,
    option_schema: dict[str, Any],
) -> tuple[Any | None, bool]:
    """Return a registered action and whether ``token`` has an attached value."""
    option_name = token.split("=", 1)[0]
    action = option_schema.get(option_name)
    if action is not None:
        return action, False

    if "=" in token:
        return None, False

    short_matches = [
        (option, candidate)
        for candidate in option_schema.values()
        for option in candidate.option_strings
        if option.startswith("-")
        and not option.startswith("--")
        and token.startswith(option)
        and len(token) > len(option)
    ]
    if not short_matches:
        return None, False
    _, action = max(short_matches, key=lambda match: len(match[0]))
    return action, True


def _resolves_as_target(repo_root: Path, token: str) -> bool:
    """Return whether an opaque option value could be a pytest target."""
    path_text = token.split("::", 1)[0]
    if not path_text or path_text.startswith("-"):
        return False

    path = Path(path_text)
    if not path.is_absolute():
        path = repo_root / path
    if path.exists():
        return path.is_file() or path.is_dir()

    if any(character in path_text for character in "*?["):
        try:
            return any(Path(match).exists() for match in glob.glob(str(path)))
        except OSError:
            return False

    # A missing Python path is still target-like: silently treating it as an opaque
    # plugin value would make the runner fall back to its default test discovery.
    return "::" in token or "/" in path_text or "\\" in path_text or path.suffix == ".py"


class CLIParser:
    """CLI argument parser separating orchestrator options and pytest passthrough flags."""

    def parse_args(
        self,
        args: Sequence[str] | None = None,
        repo_root: Path | None = None,
    ) -> RunnerConfig:
        """Parse CLI arguments into RunnerConfig."""
        if args is None:
            args = sys.argv[1:]
        if repo_root is None:
            repo_root = Path.cwd()

        original = tuple(args)
        sentinel = original.index("--") if "--" in original else None
        parse_end = sentinel if sentinel is not None else len(original)

        # Let argparse own the typed runner vocabulary and unknown-option behavior.  The
        # replay scan below is intentionally separate because argparse's unknown list loses
        # the caller's original interleaving.
        argparse_parser = argparse.ArgumentParser(add_help=False, allow_abbrev=False)
        argparse_parser.add_argument("-n", "--workers")
        argparse_parser.add_argument("--worker-timeout")
        argparse_parser.add_argument("--cov", nargs="?", const="")
        argparse_parser.add_argument("--report-json")
        argparse_parser.add_argument("--cov-fail-under")
        argparse_parser.add_argument("--cov-report", action="append")
        try:
            namespace, _ = argparse_parser.parse_known_args(list(original[:parse_end]))
        except SystemExit as exc:
            raise RunnerValidationError(
                "invalid_arguments",
                "invalid runner arguments; check --workers, --worker-timeout, and coverage options",
            ) from exc

        runner_spans: list[ArgvSpan] = []
        coverage_sources: list[str] = []
        coverage_reports: list[str] = []
        coverage_enabled = False
        coverage_fail_under: int | None = None
        report_json_path: Path | None = None
        cli_workers: str | None = namespace.workers
        cli_worker_timeout: str | None = namespace.worker_timeout

        def consume_value(index: int, option: str) -> tuple[str, int]:
            if index + 1 >= parse_end or original[index + 1] == "--":
                raise RunnerValidationError(
                    "missing_value",
                    f"{option} requires a value",
                )
            return original[index + 1], index + 2

        i = 0
        while i < parse_end:
            arg = original[i]
            start = i
            if arg in ("-n", "--workers"):
                value, i = consume_value(i, arg)
                _positive_int(value, arg)
                cli_workers = value
                runner_spans.append(ArgvSpan(start, i, "runner"))
                continue
            if arg.startswith("--workers="):
                cli_workers = arg.split("=", 1)[1]
                _positive_int(cli_workers, "--workers")
                i += 1
                runner_spans.append(ArgvSpan(start, i, "runner"))
                continue
            if arg.startswith("-n") and len(arg) > 2:
                cli_workers = arg[2:]
                _positive_int(cli_workers, "-n")
                i += 1
                runner_spans.append(ArgvSpan(start, i, "runner"))
                continue
            if arg == "--worker-timeout":
                value, i = consume_value(i, arg)
                parse_worker_timeout(value, arg)
                cli_worker_timeout = value
                runner_spans.append(ArgvSpan(start, i, "runner"))
                continue
            if arg.startswith("--worker-timeout="):
                cli_worker_timeout = arg.split("=", 1)[1]
                parse_worker_timeout(cli_worker_timeout, "--worker-timeout")
                i += 1
                runner_spans.append(ArgvSpan(start, i, "runner"))
                continue
            if arg == "--cov":
                coverage_enabled = True
                i += 1
                runner_spans.append(ArgvSpan(start, i, "runner"))
                continue
            if arg.startswith("--cov="):
                source = arg.split("=", 1)[1]
                if not source:
                    raise RunnerValidationError(
                        "invalid_coverage", "--cov= requires a non-empty source"
                    )
                coverage_enabled = True
                coverage_sources.append(source)
                i += 1
                runner_spans.append(ArgvSpan(start, i, "runner"))
                continue
            if arg == "--report-json":
                value, i = consume_value(i, arg)
                report_json_path = Path(value)
                runner_spans.append(ArgvSpan(start, i, "runner"))
                continue
            if arg.startswith("--report-json="):
                value = arg.split("=", 1)[1]
                if not value:
                    raise RunnerValidationError("invalid_report", "--report-json requires a path")
                report_json_path = Path(value)
                i += 1
                runner_spans.append(ArgvSpan(start, i, "runner"))
                continue
            if arg == "--cov-report":
                value, i = consume_value(i, arg)
                coverage_reports.append(value)
                runner_spans.append(ArgvSpan(start, i, "runner"))
                continue
            if arg.startswith("--cov-report="):
                coverage_reports.append(arg.split("=", 1)[1])
                i += 1
                runner_spans.append(ArgvSpan(start, i, "runner"))
                continue
            if arg == "--cov-fail-under":
                value, i = consume_value(i, arg)
                coverage_fail_under = _coverage_threshold(value)
                runner_spans.append(ArgvSpan(start, i, "runner"))
                continue
            if arg.startswith("--cov-fail-under="):
                coverage_fail_under = _coverage_threshold(arg.split("=", 1)[1])
                i += 1
                runner_spans.append(ArgvSpan(start, i, "runner"))
                continue
            i += 1

        workers = get_worker_count(cli_workers)
        worker_timeout = get_worker_timeout(cli_worker_timeout)
        if (coverage_fail_under is not None or coverage_reports) and not coverage_enabled:
            raise RunnerValidationError(
                "coverage_without_mode",
                "coverage report options require --cov or --cov=SOURCE",
            )
        python_bin = Path(sys.executable)

        layout = PytestArgvLayout.from_project(repo_root, original, runner_spans)
        target_records = _records_from_layout(layout)
        target_positions = {
            position
            for start, end in layout.positional_spans
            for position in range(start, end)
        }
        pytest_args = [
            token
            for index, token in enumerate(layout.pytest_argv)
            if index not in target_positions
            and token != "--"
        ]
        test_targets = [record.raw_target for record in target_records]
        return RunnerConfig(
            workers=workers,
            enable_coverage=coverage_enabled,
            report_json_path=report_json_path,
            test_targets=test_targets,
            pytest_args=pytest_args,
            repo_root=repo_root,
            python_bin=python_bin,
            worker_timeout=worker_timeout,
            original_argv=original,
            pytest_argv=list(layout.pytest_argv),
            runner_spans=tuple(runner_spans),
            target_records=target_records,
            coverage_sources=tuple(coverage_sources) or None,
            coverage_reports=tuple(coverage_reports),
            coverage_fail_under=coverage_fail_under,
        )


class PytestArgvLayout:
    """Lossless replay layout for runner-owned and pytest-owned argv tokens."""

    def __init__(
        self,
        original_argv: tuple[str, ...],
        pytest_argv: tuple[str, ...],
        runner_spans: tuple[ArgvSpan, ...],
        sentinel_index: int | None,
        spans: tuple[ArgvSpan, ...],
        positional_spans: tuple[tuple[int, int], ...],
    ) -> None:
        self.original_argv = original_argv
        self.pytest_argv = pytest_argv
        self.runner_spans = runner_spans
        self.sentinel_index = sentinel_index
        self.pre_sentinel_tokens = (
            pytest_argv[:sentinel_index] if sentinel_index is not None else pytest_argv
        )
        self.post_sentinel_tokens = (
            pytest_argv[sentinel_index + 1 :] if sentinel_index is not None else ()
        )
        self.spans = spans
        self.positional_spans = positional_spans

    @classmethod
    def from_project(
        cls,
        repo_root: Path,
        original_argv: Sequence[str],
        runner_spans: Sequence[ArgvSpan],
    ) -> "PytestArgvLayout":
        """Remove only owned spans and classify positional pytest targets conservatively."""
        original = tuple(original_argv)
        owned = {
            position
            for span in runner_spans
            for position in range(span.start, span.end)
        }
        pytest_argv = tuple(token for index, token in enumerate(original) if index not in owned)
        sentinel_index = pytest_argv.index("--") if "--" in pytest_argv else None
        option_schema = _load_pytest_option_schema(
            repo_root,
            pytest_argv[:sentinel_index] if sentinel_index is not None else pytest_argv,
        )
        spans: list[ArgvSpan] = []
        positional: list[tuple[int, int]] = []
        index = 0
        while index < len(pytest_argv):
            token = pytest_argv[index]
            if sentinel_index is not None and index == sentinel_index:
                spans.append(ArgvSpan(index, index + 1, "sentinel"))
                index += 1
                continue
            if sentinel_index is not None and index > sentinel_index:
                spans.append(ArgvSpan(index, index + 1, "target"))
                positional.append((index, index + 1))
                index += 1
                continue
            if token.startswith("-"):
                spans.append(ArgvSpan(index, index + 1, "pytest_option"))
                index += 1
                action, attached_value = _registered_action_for_token(token, option_schema)
                if action is not None and "=" not in token and not attached_value:
                    nargs = action.nargs
                    if nargs == 0:
                        value_count = 0
                    elif nargs in (None, 1):
                        value_count = 1
                    elif nargs == "?":
                        value_count = int(
                            index < len(pytest_argv)
                            and not pytest_argv[index].startswith("-")
                        )
                    elif nargs in ("*", "+"):
                        value_count = 0
                        while (
                            index + value_count < len(pytest_argv)
                            and not pytest_argv[index + value_count].startswith("-")
                        ):
                            value_count += 1
                    elif isinstance(nargs, int):
                        value_count = nargs
                    else:
                        value_count = 0
                    for _ in range(value_count):
                        if index >= len(pytest_argv):
                            break
                        spans.append(ArgvSpan(index, index + 1, "pytest_value"))
                        index += 1
                elif action is None and "=" not in token:
                    # Unknown plugin options are opaque until the next option/sentinel.  A
                    # target-like value is ambiguous because it could be a lost explicit target.
                    while (
                        index < len(pytest_argv)
                        and pytest_argv[index] != "--"
                        and not pytest_argv[index].startswith("-")
                    ):
                        value = pytest_argv[index]
                        if _resolves_as_target(repo_root, value):
                            raise RunnerValidationError(
                                "ambiguous_passthrough",
                                f"unknown pytest option {token!r} has target-like value "
                                f"{value!r}; register the option or place it after '--'",
                                raw_target=value,
                            )
                        spans.append(ArgvSpan(index, index + 1, "pytest_value"))
                        index += 1
                continue
            spans.append(ArgvSpan(index, index + 1, "target"))
            positional.append((index, index + 1))
            index += 1
        return cls(
            original_argv=original,
            pytest_argv=pytest_argv,
            runner_spans=tuple(runner_spans),
            sentinel_index=sentinel_index,
            spans=tuple(spans),
            positional_spans=tuple(positional),
        )


class TestDiscovery:
    """Discovers target records and groups them into file-level dispatch units."""

    __test__ = False

    @staticmethod
    def _backing_path(repo_root: Path, raw_target: str) -> tuple[Path, str | None]:
        path_text, separator, node_id = raw_target.partition("::")
        path = Path(path_text)
        if not path.is_absolute():
            path = repo_root / path
        return path, node_id if separator else None

    def discover(
        self,
        *,
        repo_root: Path,
        target_records: Sequence[TargetRecord],
    ) -> DiscoveryResult:
        """Resolve targets, reject missing selections, and group by backing file."""
        if not target_records:
            default_tests = repo_root / "tests"
            paths = sorted(default_tests.glob("test_*.py")) if default_tests.is_dir() else []
            records = tuple(
                TargetRecord(
                    raw_target=str(path),
                    file_path=path.resolve(),
                    node_id=None,
                    child_target=str(path),
                    argv_span=None,
                    ordinal=index,
                )
                for index, path in enumerate(paths)
                if path.is_file()
            )
            if not records:
                return DiscoveryResult(
                    records=(),
                    units=(),
                    errors=(
                        ValidationError("empty_discovery", "no test files were discovered"),
                    ),
                )
            return self._group(records)

        resolved: list[TargetRecord] = []
        errors: list[ValidationError] = []
        seen: set[tuple[Path, str | None]] = set()
        for record in target_records:
            base, node_id = self._backing_path(repo_root, record.raw_target)
            candidates: list[Path]
            if base.is_dir():
                candidates = sorted(base.glob("test_*.py"))
            elif base.is_file():
                candidates = [base]
            else:
                pattern = str(base)
                glob_pattern = (
                    pattern[len(str(repo_root)) + 1 :]
                    if pattern.startswith(str(repo_root))
                    else record.raw_target.split("::", 1)[0]
                )
                candidates = sorted(
                    path for path in repo_root.glob(glob_pattern) if path.is_file()
                )
            if not candidates:
                errors.append(
                    ValidationError(
                        "target_not_found",
                        f"target {record.raw_target!r} did not resolve to a test file",
                        record.raw_target,
                    )
                )
                continue
            for candidate in candidates:
                resolved_path = candidate.resolve()
                resolved_key = (resolved_path, node_id)
                if resolved_key in seen:
                    continue
                seen.add(resolved_key)
                child_target = record.raw_target if len(candidates) == 1 and node_id else (
                    str(candidate.relative_to(repo_root))
                    if candidate.is_relative_to(repo_root)
                    else str(candidate)
                )
                resolved.append(
                    TargetRecord(
                        raw_target=record.raw_target,
                        file_path=resolved_path,
                        node_id=node_id,
                        child_target=child_target,
                        argv_span=record.argv_span,
                        ordinal=record.ordinal,
                    )
                )
        if errors:
            return DiscoveryResult(tuple(resolved), (), tuple(errors))
        return self._group(tuple(resolved))

    @staticmethod
    def _group(records: Sequence[TargetRecord]) -> DiscoveryResult:
        groups: dict[Path, list[TargetRecord]] = {}
        for record in records:
            groups.setdefault(record.file_path, []).append(record)
        units = tuple(
            DispatchUnit(
                file_path=file_path,
                records=tuple(group),
                target_spans=tuple(
                    span for span in (record.argv_span for record in group) if span is not None
                ),
            )
            for file_path, group in groups.items()
        )
        return DiscoveryResult(tuple(records), units, ())

    @staticmethod
    def discover_test_files(repo_root: Path, targets: list[str]) -> list[Path]:
        """Compatibility projection returning only resolved file paths."""
        records = tuple(
            TargetRecord(
                target, Path(target), None, target, (index, index + 1), ordinal=index
            )
            for index, target in enumerate(targets)
        )
        result = TestDiscovery().discover(repo_root=repo_root, target_records=records)
        return [unit.file_path for unit in result.units]


def kill_process_group(pid: int, *, run_id: str = "-") -> None:
    """Terminate a process group cleanly on POSIX systems with Windows fallback."""
    if sys.platform == "win32":
        try:
            os.kill(pid, signal.SIGTERM)
        except (ProcessLookupError, PermissionError, OSError) as exc:
            logger.debug(
                "kill_process_group win32 failed run_id=%s pid=%s error_type=%s",
                run_id,
                pid,
                type(exc).__name__,
            )
        return

    try:
        try:
            pgid = os.getpgid(pid)
        except (ProcessLookupError, OSError) as exc:
            logger.debug(
                "kill_process_group getpgid failed run_id=%s pid=%s error_type=%s; "
                "falling back to pgid=pid",
                run_id,
                pid,
                type(exc).__name__,
            )
            pgid = pid
        logger.debug(
            "kill_process_group sending SIGKILL run_id=%s to pgid=%s for pid=%s",
            run_id,
            pgid,
            pid,
        )
        os.killpg(pgid, signal.SIGKILL)
    except (ProcessLookupError, PermissionError, OSError) as exc:
        logger.debug(
            "kill_process_group killpg failed run_id=%s for pgid=%s error_type=%s",
            run_id,
            pgid,
            type(exc).__name__,
        )


def build_child_argv(
    *,
    layout: PytestArgvLayout,
    all_target_records: Sequence[TargetRecord],
    unit: DispatchUnit,
) -> list[str]:
    """Build one child argv without changing the caller's pytest token ordering."""
    records_by_span: dict[tuple[int, int], list[TargetRecord]] = {}
    for record in unit.records:
        if record.argv_span is not None:
            records_by_span.setdefault(record.argv_span, []).append(record)
    target_spans = set(layout.positional_spans)
    command: list[str] = []
    for index, token in enumerate(layout.pytest_argv):
        matching = records_by_span.get((index, index + 1))
        if (index, index + 1) in target_spans:
            if matching:
                command.extend(dict.fromkeys(record.child_target for record in matching))
            continue
        command.append(token)
    if not target_spans:
        insertion = layout.sentinel_index
        target = unit.records[0].child_target if unit.records else str(unit.file_path)
        if insertion is None:
            command.append(target)
        else:
            command.insert(insertion, target)
    return command


def _insert_before_sentinel(argv: Sequence[str], additions: Sequence[str]) -> list[str]:
    """Insert runner-owned child flags before a retained pytest ``--`` sentinel."""
    command = list(argv)
    insertion = command.index("--") if "--" in command else len(command)
    command[insertion:insertion] = additions
    return command


def _display_path(repo_root: Path, path: Path) -> str:
    """Return a repository-relative path when possible."""
    try:
        return str(path.relative_to(repo_root))
    except ValueError:
        return str(path)


class SubprocessTestExecutor:
    """Execute one dispatch unit in an isolated subprocess."""

    def __init__(self, config: RunnerConfig) -> None:
        self.config = config

    def run_dispatch_unit(
        self,
        *,
        unit: DispatchUnit,
        layout: PytestArgvLayout,
        all_target_records: Sequence[TargetRecord],
        index: int,
        total: int,
        coverage_plan: CoveragePlan | None,
    ) -> RunResult:
        """Run one file-level unit and capture its bounded or unbounded outcome."""
        rel_file = _display_path(self.config.repo_root, unit.file_path)
        logger.debug(
            "test_file_started run_id=%s file=%s index=%d total=%d timeout_seconds=%s "
            "coverage_enabled=%s",
            self.config.run_id or "-",
            rel_file,
            index,
            total,
            self.config.worker_timeout,
            coverage_plan is not None,
        )
        env = os.environ.copy()
        env["QT_QPA_PLATFORM"] = "offscreen"
        current_pythonpath = env.get("PYTHONPATH", "")
        repo_str = str(self.config.repo_root)
        env["PYTHONPATH"] = f"{repo_str}:{current_pythonpath}" if current_pythonpath else repo_str

        cmd = [
            str(self.config.python_bin),
            "-c",
            "import sys, os, pytest; "
            "code = int(pytest.main(sys.argv[1:])); "
            "sys.stdout.flush(); sys.stderr.flush(); "
            "os._exit(code)",
        ]
        child_argv = build_child_argv(
            layout=layout,
            all_target_records=all_target_records,
            unit=unit,
        )

        if coverage_plan is not None:
            cov_file = coverage_plan.worker_data_dir / f".coverage.worker_{index}_{uuid4().hex}"
            env["COVERAGE_FILE"] = str(cov_file)
            if coverage_plan.worker_rcfile is not None:
                env["COVERAGE_RCFILE"] = str(coverage_plan.worker_rcfile)
            source_args = [f"--cov={source}" for source in (coverage_plan.sources or ())]
            if not source_args:
                source_args = ["--cov"]
            child_argv = _insert_before_sentinel(
                child_argv,
                [*source_args, "--cov-report="],
            )

        cmd.extend(child_argv)

        start_time = time.perf_counter()
        popen_kwargs: dict[str, Any] = {
            "cwd": str(self.config.repo_root),
            "env": env,
            "stdout": subprocess.PIPE,
            "stderr": subprocess.PIPE,
            "text": True,
        }
        if sys.platform != "win32":
            popen_kwargs["start_new_session"] = True

        proc = subprocess.Popen(cmd, **popen_kwargs)
        try:
            if self.config.worker_timeout is None:
                stdout, stderr = proc.communicate()
            else:
                stdout, stderr = proc.communicate(timeout=self.config.worker_timeout)
        except subprocess.TimeoutExpired:
            duration = time.perf_counter() - start_time
            kill_process_group(proc.pid, run_id=self.config.run_id or "-")
            try:
                proc.kill()
            except (ProcessLookupError, OSError):
                pass
            stdout, stderr = proc.communicate()
            stdout_str = stdout or ""
            stderr_str = stderr or ""
            timeout_note = f"worker timeout after {self.config.worker_timeout}s"
            stderr_str = f"{stderr_str}\n{timeout_note}".strip()
            logger.warning(
                "worker_timeout run_id=%s file=%s timeout_seconds=%s duration_seconds=%.2f "
                "exit_code=-9",
                self.config.run_id or "-",
                rel_file,
                self.config.worker_timeout,
                duration,
            )
            return RunResult(
                kind="test",
                status="timed_out",
                target=rel_file,
                exit_code=-9,
                duration_seconds=duration,
                message=timeout_note,
                stdout=stdout_str,
                stderr=stderr_str,
            )
        duration = time.perf_counter() - start_time

        if proc.returncode == 0:
            status = "passed"
        elif proc.returncode == 5:
            # Pytest exit code 5: no tests collected (e.g. due to -k or -m filter)
            status = "skipped"
        else:
            status = "failed"

        return RunResult(
            kind="test",
            status=status,
            target=rel_file,
            exit_code=proc.returncode if proc.returncode is not None else 1,
            duration_seconds=duration,
            message=(stderr or "").strip(),
            stdout=stdout or "",
            stderr=stderr or "",
        )


class CoverageManager:
    """Prepare, combine, and report one aggregate coverage plan."""

    def __init__(
        self,
        repo_root: Path,
        cov_dir: Path,
        python_bin: Path | None = None,
        run_id: str = "",
    ) -> None:
        self.repo_root = repo_root
        self.cov_dir = cov_dir
        self.python_bin = python_bin or Path(sys.executable)
        self.run_id = run_id or "-"

    def prepare(
        self,
        *,
        repo_root: Path | None = None,
        python_bin: Path | None = None,
        request: CoverageRequest | None = None,
    ) -> CoveragePlan:
        """Create fresh data storage and return the effective aggregate plan."""
        if repo_root is not None:
            self.repo_root = repo_root
        if python_bin is not None:
            self.python_bin = python_bin
        if request is None:
            request = CoverageRequest()
        self.cleanup_root_fragments()
        if self.cov_dir.exists():
            shutil.rmtree(self.cov_dir)
        self.cov_dir.mkdir(parents=True, exist_ok=True)

        root_cov = self.repo_root / ".coverage"
        if root_cov.exists():
            try:
                root_cov.unlink()
            except OSError:
                pass

        configured_sources, configured_threshold = self._read_project_policy()
        sources = request.source_override or configured_sources
        fail_under = (
            request.fail_under_override
            if request.fail_under_override is not None
            else configured_threshold
        )
        reports = request.report_specs
        for report_spec in reports:
            _validate_report_spec(report_spec)
        rcfile: Path | None = None
        if request.source_override is not None or request.fail_under_override is not None:
            rcfile = self.cov_dir / "aggregate.coveragerc"
            lines = ["[run]"]
            if sources:
                lines.append("source =")
                lines.extend(f"    {source}" for source in sources)
            if fail_under is not None:
                lines.extend(["", "[report]", f"fail_under = {fail_under}"])
            rcfile.write_text("\n".join(lines) + "\n", encoding="utf-8")
        worker_rcfile = self.cov_dir / "worker.coveragerc"
        worker_lines = ["[run]"]
        if sources:
            worker_lines.append("source =")
            worker_lines.extend(f"    {source}" for source in sources)
        worker_lines.extend(["", "[report]", "fail_under = 0"])
        worker_rcfile.write_text("\n".join(worker_lines) + "\n", encoding="utf-8")
        logger.info(
            "coverage_collection_prepared run_id=%s source_count=%d report_count=%d "
            "fail_under=%s threshold_overridden=%s",
            self.run_id,
            len(sources or ()),
            len(reports),
            fail_under,
            request.fail_under_override is not None,
        )
        return CoveragePlan(
            worker_data_dir=self.cov_dir,
            aggregate_rcfile=rcfile,
            sources=sources,
            fail_under=fail_under,
            report_specs=reports,
            worker_rcfile=worker_rcfile,
        )

    def cleanup_root_fragments(self) -> None:
        """Remove coverage fragments accidentally emitted beside the project config."""
        _cleanup_root_coverage_fragments(self.repo_root, run_id=self.run_id)

    def _read_project_policy(self) -> tuple[tuple[str, ...] | None, int | None]:
        """Read coverage source and threshold from the project configuration."""
        config_path = self.repo_root / "pyproject.toml"
        if not config_path.is_file():
            return None, None
        try:
            import tomllib

            data = tomllib.loads(config_path.read_text(encoding="utf-8"))
        except (OSError, tomllib.TOMLDecodeError) as exc:
            raise RunnerValidationError(
                "invalid_coverage_config",
                f"could not read coverage configuration from {config_path}: {exc}",
            ) from exc
        coverage = data.get("tool", {}).get("coverage", {})
        run = coverage.get("run", {})
        report = coverage.get("report", {})
        source = run.get("source")
        sources: tuple[str, ...] | None
        if isinstance(source, str):
            sources = (source,)
        elif isinstance(source, list) and all(isinstance(item, str) for item in source):
            sources = tuple(source)
        else:
            sources = None
        fail_under = report.get("fail_under")
        if fail_under is not None:
            try:
                fail_under = _coverage_threshold(str(fail_under))
            except RunnerValidationError:
                raise RunnerValidationError(
                    "invalid_coverage_config",
                    "coverage report fail_under must be an integer from 0 through 100 "
                    f"in {config_path}",
                )
        return sources, fail_under

    @staticmethod
    def _report_command(
        python_bin: Path,
        plan: CoveragePlan,
        command: list[str],
    ) -> list[str]:
        """Add the aggregate rcfile and threshold to a coverage command."""
        result = [str(python_bin), "-m", "coverage", *command]
        if plan.aggregate_rcfile is not None:
            result.append(f"--rcfile={plan.aggregate_rcfile}")
        if command[0] == "report" and plan.fail_under is not None:
            result.append(f"--fail-under={plan.fail_under}")
        return result

    def combine(self, *, plan: CoveragePlan) -> RunResult:
        """Combine all worker fragments, failing when no data was collected."""
        start_time = time.perf_counter()
        cov_files = list(self.cov_dir.glob(".coverage*"))
        logger.info(
            "coverage_aggregation_started run_id=%s data_file_count=%d",
            self.run_id,
            len(cov_files),
        )
        if not cov_files:
            duration = time.perf_counter() - start_time
            logger.error(
                "coverage_aggregation_failed run_id=%s reason=no_data data_file_count=0 "
                "exit_code=2 duration_seconds=%.2f",
                self.run_id,
                duration,
            )
            return RunResult(
                kind="coverage", status="failed", target=None, exit_code=2,
                duration_seconds=duration, message="No coverage data files collected.",
                error_code="coverage_no_data",
            )

        output_parts: list[str] = []

        combine_cmd = [
            str(self.python_bin),
            "-m",
            "coverage",
            "combine",
            *(str(path) for path in cov_files),
        ]
        try:
            combine_proc = subprocess.run(
                combine_cmd,
                cwd=str(self.repo_root),
                capture_output=True,
                text=True,
            )
        except OSError:
            duration = time.perf_counter() - start_time
            logger.error(
                "coverage_aggregation_failed run_id=%s reason=coverage_command "
                "data_file_count=%d exit_code=127 duration_seconds=%.2f",
                self.run_id,
                len(cov_files),
                duration,
            )
            return RunResult(
                kind="coverage",
                status="failed",
                target=None,
                exit_code=127,
                duration_seconds=duration,
                message="Coverage combine command could not be started.",
                error_code="coverage_command",
            )
        if combine_proc.stdout.strip():
            output_parts.append(combine_proc.stdout.strip())
        if combine_proc.stderr.strip():
            output_parts.append(combine_proc.stderr.strip())
        message = "\n".join(output_parts)
        duration = time.perf_counter() - start_time
        if combine_proc.returncode == 0:
            logger.info(
                "coverage_aggregation_completed run_id=%s status=passed data_file_count=%d "
                "exit_code=0 duration_seconds=%.2f",
                self.run_id,
                len(cov_files),
                duration,
            )
        else:
            logger.error(
                "coverage_aggregation_failed run_id=%s reason=combine_error "
                "data_file_count=%d exit_code=%d duration_seconds=%.2f",
                self.run_id,
                len(cov_files),
                combine_proc.returncode,
                duration,
            )
        return RunResult(
            kind="coverage",
            status="passed" if combine_proc.returncode == 0 else "failed",
            target=None,
            exit_code=combine_proc.returncode,
            duration_seconds=duration,
            message=message,
            stdout=combine_proc.stdout or "",
            stderr=combine_proc.stderr or "",
            error_code=None if combine_proc.returncode == 0 else "coverage_combine",
        )

    def report(self, *, plan: CoveragePlan) -> RunResult:
        """Run the threshold-bearing report and requested artifact reports."""
        start_time = time.perf_counter()
        output_parts: list[str] = []
        specs = plan.report_specs
        logger.info(
            "coverage_report_started run_id=%s report_count=%d fail_under=%s",
            self.run_id,
            len(specs),
            plan.fail_under,
        )
        show_missing = not specs or any(
            spec.partition(":")[0] in ("term-missing", "term-m") for spec in specs
        )
        report_args = ["report"]
        if show_missing:
            report_args.append("-m")
        try:
            report_proc = subprocess.run(
                self._report_command(self.python_bin, plan, report_args),
                cwd=str(self.repo_root), capture_output=True, text=True,
            )
        except OSError:
            duration = time.perf_counter() - start_time
            logger.error(
                "coverage_report_failed run_id=%s reason=coverage_command exit_code=127 "
                "duration_seconds=%.2f",
                self.run_id,
                duration,
            )
            return RunResult(
                kind="coverage",
                status="failed",
                target=None,
                exit_code=127,
                duration_seconds=duration,
                message="Coverage report command could not be started.",
                error_code="coverage_command",
            )
        if report_proc.stdout.strip():
            output_parts.append(report_proc.stdout.strip())
        if report_proc.stderr.strip():
            output_parts.append(report_proc.stderr.strip())
        artifact_failures = report_proc.returncode != 0
        error_code: str | None = None
        failure_exit_code = report_proc.returncode
        if report_proc.returncode != 0:
            error_code = _coverage_report_failure_code("\n".join(output_parts))
        if report_proc.returncode == 0:
            for spec in specs or ("html:htmlcov",):
                if not spec:
                    continue
                format_name, _, destination = spec.partition(":")
                if format_name in ("term", "term-missing", "term-m"):
                    continue
                if format_name == "html":
                    artifact_args = ["html", "-d", destination or "htmlcov"]
                elif format_name == "xml":
                    artifact_args = ["xml", "-o", destination or "coverage.xml"]
                elif format_name == "json":
                    artifact_args = ["json", "-o", destination or "coverage.json"]
                elif format_name == "lcov":
                    artifact_args = ["lcov", "-o", destination or "coverage.lcov"]
                elif format_name == "annotate":
                    artifact_args = ["annotate", "-d", destination or "annotated"]
                else:
                    continue
                try:
                    artifact_proc = subprocess.run(
                        self._report_command(self.python_bin, plan, artifact_args),
                        cwd=str(self.repo_root), capture_output=True, text=True,
                    )
                except OSError:
                    artifact_failures = True
                    if error_code is None:
                        error_code = "coverage_command"
                        failure_exit_code = 127
                    continue
                artifact_failures = artifact_failures or artifact_proc.returncode != 0
                if artifact_proc.returncode != 0 and error_code is None:
                    artifact_output = "\n".join(
                        part for part in (artifact_proc.stdout, artifact_proc.stderr) if part
                    )
                    error_code = (
                        "coverage_configuration"
                        if _COVERAGE_CONFIGURATION_FAILURE.search(artifact_output)
                        else "coverage_artifact"
                    )
                    failure_exit_code = artifact_proc.returncode
                if artifact_proc.stdout.strip():
                    output_parts.append(artifact_proc.stdout.strip())
                if artifact_proc.stderr.strip():
                    output_parts.append(artifact_proc.stderr.strip())
        duration = time.perf_counter() - start_time
        status = "failed" if artifact_failures else "passed"
        if status == "passed":
            logger.info(
                "coverage_report_completed run_id=%s status=passed report_count=%d "
                "fail_under=%s exit_code=0 duration_seconds=%.2f",
                self.run_id,
                len(specs),
                plan.fail_under,
                duration,
            )
        else:
            logger.error(
                "coverage_report_failed run_id=%s reason=%s exit_code=%d "
                "duration_seconds=%.2f",
                self.run_id,
                error_code or "unknown",
                failure_exit_code,
                duration,
            )
        return RunResult(
            kind="coverage",
            status=status,
            target=None,
            exit_code=failure_exit_code if artifact_failures else 0,
            duration_seconds=duration,
            message="\n".join(output_parts),
            stdout="\n".join(output_parts),
            error_code=error_code,
        )


class JsonReporter:
    """Serializes test run results into machine-readable JSON."""

    @staticmethod
    def to_dict(summary: RunSummary) -> dict[str, Any]:
        """Convert RunSummary into dictionary matching JSON schema."""
        return {
            "summary": {
                "total_files": summary.total_files,
                "passed_files": summary.passed_files,
                "failed_files": summary.failed_files,
                "skipped_files": summary.skipped_files,
                "wall_clock_seconds": round(summary.total_wall_clock_seconds, 2),
                "cumulative_duration_seconds": round(summary.cumulative_duration_seconds, 2),
                "workers": summary.worker_count,
                "status": "passed" if summary.is_success else "failed",
            },
            "slowest_files": [
                {"file": f, "duration_seconds": round(d, 2)}
                for f, d in summary.slowest_files
            ],
            "results": [
                {
                    "file": r.test_file,
                    "status": r.status.value if isinstance(r.status, Enum) else r.status,
                    "exit_code": r.exit_code,
                    "duration_seconds": round(r.duration_seconds, 2),
                    "stdout": r.stdout,
                    "stderr": r.stderr,
                }
                for r in summary.results
            ],
        }

    @classmethod
    def write_report(cls, summary: RunSummary, path: Path) -> None:
        """Write JSON summary report to disk."""
        path.parent.mkdir(parents=True, exist_ok=True)
        data = cls.to_dict(summary)
        path.write_text(json.dumps(data, indent=2), encoding="utf-8")


def _records_from_layout(layout: PytestArgvLayout) -> tuple[TargetRecord, ...]:
    """Create target records from a replayed layout."""
    return tuple(
        TargetRecord(
            raw_target=layout.pytest_argv[start],
            file_path=Path(layout.pytest_argv[start].split("::", 1)[0]),
            node_id=(
                layout.pytest_argv[start].split("::", 1)[1]
                if "::" in layout.pytest_argv[start]
                else None
            ),
            child_target=layout.pytest_argv[start],
            argv_span=(start, end),
            ordinal=index,
        )
        for index, (start, end) in enumerate(layout.positional_spans)
    )


def invalid_summary(error: RunnerValidationError, worker_count: int) -> RunSummary:
    """Build the fail-closed summary used for parser and discovery errors."""
    result = RunResult(
        kind="validation",
        status="invalid",
        target=error.raw_target,
        exit_code=2,
        duration_seconds=0.0,
        message=error.message,
        error_code=error.code,
    )
    return RunSummary(
        results=[result],
        scheduled_units=0,
        worker_count=worker_count,
        coverage_result=None,
        exit_code=2,
    )


def _log_run_completed(
    summary: RunSummary,
    *,
    run_id: str,
    duration_seconds: float | None = None,
    failure_phase: str | None = None,
    failure_code: str | None = None,
) -> None:
    """Emit the terminal lifecycle event for both dispatched and rejected runs."""
    wall_clock_seconds = (
        summary.total_wall_clock_seconds
        if duration_seconds is None
        else duration_seconds
    )
    cumulative_duration = summary.cumulative_duration_seconds
    speedup = (
        cumulative_duration / max(0.001, wall_clock_seconds)
        if wall_clock_seconds > 0
        else 1.0
    )
    logger.info(
        "parallel_test_run_completed run_id=%s total_files=%d passed=%d failed=%d "
        "skipped=%d scheduled_units=%d wall_clock_seconds=%.2f "
        "cumulative_duration_seconds=%.2f speedup=%.1f coverage_status=%s outcome=%s "
        "failure_phase=%s failure_code=%s",
        run_id,
        summary.total_files,
        summary.passed_files,
        summary.failed_files,
        summary.skipped_files,
        summary.scheduled_units if summary.scheduled_units is not None else 0,
        wall_clock_seconds,
        cumulative_duration,
        speedup,
        summary.coverage_result.status if summary.coverage_result is not None else "disabled",
        "passed" if summary.is_success else "failed",
        failure_phase or "none",
        failure_code or "none",
    )


def run_parallel_tests(config: RunnerConfig) -> RunSummary:
    """Main orchestration function executing test files across dynamic worker pool."""
    run_start_time = time.perf_counter()
    run_id = uuid4().hex[:12]
    config.run_id = run_id
    report_json = str(config.report_json_path) if config.report_json_path else ""
    target_selection = "explicit" if config.test_targets else "default"
    logger.info(
        "parallel_test_run_started run_id=%s workers=%d enable_coverage=%s report_json=%s "
        "target_selection=%s target_count=%d pytest_arg_count=%d worker_timeout=%s",
        run_id,
        config.workers,
        config.enable_coverage,
        report_json,
        target_selection,
        len(config.test_targets),
        len(config.pytest_args),
        config.worker_timeout,
    )
    _cleanup_root_coverage_fragments(config.repo_root, run_id=run_id)

    try:
        workers = _positive_int(str(config.workers), "--workers")
        if config.worker_timeout is None:
            timeout = None
        else:
            timeout = parse_worker_timeout(config.worker_timeout, "--worker-timeout")
        if config.pytest_argv:
            layout = PytestArgvLayout.from_project(
                config.repo_root, config.original_argv, config.runner_spans,
            )
            target_records = config.target_records or _records_from_layout(layout)
        else:
            legacy_argv = tuple(config.pytest_args) + tuple(config.test_targets)
            layout = PytestArgvLayout.from_project(config.repo_root, legacy_argv, ())
            target_records = _records_from_layout(layout)
        config.workers = workers
        config.worker_timeout = timeout
    except RunnerValidationError as error:
        _log_validation_failure(
            error,
            run_id=run_id,
            phase="configuration",
            worker_count=config.workers,
        )
        summary = invalid_summary(error, config.workers)
        if config.report_json_path:
            JsonReporter.write_report(summary, config.report_json_path)
        _cleanup_root_coverage_fragments(config.repo_root, run_id=run_id)
        _log_run_completed(
            summary,
            run_id=run_id,
            duration_seconds=time.perf_counter() - run_start_time,
            failure_phase="configuration",
            failure_code=error.code,
        )
        return summary

    logger.info(
        "test_discovery_started run_id=%s target_count=%d default_selection=%s",
        run_id,
        len(target_records),
        not target_records,
    )
    discovery = TestDiscovery().discover(
        repo_root=config.repo_root,
        target_records=target_records,
    )
    if discovery.errors or not discovery.units:
        first_error = discovery.errors[0] if discovery.errors else ValidationError(
            "empty_discovery", "no test files were discovered"
        )
        error = RunnerValidationError(first_error.code, first_error.message, first_error.raw_target)
        _log_validation_failure(
            error,
            run_id=run_id,
            phase="discovery",
            worker_count=config.workers,
        )
        summary = invalid_summary(error, config.workers)
        if config.report_json_path:
            JsonReporter.write_report(summary, config.report_json_path)
        _cleanup_root_coverage_fragments(config.repo_root, run_id=run_id)
        _log_run_completed(
            summary,
            run_id=run_id,
            duration_seconds=time.perf_counter() - run_start_time,
            failure_phase="discovery",
            failure_code=error.code,
        )
        return summary

    logger.info(
        "test_discovery_completed run_id=%s record_count=%d unit_count=%d",
        run_id,
        len(discovery.records),
        len(discovery.units),
    )

    cov_mgr: CoverageManager | None = None
    coverage_plan: CoveragePlan | None = None
    if config.enable_coverage:
        cov_dir = config.repo_root / ".coverage_parallel"
        cov_mgr = CoverageManager(config.repo_root, cov_dir, config.python_bin, run_id)
        coverage_sources = config.coverage_sources or tuple(
            arg.split("=", 1)[1]
            for arg in config.pytest_args
            if arg.startswith("--cov=")
        )
        coverage_request = CoverageRequest(
            source_override=coverage_sources or None,
            fail_under_override=config.coverage_fail_under,
            report_specs=config.coverage_reports,
        )
        try:
            coverage_plan = cov_mgr.prepare(request=coverage_request)
        except RunnerValidationError as error:
            _log_validation_failure(
                error,
                run_id=run_id,
                phase="coverage_prepare",
                worker_count=config.workers,
            )
            summary = invalid_summary(error, config.workers)
            if config.report_json_path:
                JsonReporter.write_report(summary, config.report_json_path)
            _cleanup_root_coverage_fragments(config.repo_root, run_id=run_id)
            _log_run_completed(
                summary,
                run_id=run_id,
                duration_seconds=time.perf_counter() - run_start_time,
                failure_phase="coverage_prepare",
                failure_code=error.code,
            )
            return summary

    executor = SubprocessTestExecutor(config)
    units = discovery.units
    total_files = len(units)
    results: list[RunResult] = []

    start_wall_clock = time.perf_counter()

    logger.info(
        "test_worker_pool_started run_id=%s workers=%d scheduled_units=%d",
        run_id,
        config.workers,
        total_files,
    )
    with concurrent.futures.ThreadPoolExecutor(max_workers=config.workers) as pool:
        future_to_unit = {
            pool.submit(
                executor.run_dispatch_unit,
                unit=unit,
                layout=layout,
                all_target_records=discovery.records,
                index=i + 1,
                total=total_files,
                coverage_plan=coverage_plan,
            ): (i + 1, unit)
            for i, unit in enumerate(units)
        }
        completed_count = 0
        for future in concurrent.futures.as_completed(future_to_unit):
            completed_count += 1
            res = future.result()
            results.append(res)
            print(  # noqa: T201
                f"[{completed_count:>3}/{total_files:<3}] {res.test_file} ... "
                f"{str(res.status).upper()} ({res.duration_seconds:.2f}s)",
                flush=True,
            )
            logger.info(
                "test_file_completed run_id=%s file=%s status=%s exit_code=%d "
                "duration_seconds=%.2f progress=%d/%d",
                run_id,
                res.test_file,
                res.status,
                res.exit_code,
                res.duration_seconds,
                completed_count,
                total_files,
            )

    wall_clock_seconds = time.perf_counter() - start_wall_clock
    logger.info(
        "test_worker_pool_completed run_id=%s completed_units=%d duration_seconds=%.2f",
        run_id,
        len(results),
        wall_clock_seconds,
    )
    cumulative_duration = sum(r.duration_seconds for r in results)
    passed_count = sum(1 for r in results if r.status == "passed")
    failed_count = sum(
        1
        for r in results
        if r.status in ("failed", "timed_out")
    )
    skipped_count = sum(1 for r in results if r.status == "skipped")

    slowest = sorted(
        [(r.test_file, r.duration_seconds) for r in results],
        key=lambda x: x[1],
        reverse=True,
    )[:5]

    coverage_result: RunResult | None = None
    if cov_mgr is not None and coverage_plan is not None:
        try:
            combine_result = cov_mgr.combine(plan=coverage_plan)
            coverage_result = combine_result
            if combine_result.status == "passed":
                coverage_result = cov_mgr.report(plan=coverage_plan)
            if coverage_result.message:
                print("\n" + coverage_result.message, flush=True)  # noqa: T201
            if coverage_result.status != "passed":
                if coverage_result.error_code == "coverage_threshold":
                    logger.warning(
                        "coverage_threshold_failed run_id=%s fail_under=%s exit_code=%d "
                        "duration_seconds=%.2f",
                        run_id,
                        coverage_plan.fail_under,
                        coverage_result.exit_code,
                        coverage_result.duration_seconds,
                    )
                failed_count += 1
        finally:
            cov_mgr.cleanup_root_fragments()

    failed_results = [
        r for r in results if r.status in ("failed", "timed_out")
    ]
    if failed_results:
        sep = "=" * 80
        print(f"\n{sep[:35]} FAILURES {sep[:35]}", flush=True)  # noqa: T201
        for r in failed_results:
            if r.status == "timed_out":
                logger.error(
                    "test_file_timed_out run_id=%s file=%s exit_code=%d "
                    "duration_seconds=%.2f",
                    run_id,
                    r.test_file,
                    r.exit_code,
                    r.duration_seconds,
                )
            else:
                logger.error(
                    "test_file_failed run_id=%s file=%s exit_code=%d duration_seconds=%.2f",
                    run_id,
                    r.test_file,
                    r.exit_code,
                    r.duration_seconds,
                )
            title = f" FAILURES: {r.test_file} "
            pad_left = (80 - len(title)) // 2
            pad_right = 80 - len(title) - pad_left
            print(f"{'_' * pad_left}{title}{'_' * pad_right}", flush=True)  # noqa: T201
            if r.stdout.strip():
                print(r.stdout.strip(), flush=True)  # noqa: T201
            if r.stderr.strip():
                print(r.stderr.strip(), flush=True)  # noqa: T201
        print(sep, flush=True)  # noqa: T201

    if slowest:
        sep = "=" * 80
        print(f"\n{sep[:30]} TOP 5 SLOWEST FILES {sep[:30]}", flush=True)  # noqa: T201
        for rank, (file_name, dur) in enumerate(slowest, 1):
            print(f"{rank}. {file_name} ({dur:.2f}s)", flush=True)  # noqa: T201
            logger.log(
                NOTICE,
                "slowest_test_file rank=%d file=%s duration_seconds=%.2f",
                rank,
                file_name,
                dur,
            )

    sep = "=" * 80
    print(f"\n{sep[:35]} SUMMARY {sep[:36]}", flush=True)  # noqa: T201
    speedup = (
        cumulative_duration / max(0.001, wall_clock_seconds)
        if wall_clock_seconds > 0
        else 1.0
    )
    print(  # noqa: T201
        f"Total Files: {total_files} | Passed: {passed_count} | "
        f"Failed: {failed_count} | Skipped: {skipped_count}\n"
        f"Wall-clock duration: {wall_clock_seconds:.2f}s | "
        f"Cumulative CPU duration: {cumulative_duration:.2f}s ({speedup:.1f}x speedup)",
        flush=True,
    )
    summary = RunSummary(
        total_files=total_files,
        passed_files=passed_count,
        failed_files=failed_count,
        skipped_files=skipped_count,
        total_wall_clock_seconds=wall_clock_seconds,
        cumulative_duration_seconds=cumulative_duration,
        worker_count=config.workers,
        slowest_files=slowest,
        results=results,
        scheduled_units=total_files,
        coverage_result=coverage_result,
        exit_code=0 if failed_count == 0 else 1,
    )

    _cleanup_root_coverage_fragments(config.repo_root, run_id=run_id)
    _log_run_completed(summary, run_id=run_id)

    if config.report_json_path:
        JsonReporter.write_report(summary, config.report_json_path)
        logger.info("json_report_written run_id=%s path=%s", run_id, config.report_json_path)

    return summary


def main(
    args: Sequence[str] | None = None,
    repo_root: Path | None = None,
) -> int:
    """CLI main entry point returning 0 on success or 1 on failure."""
    if args is None:
        args = sys.argv[1:]
    if repo_root is None:
        repo_root = Path.cwd()

    _configure_logging()
    run_start_time = time.perf_counter()
    run_id = uuid4().hex[:12]
    parser = CLIParser()
    try:
        config = parser.parse_args(args=args, repo_root=repo_root)
    except RunnerValidationError as error:
        _log_validation_failure(
            error,
            run_id=run_id,
            phase="cli_parse",
            worker_count=None,
        )
        summary = invalid_summary(error, worker_count=0)
        _cleanup_root_coverage_fragments(repo_root, run_id=run_id)
        _log_run_completed(
            summary,
            run_id=run_id,
            duration_seconds=time.perf_counter() - run_start_time,
            failure_phase="cli_parse",
            failure_code=error.code,
        )
        print(f"parallel runner configuration error: {error.message}", file=sys.stderr)
        return 2
    summary = run_parallel_tests(config)
    return 0 if summary.is_success else 1


if __name__ == "__main__":
    sys.exit(main())
