"""PYPOST-984: `make check-lock` retry/messaging/cleanup contract (offline, fake uv).

All tests drive the real `Makefile` `check-lock` target via `subprocess`, substituting
a fake `uv` executable through the target's existing `UV ?= uv` override (see
`tests/test_makefile.py` for the sibling `make_workspace` fixture pattern). No network
access or real `uv` binary is required.
"""

from __future__ import annotations

import os
import shutil
import stat
import subprocess
from pathlib import Path

import pytest

pytestmark = pytest.mark.timeout(30)

REPO_ROOT = Path(__file__).resolve().parents[1]
MAKEFILE = REPO_ROOT / "Makefile"

_REQUIREMENTS_IN = "# fake production requirements source (PYPOST-984 test fixture)\nfoo\n"
_REQUIREMENTS_HEADER = "# seeded uv header line 1\n# seeded uv header line 2\n"
_REQUIREMENTS_BODY = "foo==1.0\n"
_REQUIREMENTS_TXT = _REQUIREMENTS_HEADER + _REQUIREMENTS_BODY

_FAKE_UV_SCRIPT = '''#!/usr/bin/env python3
"""Fake uv for offline check-lock tests (PYPOST-984).

Records its invocation count to $FAKE_UV_COUNTER_FILE and can be configured (via env
vars) to fail its first N invocations before succeeding, or to always fail.
"""
import os
import pathlib
import sys


def main() -> int:
    args = sys.argv[1:]
    out_path = None
    for index, arg in enumerate(args):
        if arg == "-o" and index + 1 < len(args):
            out_path = args[index + 1]

    counter_file = pathlib.Path(os.environ["FAKE_UV_COUNTER_FILE"])
    count = int(counter_file.read_text()) if counter_file.exists() else 0
    count += 1
    counter_file.write_text(str(count))

    fail_count = int(os.environ.get("FAKE_UV_FAIL_COUNT", "0"))
    always_fail = os.environ.get("FAKE_UV_ALWAYS_FAIL") == "1"
    should_fail = always_fail or count <= fail_count

    if should_fail:
        if out_path and os.environ.get("FAKE_UV_LEAVE_PARTIAL_OUTPUT") == "1":
            pathlib.Path(out_path).write_text("partial-fake-uv-output\\n")
        sys.stderr.write("fake-uv: simulated uv pip compile failure\\n")
        return 1

    if out_path:
        header = "# fake uv header line 1\\n# fake uv header line 2\\n"
        body = os.environ.get("FAKE_UV_OUTPUT_BODY", "")
        pathlib.Path(out_path).write_text(header + body)
    return 0


if __name__ == "__main__":
    sys.exit(main())
'''

_SCRATCH_FILE_NAMES = (
    "requirements.txt.check",
    "requirements.txt.body",
    "requirements.txt.check.body",
)


def _write_fake_uv(workspace: Path) -> Path:
    script = workspace / "fake_uv.py"
    script.write_text(_FAKE_UV_SCRIPT, encoding="utf-8")
    script.chmod(script.stat().st_mode | stat.S_IEXEC | stat.S_IXGRP | stat.S_IXOTH)
    return script


def _run_check_lock(
    workspace: Path,
    fake_uv: Path,
    *,
    extra_env: dict[str, str],
    timeout: int = 20,
) -> subprocess.CompletedProcess[str]:
    env = os.environ.copy()
    env.pop("PYTEST_ARGS", None)
    counter_file = workspace / "fake_uv_calls.count"
    counter_file.unlink(missing_ok=True)
    env["FAKE_UV_COUNTER_FILE"] = str(counter_file)
    env.update(extra_env)
    return subprocess.run(
        ["make", "check-lock", f"UV={fake_uv}"],
        cwd=workspace,
        capture_output=True,
        text=True,
        timeout=timeout,
        env=env,
        check=False,
    )


def _combined_output(proc: subprocess.CompletedProcess[str]) -> str:
    return f"{proc.stdout}\n{proc.stderr}"


