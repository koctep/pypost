"""Integration tests for make install stamp contract.

Covers PYPOST-929, PYPOST-1262.
"""

from __future__ import annotations

from pathlib import Path

import pytest

from tests.makefile_test_helpers import (
    VENV_OTEL_STAMP_NAME,
    VENV_TEST_STAMP_NAME,
    _assert_no_pip_install,
    _combined_output,
    _run_make,
    make_workspace,
)

pytestmark = pytest.mark.timeout(60)


class TestInstallExtraStampContract:
    """PYPOST-929: make install must touch both extra stamps."""

    @pytest.mark.timeout(60)
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

    @pytest.mark.timeout(60)
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
