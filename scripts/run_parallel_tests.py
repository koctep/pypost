"""Parallel test runner orchestrator for PyPost (PYPOST-1149)."""

from __future__ import annotations

import concurrent.futures
import json
import logging
import os
import shutil
import signal
import subprocess
import sys
import time
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import Any, Sequence
from uuid import uuid4

NOTICE = 25
logging.addLevelName(NOTICE, "NOTICE")

logger = logging.getLogger(__name__)


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


@dataclass(frozen=True)
class TestResult:
    """Outcome and captured output from running a single test file."""

    __test__ = False

    test_file: str
    status: TestStatus
    exit_code: int
    duration_seconds: float
    stdout: str
    stderr: str


@dataclass
class RunSummary:
    """Consolidated summary across all parallel test file executions."""

    total_files: int
    passed_files: int
    failed_files: int
    skipped_files: int
    total_wall_clock_seconds: float
    cumulative_duration_seconds: float
    worker_count: int
    slowest_files: list[tuple[str, float]]
    results: list[TestResult] = field(default_factory=list)

    @property
    def is_success(self) -> bool:
        """Return True if all test files passed or skipped with zero failures."""
        return self.failed_files == 0


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
    worker_timeout: float = 30.0


def default_worker_count() -> int:
    """Return tuned default worker count for subprocess pytest parallelism.

    Policy (PYPOST-1154): modest oversubscription for I/O-bound per-file subprocesses,
    with a ceiling to limit memory pressure from concurrent Qt-heavy workers.
    """
    cpu = max(1, os.cpu_count() or 4)
    return min(cpu + 2, 16)


def get_worker_count(cli_workers: int | None = None) -> int:
    """Determine effective worker count following precedence rules.

    Precedence:
    1. Explicit CLI argument (--workers / -n)
    2. WORKERS environment variable
    3. PYTEST_WORKERS environment variable
    4. default_worker_count()
    """
    if cli_workers is not None and cli_workers > 0:
        return cli_workers

    workers_env = os.environ.get("WORKERS") or os.environ.get("PYTEST_WORKERS")
    if workers_env:
        try:
            val = int(workers_env.strip())
            if val > 0:
                return val
        except ValueError:
            pass

    return default_worker_count()


DEFAULT_WORKER_TIMEOUT = 30.0


def get_worker_timeout(cli_timeout: float | None = None) -> float:
    """Determine effective per-worker timeout following precedence rules.

    Precedence:
    1. Explicit CLI argument (--worker-timeout)
    2. WORKER_TIMEOUT environment variable
    3. DEFAULT_WORKER_TIMEOUT (30 seconds)
    """
    if cli_timeout is not None and cli_timeout > 0:
        return cli_timeout

    timeout_env = os.environ.get("WORKER_TIMEOUT")
    if timeout_env:
        try:
            val = float(timeout_env.strip())
            if val > 0:
                return val
        except ValueError:
            pass

    return DEFAULT_WORKER_TIMEOUT


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

        cli_workers: int | None = None
        cli_worker_timeout: float | None = None
        enable_coverage = False
        report_json_path: Path | None = None
        test_targets: list[str] = []
        pytest_args: list[str] = []

        i = 0
        while i < len(args):
            arg = args[i]
            if arg in ("-n", "--workers"):
                if i + 1 < len(args):
                    cli_workers = int(args[i + 1])
                    i += 2
                else:
                    i += 1
            elif arg.startswith("--workers="):
                cli_workers = int(arg.split("=", 1)[1])
                i += 1
            elif arg.startswith("-n") and len(arg) > 2 and arg[2:].isdigit():
                cli_workers = int(arg[2:])
                i += 1
            elif arg == "--worker-timeout":
                if i + 1 < len(args):
                    cli_worker_timeout = float(args[i + 1])
                    i += 2
                else:
                    i += 1
            elif arg.startswith("--worker-timeout="):
                cli_worker_timeout = float(arg.split("=", 1)[1])
                i += 1
            elif arg == "--cov":
                enable_coverage = True
                i += 1
            elif arg.startswith("--cov="):
                enable_coverage = True
                pytest_args.append(arg)
                i += 1
            elif arg == "--report-json":
                if i + 1 < len(args):
                    report_json_path = Path(args[i + 1])
                    i += 2
                else:
                    i += 1
            elif arg.startswith("--report-json="):
                report_json_path = Path(arg.split("=", 1)[1])
                i += 1
            elif arg in (
                "-k",
                "-m",
                "-o",
                "-c",
                "-W",
                "--override-ini",
                "--ignore",
                "--deselect",
                "--tb",
                "--capture",
                "--color",
                "--maxfail",
            ):
                pytest_args.append(arg)
                if i + 1 < len(args):
                    pytest_args.append(args[i + 1])
                    i += 2
                else:
                    i += 1
            elif arg.startswith("-"):
                pytest_args.append(arg)
                i += 1
            else:
                test_targets.append(arg)
                i += 1

        workers = get_worker_count(cli_workers)
        worker_timeout = get_worker_timeout(cli_worker_timeout)
        python_bin = Path(sys.executable)

        return RunnerConfig(
            workers=workers,
            enable_coverage=enable_coverage,
            report_json_path=report_json_path,
            test_targets=test_targets,
            pytest_args=pytest_args,
            repo_root=repo_root,
            python_bin=python_bin,
            worker_timeout=worker_timeout,
        )