def _scratch_files(workspace: Path) -> list[Path]:
    return [workspace / name for name in _SCRATCH_FILE_NAMES if (workspace / name).exists()]


@pytest.fixture
def check_lock_workspace(tmp_path: Path) -> Path:
    shutil.copy(MAKEFILE, tmp_path / "Makefile")
    (tmp_path / "requirements.in").write_text(_REQUIREMENTS_IN, encoding="utf-8")
    (tmp_path / "requirements.txt").write_text(_REQUIREMENTS_TXT, encoding="utf-8")
    return tmp_path


class TestCheckLockRetriesTransientFailure:
    """A one-off uv/network blip must not fail the gate outright."""

    def test_recovers_after_two_transient_failures(
        self,
        check_lock_workspace: Path,
    ) -> None:
        fake_uv = _write_fake_uv(check_lock_workspace)
        result = _run_check_lock(
            check_lock_workspace,
            fake_uv,
            extra_env={
                "FAKE_UV_FAIL_COUNT": "2",
                "FAKE_UV_OUTPUT_BODY": _REQUIREMENTS_BODY,
            },
        )
        assert result.returncode == 0, (
            "make check-lock must retry transient uv pip compile failures and "
            f"still succeed once uv recovers; got:\n{_combined_output(result)}"
        )


class TestCheckLockReportsExhaustedCompileFailure:
    """Exhausted retries must report distinctly and clean up scratch files."""

    def test_always_failing_uv_reports_distinct_message(
        self,
        check_lock_workspace: Path,
    ) -> None:
        fake_uv = _write_fake_uv(check_lock_workspace)
        result = _run_check_lock(
            check_lock_workspace,
            fake_uv,
            extra_env={
                "FAKE_UV_ALWAYS_FAIL": "1",
                "FAKE_UV_LEAVE_PARTIAL_OUTPUT": "1",
            },
        )
        output = _combined_output(result)
        assert result.returncode != 0, (
            f"make check-lock must fail when uv pip compile never succeeds; got:\n{output}"
        )
        assert "compile failed" in output.lower() and "attempt" in output.lower(), (
            "make check-lock must emit a distinct 'uv pip compile failed after N "
            f"attempts' message when retries are exhausted; got:\n{output}"
        )
        assert "differ" not in output.lower(), (
            f"an exhausted-compile failure must not read like a diff mismatch; got:\n{output}"
        )

    def test_always_failing_uv_leaves_no_scratch_files(
        self,
        check_lock_workspace: Path,
    ) -> None:
        fake_uv = _write_fake_uv(check_lock_workspace)
        _run_check_lock(
            check_lock_workspace,
            fake_uv,
            extra_env={
                "FAKE_UV_ALWAYS_FAIL": "1",
                "FAKE_UV_LEAVE_PARTIAL_OUTPUT": "1",
            },
        )
        leftovers = _scratch_files(check_lock_workspace)
        assert not leftovers, (
            "make check-lock must clean up requirements.txt.check/.body scratch "
            f"files even when uv pip compile fails; left behind: {leftovers}"
        )


class TestCheckLockStillCatchesGenuineDrift:
    """Regression guard: retry/messaging changes must not mask real drift."""

    def test_genuine_mismatch_still_fails_with_distinct_message(
        self,
        check_lock_workspace: Path,
    ) -> None:
        fake_uv = _write_fake_uv(check_lock_workspace)
        result = _run_check_lock(
            check_lock_workspace,
            fake_uv,
            extra_env={"FAKE_UV_OUTPUT_BODY": "foo==2.0\n"},
        )
        output = _combined_output(result)
        assert result.returncode != 0, (
            f"make check-lock must still fail on genuine lock drift; got:\n{output}"
        )
        assert "stale" in output.lower(), (
            "make check-lock must report genuine drift with a distinct 'stale' lock "
            f"message rather than raw diff -q output; got:\n{output}"
        )
        assert "compile failed" not in output.lower(), (
            f"a genuine diff mismatch must not be reported as a compile failure; got:\n{output}"
        )
