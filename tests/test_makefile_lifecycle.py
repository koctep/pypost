"""Integration tests for virtualenv marker and stamp lifecycle.

Covers PYPOST-274, PYPOST-905, PYPOST-929.
"""

from __future__ import annotations

from pathlib import Path

import pytest

from tests.makefile_test_helpers import (
    MARKER_NAME,
    VENV_OTEL_STAMP_NAME,
    VENV_OTEL_STAMP_REL,
    VENV_TEST_STAMP_NAME,
    VENV_TEST_STAMP_REL,
    _assert_no_pip_install,
    _assert_pip_install_extra,
    _combined_output,
    _make_stamp_stale,
    _prerequisites,
    _run_make,
    make_workspace,
)

pytestmark = pytest.mark.timeout(60)


class TestMarkerLifecycle:
    def test_venv_creates_version_marker(self, make_workspace: Path) -> None:
        result = _run_make(make_workspace, "venv")
        assert result.returncode == 0, result.stderr
        marker = make_workspace / ".venv" / MARKER_NAME
        assert marker.is_file()

    def test_clean_removes_venv_and_marker(self, make_workspace: Path) -> None:
        _run_make(make_workspace, "venv", check=False)
        result = _run_make(make_workspace, "clean")
        assert result.returncode == 0, result.stderr
        assert not (make_workspace / ".venv").exists()

    def test_venv_is_idempotent(self, make_workspace: Path) -> None:
        first = _run_make(make_workspace, "venv")
        second = _run_make(make_workspace, "venv")
        assert first.returncode == 0, first.stderr
        assert second.returncode == 0, second.stderr
        assert (make_workspace / ".venv" / MARKER_NAME).is_file()


class TestVenvExtraStampIdempotency:
    """PYPOST-905: skip pip when stamp current; install when missing/stale."""

    def test_venv_test_skips_pip_when_current(self, make_workspace: Path) -> None:
        venv = _run_make(make_workspace, "venv")
        assert venv.returncode == 0, venv.stderr
        first = _run_make(make_workspace, "venv-test")
        assert first.returncode == 0, first.stderr
        second = _run_make(make_workspace, "venv-test")
        assert second.returncode == 0, second.stderr
        _assert_no_pip_install(_combined_output(second))

    def test_venv_otel_skips_pip_when_current(self, make_workspace: Path) -> None:
        venv = _run_make(make_workspace, "venv")
        assert venv.returncode == 0, venv.stderr
        first = _run_make(make_workspace, "venv-otel")
        assert first.returncode == 0, first.stderr
        second = _run_make(make_workspace, "venv-otel")
        assert second.returncode == 0, second.stderr
        _assert_no_pip_install(_combined_output(second))

    def test_venv_test_installs_when_stamp_missing(
        self,
        make_workspace: Path,
    ) -> None:
        stamp = make_workspace / ".venv" / VENV_TEST_STAMP_NAME
        venv = _run_make(make_workspace, "venv")
        assert venv.returncode == 0, venv.stderr
        if stamp.exists():
            stamp.unlink()
        result = _run_make(make_workspace, "venv-test")
        assert result.returncode == 0, result.stderr
        _assert_pip_install_extra(_combined_output(result), ".[dev]")

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

    def test_venv_test_installs_when_stamp_stale(
        self,
        make_workspace: Path,
    ) -> None:
        venv = _run_make(make_workspace, "venv")
        assert venv.returncode == 0, venv.stderr
        first = _run_make(make_workspace, "venv-test")
        assert first.returncode == 0, first.stderr
        _make_stamp_stale(make_workspace, VENV_TEST_STAMP_NAME)
        result = _run_make(make_workspace, "venv-test")
        assert result.returncode == 0, result.stderr
        _assert_pip_install_extra(_combined_output(result), ".[dev]")

    def test_venv_otel_installs_when_stamp_stale(
        self,
        make_workspace: Path,
    ) -> None:
        venv = _run_make(make_workspace, "venv")
        assert venv.returncode == 0, venv.stderr
        first = _run_make(make_workspace, "venv-otel")
        assert first.returncode == 0, first.stderr
        _make_stamp_stale(make_workspace, VENV_OTEL_STAMP_NAME)
        result = _run_make(make_workspace, "venv-otel")
        assert result.returncode == 0, result.stderr
        _assert_pip_install_extra(_combined_output(result), ".[otel]")

    def test_venv_test_depends_on_stamp(self, make_workspace: Path) -> None:
        prereqs = _prerequisites(make_workspace, "venv-test")
        assert VENV_TEST_STAMP_REL in prereqs

    def test_venv_otel_depends_on_stamp(self, make_workspace: Path) -> None:
        prereqs = _prerequisites(make_workspace, "venv-otel")
        assert VENV_OTEL_STAMP_REL in prereqs


class TestInstallExtraStampContract:
    """PYPOST-929: make install must touch both extra stamps."""

    def test_install_touches_both_extra_stamps(
        self,
        make_workspace: Path,
    ) -> None:
        venv = _run_make(make_workspace, "venv")
        assert venv.returncode == 0, venv.stderr
        test_stamp = make_workspace / ".venv" / VENV_TEST_STAMP_NAME
        otel_stamp = make_workspace / ".venv" / VENV_OTEL_STAMP_NAME
        assert not test_stamp.exists()
        assert not otel_stamp.exists()

        install = _run_make(make_workspace, "install")
        assert install.returncode == 0, install.stderr
        assert test_stamp.is_file(), (
            "make install must touch VENV_TEST_STAMP so venv-test skips pip"
        )
        assert otel_stamp.is_file(), (
            "make install must touch VENV_OTEL_STAMP so venv-otel skips pip"
        )

    def test_install_stamps_allow_skip_pip_on_venv_test_otel(
        self,
        make_workspace: Path,
    ) -> None:
        venv = _run_make(make_workspace, "venv")
        assert venv.returncode == 0, venv.stderr
        install = _run_make(make_workspace, "install")
        assert install.returncode == 0, install.stderr

        test_second = _run_make(make_workspace, "venv-test")
        assert test_second.returncode == 0, test_second.stderr
        _assert_no_pip_install(_combined_output(test_second))

        otel_second = _run_make(make_workspace, "venv-otel")
        assert otel_second.returncode == 0, otel_second.stderr
        _assert_no_pip_install(_combined_output(otel_second))