class TestDiscovery:
    """Discovers test files from explicit paths or workspace scanning."""

    __test__ = False

    @staticmethod
    def discover_test_files(repo_root: Path, targets: list[str]) -> list[Path]:
        """Resolve candidate test files from targets or scanning tests/."""
        discovered: list[Path] = []

        if not targets:
            default_tests = repo_root / "tests"
            if default_tests.is_dir():
                discovered.extend(sorted(default_tests.glob("test_*.py")))
            return [p.resolve() for p in discovered if p.is_file()]

        for target in targets:
            target_path = Path(target)
            if not target_path.is_absolute():
                target_path = repo_root / target

            if target_path.is_dir():
                discovered.extend(sorted(target_path.glob("test_*.py")))
            elif target_path.is_file():
                discovered.append(target_path)
            else:
                matching = sorted(repo_root.glob(target))
                if matching:
                    discovered.extend([p for p in matching if p.is_file()])
                elif (repo_root / target).exists():
                    discovered.append(repo_root / target)

        seen: set[Path] = set()
        result: list[Path] = []
        for p in discovered:
            resolved = p.resolve()
            if resolved not in seen and resolved.is_file():
                if resolved.name.startswith("test_") and resolved.name.endswith(".py"):
                    seen.add(resolved)
                    result.append(resolved)
                elif any(Path(t).resolve() == resolved for t in targets if Path(t).exists()):
                    seen.add(resolved)
                    result.append(resolved)

        return result


def kill_process_group(pid: int) -> None:
    """Terminate a process group cleanly on POSIX systems with Windows fallback."""
    if sys.platform == "win32":
        try:
            os.kill(pid, signal.SIGTERM)
        except (ProcessLookupError, PermissionError, OSError) as exc:
            logger.debug("kill_process_group win32 failed for pid=%s: %s", pid, exc)
        return

    try:
        try:
            pgid = os.getpgid(pid)
        except (ProcessLookupError, OSError) as exc:
            logger.debug(
                "kill_process_group getpgid failed for pid=%s: %s; falling back to pgid=pid",
                pid,
                exc,
            )
            pgid = pid
        logger.debug("kill_process_group sending SIGKILL to pgid=%s for pid=%s", pgid, pid)
        os.killpg(pgid, signal.SIGKILL)
    except (ProcessLookupError, PermissionError, OSError) as exc:
        logger.debug("kill_process_group killpg failed for pgid=%s: %s", pgid, exc)


class SubprocessTestExecutor:
    """Executes a single test file in an isolated OS subprocess with QT_QPA_PLATFORM=offscreen."""

    def __init__(self, config: RunnerConfig, cov_dir: Path | None = None) -> None:
        self.config = config
        self.cov_dir = cov_dir

    def run_test_file(self, test_file: Path, index: int, total: int) -> TestResult:
        """Run one test file and capture duration, exit code, stdout, and stderr."""
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
            str(test_file),
        ]
        cmd.extend(self.config.pytest_args)

        if self.cov_dir is not None:
            cov_file = self.cov_dir / f".coverage.worker_{index}_{uuid4().hex}"
            env["COVERAGE_FILE"] = str(cov_file)
            if not any(arg.startswith("--cov") for arg in self.config.pytest_args):
                cmd.append("--cov=pypost")
            cmd.extend(["--cov-report=", "--cov-fail-under=0"])

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
            stdout, stderr = proc.communicate(timeout=self.config.worker_timeout)
        except subprocess.TimeoutExpired:
            duration = time.perf_counter() - start_time
            kill_process_group(proc.pid)
            try:
                proc.kill()
            except (ProcessLookupError, OSError):
                pass
            stdout, stderr = proc.communicate()
            stdout_str = stdout or ""
            stderr_str = stderr or ""
            try:
                rel_file = str(test_file.relative_to(self.config.repo_root))
            except ValueError:
                rel_file = str(test_file)
            timeout_note = (
                f"worker timed out after {self.config.worker_timeout}s"
            )
            stderr_str = f"{stderr_str}\n{timeout_note}".strip()
            logger.warning(
                "worker_timeout file=%s timeout_seconds=%s",
                rel_file,
                self.config.worker_timeout,
            )
            return TestResult(
                test_file=rel_file,
                status=TestStatus.TIMED_OUT,
                exit_code=-9,
                duration_seconds=duration,
                stdout=stdout_str,
                stderr=stderr_str,
            )
        duration = time.perf_counter() - start_time

        if proc.returncode == 0:
            status = TestStatus.PASSED
        elif proc.returncode == 5:
            # Pytest exit code 5: no tests collected (e.g. due to -k or -m filter)
            status = TestStatus.SKIPPED
        else:
            status = TestStatus.FAILED

        try:
            rel_file = str(test_file.relative_to(self.config.repo_root))
        except ValueError:
            rel_file = str(test_file)

        return TestResult(
            test_file=rel_file,
            status=status,
            exit_code=proc.returncode if proc.returncode is not None else 1,
            duration_seconds=duration,
            stdout=stdout or "",
            stderr=stderr or "",
        )


