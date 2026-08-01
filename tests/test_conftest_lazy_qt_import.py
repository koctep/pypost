"""PYPOST-926: conftest must defer PySide6 import until the qapp fixture runs."""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

import pytest

pytestmark = pytest.mark.timeout(10)

_REPO_ROOT = Path(__file__).resolve().parents[1]

_CONFTST_IMPORT_SNIPPET = """
import sys

sys.path.insert(0, {repo_root!r})

import tests.conftest  # noqa: F401

assert "PySide6" not in sys.modules, (
    "tests.conftest must not import PySide6 at module level; "
    "defer to the qapp fixture"
)
"""


def test_conftest_does_not_import_pyside6_at_module_level() -> None:
    """Importing conftest alone must not load PySide6 (non-GUI collection paths)."""
    code = _CONFTST_IMPORT_SNIPPET.format(repo_root=str(_REPO_ROOT))
    result = subprocess.run(
        [sys.executable, "-c", code],
        cwd=_REPO_ROOT,
        capture_output=True,
        text=True,
        timeout=10,
        check=False,
    )
    if result.returncode != 0:
        pytest.fail(
            "conftest module-level import check failed:\n"
            f"stdout: {result.stdout}\n"
            f"stderr: {result.stderr}"
        )


def test_qapp_fixture_still_provides_qapplication(qapp) -> None:
    """GUI tests must still receive a live QApplication from the shared fixture."""
    from PySide6.QtWidgets import QApplication

    assert isinstance(qapp, QApplication)
    assert QApplication.instance() is qapp
