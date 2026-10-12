"""Actual Make lint must reject new test-source defects (PYPOST-1303)."""

from __future__ import annotations

import json
import os
import shlex
import shutil
import sys
import time
from pathlib import Path

import pytest

from tests.makefile_test_helpers import (
    MAKEFILE,
    MARKER_NAME,
    REPO_ROOT,
    VENV_TEST_STAMP_NAME,
    _run_make,
)

pytestmark = pytest.mark.timeout(60)


@pytest.fixture
def lint_workspace(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    """Use installed tools and locally satisfied Make prerequisites without pip."""
    shutil.copy(MAKEFILE, tmp_path / "Makefile")
    shutil.copy(REPO_ROOT / ".flake8", tmp_path / ".flake8")
    (tmp_path / "pyproject.toml").write_text(
        '[project]\nname = "lint-gate-repro"\nversion = "0.0.0"\n', encoding="utf-8",
    )
    production = tmp_path / "pypost"
    production.mkdir()
    (production / "__init__.py").write_text("", encoding="utf-8")
    tests = tmp_path / "tests"
    tests.mkdir()
    (tests / "test_clean.py").write_text(
        "import pytest\n\npytestmark = pytest.mark.timeout(10)\n\n\n"
        "def test_clean() -> None:\n    assert True\n", encoding="utf-8",
    )
    scripts = tmp_path / "scripts"
    scripts.mkdir()
    checker = REPO_ROOT / "scripts" / "check_test_lint_baseline.py"
    if checker.is_file():
        shutil.copy(checker, scripts / checker.name)
    (tmp_path / "test-lint-baseline.json").write_text(
        json.dumps({"version": 1, "entries": []}) + "\n", encoding="utf-8",
    )
    venv = tmp_path / ".venv"
    (venv / "bin").mkdir(parents=True)
    python = venv / "bin" / "python"
    python.write_text(
        f"#!/bin/sh\nexec {shlex.quote(sys.executable)} \"$@\"\n", encoding="utf-8",
    )
    python.chmod(0o755)
    now = time.time()
    os.utime(tmp_path / "pyproject.toml", (now - 2, now - 2))
    marker = venv / MARKER_NAME
    marker.touch()
    os.utime(marker, (now - 1, now - 1))
    stamp = venv / VENV_TEST_STAMP_NAME
    stamp.touch()
    os.utime(stamp, (now, now))
    monkeypatch.setenv("PIP_NO_INDEX", "1")
    return tmp_path


def test_make_lint_accepts_clean_test_and_production_sources(lint_workspace: Path) -> None:
    result = _run_make(lint_workspace, "lint", timeout=20)
    output = result.stdout + result.stderr
    assert "pip install" not in output
    assert result.returncode == 0, output
    assert "flake8" in output


@pytest.mark.parametrize(
    ("source", "code"),
    [
        ("import math\n", "F401"),
        ('VALUE = "' + "x" * 110 + '"\n', "E501"),
        ('print("unexpected diagnostic output")\n', "T201"),
    ],
    ids=["F401", "E501", "T201"],
)
def test_make_lint_rejects_new_test_source_defects(
    lint_workspace: Path, source: str, code: str,
) -> None:
    (lint_workspace / "tests" / "test_new_defect.py").write_text(source, encoding="utf-8")
    result = _run_make(lint_workspace, "lint", timeout=20)
    output = result.stdout + result.stderr
    assert "pip install" not in output
    assert result.returncode != 0, f"make lint accepted new test {code}:\n{output}"
    assert "test_new_defect.py" in output, output
    assert code in output, output


def test_make_lint_still_rejects_production_unused_import(lint_workspace: Path) -> None:
    (lint_workspace / "pypost" / "defect.py").write_text("import math\n", encoding="utf-8")
    result = _run_make(lint_workspace, "lint", timeout=20)
    output = result.stdout + result.stderr
    assert "pip install" not in output
    assert result.returncode != 0, output
    assert "pypost/defect.py" in output, output
    assert "F401" in output, output