class CoverageManager:
    """Manages parallel worker coverage databases and runs aggregation."""

    def __init__(
        self,
        repo_root: Path,
        cov_dir: Path,
        python_bin: Path | None = None,
    ) -> None:
        self.repo_root = repo_root
        self.cov_dir = cov_dir
        self.python_bin = python_bin or Path(sys.executable)

    def prepare(self) -> None:
        """Create fresh coverage temp directory and remove stale root .coverage."""
        if self.cov_dir.exists():
            shutil.rmtree(self.cov_dir)
        self.cov_dir.mkdir(parents=True, exist_ok=True)

        root_cov = self.repo_root / ".coverage"
        if root_cov.exists():
            try:
                root_cov.unlink()
            except OSError:
                pass

    def get_env_for_worker(self, worker_id: int) -> dict[str, str]:
        """Return environment variables for a worker subprocess."""
        cov_file = self.cov_dir / f".coverage.worker_{worker_id}_{uuid4().hex}"
        return {"COVERAGE_FILE": str(cov_file)}

    def combine_and_report(self, fail_under: int = 70) -> tuple[bool, str]:
        """Combine collected coverage files and generate terminal & HTML reports."""
        cov_files = list(self.cov_dir.glob(".coverage*"))
        if not cov_files:
            return True, "No coverage data files collected."

        output_parts: list[str] = []

        combine_cmd = [str(self.python_bin), "-m", "coverage", "combine"] + [
            str(f) for f in cov_files
        ]
        combine_proc = subprocess.run(
            combine_cmd,
            cwd=str(self.repo_root),
            capture_output=True,
            text=True,
        )
        if combine_proc.stdout.strip():
            output_parts.append(combine_proc.stdout.strip())
        if combine_proc.stderr.strip():
            output_parts.append(combine_proc.stderr.strip())

        report_cmd = [str(self.python_bin), "-m", "coverage", "report", "-m"]
        if fail_under > 0:
            report_cmd.append(f"--fail-under={fail_under}")
        report_proc = subprocess.run(
            report_cmd,
            cwd=str(self.repo_root),
            capture_output=True,
            text=True,
        )
        if report_proc.stdout.strip():
            output_parts.append(report_proc.stdout.strip())
        if report_proc.stderr.strip():
            output_parts.append(report_proc.stderr.strip())

        html_cmd = [str(self.python_bin), "-m", "coverage", "html", "-d", "htmlcov"]
        html_proc = subprocess.run(
            html_cmd,
            cwd=str(self.repo_root),
            capture_output=True,
            text=True,
        )
        if html_proc.stdout.strip():
            output_parts.append(html_proc.stdout.strip())
        if html_proc.stderr.strip():
            output_parts.append(html_proc.stderr.strip())

        success = combine_proc.returncode == 0 and report_proc.returncode == 0
        return success, "\n".join(output_parts)


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
                    "status": r.status.value,
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


