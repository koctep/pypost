"""Integration tests for virtualenv otel extra stamp idempotency.

Covers PYPOST-905, PYPOST-1262.
"""

from __future__ import annotations

from pathlib import Path

import pytest

from tests.makefile_test_helpers import (
    VENV_OTEL_STAMP_NAME,
    VENV_OTEL_STAMP_REL,
    _assert_no_pip_install,
    _assert_pip_install_extra,
    _combined_output,
    _make_stamp_stale,
    _prerequisites,
    _run_make,
    make_workspace,
)

pytestmark = pytest.mark.timeout(60)


class TestVenvOtelStampIdempotency:
    """PYPOST-905: skip pip when otel stamp current; install when missing/stale."""

    @pytest.mark.timeout(60)
    def test_venv_otel_skips_pip_when_current(self, make_workspace: Path) -> None:
        venv = _run_make(make_workspace, "venv")
        assert venv.returncode == 0, venv.stderr
        first = _run_make(make_workspace, "venv-otel")
        assert first.returncode == 0, first.stderr
        second = _run_make(make_workspace, "venv-otel")
        assert second.returncode == 0, second.stderr
        _assert_no_pip_install(_combined_output(second))

    @pytest.mark.timeout(60)
    def test_venv_otel_installs_when_stamp_missing(
        self,
        make_workspace: Path,
    ) -> None:
        stamp = make_workspace / ".venv" / VENV_OTEL_STAMP_NAME
        venv = _run_make(make_workspace, "venv")
        assert venv.returncode == 0, venv.stderr
        if stamp.exists():
            stamp.unlink()
        result = _run_make(make_workspace, "venv-otel")
        assert result.returncode == 0, result.stderr
        _assert_pip_install_extra(_combined_output(result), ".[otel]")

    @pytest.mark.timeout(60)
    def test_venv_otel_installs_when_stamp_stale(
        self,
        make_workspace: Path,
    ) -> None:
        venv = _run_make(make_workspace, "venv")
        assert venv.returncode == 0, venv.stderr
        result = _run_make(make_workspace, "venv-otel")
        assert result.returncode == 0, result.stderr
        _make_stamp_stale(make_workspace, VENV_OTEL_STAMP_NAME)
        revisit = _run_make(make_workspace, "venv-otel")
        assert revisit.returncode == 0, revisit.stderr
        _assert_pip_install_extra(_combined_output(revisit), ".[otel]")

    @pytest.mark.timeout(60)
    def test_venv_otel_depends_on_stamp(self, make_workspace: Path) -> None:
        prereqs = _prerequisites(make_workspace, "venv-otel")
        assert VENV_OTEL_STAMP_REL in prereqs
