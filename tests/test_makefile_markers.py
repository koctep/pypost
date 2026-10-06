"""Integration tests for virtualenv version marker lifecycle.

Covers PYPOST-274, PYPOST-905, PYPOST-1262.
"""

from __future__ import annotations

from pathlib import Path

import pytest

from tests.makefile_test_helpers import MARKER_NAME, _run_make, make_workspace

pytestmark = pytest.mark.timeout(60)


class TestMarkerLifecycle:
    @pytest.mark.timeout(60)
    def test_venv_creates_version_marker(self, make_workspace: Path) -> None:
        result = _run_make(make_workspace, "venv")
        assert result.returncode == 0, result.stderr
        marker = make_workspace / ".venv" / MARKER_NAME
        assert marker.is_file()

    @pytest.mark.timeout(60)
    def test_clean_removes_venv_and_marker(self, make_workspace: Path) -> None:
        _run_make(make_workspace, "venv", check=False)
        result = _run_make(make_workspace, "clean")
        assert result.returncode == 0, result.stderr
        assert not (make_workspace / ".venv").exists()

    @pytest.mark.timeout(60)
    def test_venv_is_idempotent(self, make_workspace: Path) -> None:
        first = _run_make(make_workspace, "venv")
        second = _run_make(make_workspace, "venv")
        assert first.returncode == 0, first.stderr
        assert second.returncode == 0, second.stderr
        assert (make_workspace / ".venv" / MARKER_NAME).is_file()