def run_parallel_tests(config: RunnerConfig) -> RunSummary:
    """Main orchestration function executing test files across dynamic worker pool."""
    report_json = str(config.report_json_path) if config.report_json_path else ""
    test_targets = ",".join(config.test_targets) if config.test_targets else "tests/"
    logger.info(
        "parallel_test_run_started workers=%d enable_coverage=%s report_json=%s "
        "test_targets=%s pytest_arg_count=%d worker_timeout=%s",
        config.workers,
        config.enable_coverage,
        report_json,
        test_targets,
        len(config.pytest_args),
        config.worker_timeout,
    )

    test_files = TestDiscovery.discover_test_files(config.repo_root, config.test_targets)

    if not test_files:
        logger.warning("no_test_files_discovered test_targets=%s", test_targets)
        summary = RunSummary(
            total_files=0,
            passed_files=0,
            failed_files=0,
            skipped_files=0,
            total_wall_clock_seconds=0.0,
            cumulative_duration_seconds=0.0,
            worker_count=config.workers,
            slowest_files=[],
            results=[],
        )
        if config.report_json_path:
            JsonReporter.write_report(summary, config.report_json_path)
            logger.info("json_report_written path=%s", config.report_json_path)
        return summary

    cov_dir: Path | None = None
    cov_mgr: CoverageManager | None = None
    if config.enable_coverage:
        cov_dir = config.repo_root / ".coverage_parallel"
        cov_mgr = CoverageManager(config.repo_root, cov_dir, config.python_bin)
        cov_mgr.prepare()

    executor = SubprocessTestExecutor(config, cov_dir=cov_dir)
    total_files = len(test_files)
    results: list[TestResult] = []

    start_wall_clock = time.perf_counter()

    with concurrent.futures.ThreadPoolExecutor(max_workers=config.workers) as pool:
        future_to_file = {
            pool.submit(executor.run_test_file, f, i + 1, total_files): (i + 1, f)
            for i, f in enumerate(test_files)
        }
        completed_count = 0
        for future in concurrent.futures.as_completed(future_to_file):
            completed_count += 1
            res = future.result()
            results.append(res)
            print(  # noqa: T201
                f"[{completed_count:>3}/{total_files:<3}] {res.test_file} ... "
                f"{res.status.value.upper()} ({res.duration_seconds:.2f}s)",
                flush=True,
            )
            logger.info(
                "test_file_completed file=%s status=%s exit_code=%d duration_seconds=%.2f "
                "progress=%d/%d",
                res.test_file,
                res.status.value,
                res.exit_code,
                res.duration_seconds,
                completed_count,
                total_files,
            )

    wall_clock_seconds = time.perf_counter() - start_wall_clock
    cumulative_duration = sum(r.duration_seconds for r in results)
    passed_count = sum(1 for r in results if r.status == TestStatus.PASSED)
    failed_count = sum(
        1
        for r in results
        if r.status in (TestStatus.FAILED, TestStatus.TIMED_OUT)
    )
    skipped_count = sum(1 for r in results if r.status == TestStatus.SKIPPED)

    slowest = sorted(
        [(r.test_file, r.duration_seconds) for r in results],
        key=lambda x: x[1],
        reverse=True,
    )[:5]

    cov_success = True
    if cov_mgr is not None:
        fail_under = 70
        for arg in config.pytest_args:
            if arg.startswith("--cov-fail-under="):
                try:
                    fail_under = int(arg.split("=", 1)[1])
                except ValueError:
                    pass
        cov_success, cov_out = cov_mgr.combine_and_report(fail_under=fail_under)
        if cov_out:
            print("\n" + cov_out, flush=True)  # noqa: T201
        if not cov_success:
            logger.warning(
                "coverage_threshold_failed fail_under=%d",
                fail_under,
            )
            failed_count += 1
        else:
            logger.info("coverage_report_completed fail_under=%d", fail_under)

    failed_results = [
        r for r in results if r.status in (TestStatus.FAILED, TestStatus.TIMED_OUT)
    ]
    if failed_results:
        sep = "=" * 80
        print(f"\n{sep[:35]} FAILURES {sep[:35]}", flush=True)  # noqa: T201
        for r in failed_results:
            if r.status == TestStatus.TIMED_OUT:
                logger.error(
                    "test_file_timed_out file=%s exit_code=%d duration_seconds=%.2f",
                    r.test_file,
                    r.exit_code,
                    r.duration_seconds,
                )
            else:
                logger.error(
                    "test_file_failed file=%s exit_code=%d duration_seconds=%.2f",
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
    logger.info(
        "parallel_test_run_completed total_files=%d passed=%d failed=%d skipped=%d "
        "wall_clock_seconds=%.2f cumulative_duration_seconds=%.2f speedup=%.1f",
        total_files,
        passed_count,
        failed_count,
        skipped_count,
        wall_clock_seconds,
        cumulative_duration,
        speedup,
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
    )

    if config.report_json_path:
        JsonReporter.write_report(summary, config.report_json_path)
        logger.info("json_report_written path=%s", config.report_json_path)

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
    parser = CLIParser()
    config = parser.parse_args(args=args, repo_root=repo_root)
    summary = run_parallel_tests(config)
    return 0 if summary.is_success else 1


if __name__ == "__main__":
    sys.exit(main())
