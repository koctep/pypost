"""PYPOST-840: Lock single wait_until implementation (no agent/tests drift)."""

from __future__ import annotations

import ast
from pathlib import Path

import pytest

from pypost.agent import ui_wait as ui_wait_mod
from tests.helpers import qt_wait as qt_wait_mod

pytestmark = pytest.mark.timeout(10)

_REPO = Path(__file__).resolve().parents[1]
_AGENT_PKG = _REPO / "pypost" / "agent"
_LIFECYCLE = _AGENT_PKG / "lifecycle.py"


def test_qt_wait_reexports_production_wait_until() -> None:
    assert qt_wait_mod.wait_until is ui_wait_mod.wait_until


def test_lifecycle_has_no_private_wait_until_function() -> None:
    tree = ast.parse(_LIFECYCLE.read_text(encoding="utf-8"))
    for node in tree.body:
        if isinstance(node, ast.FunctionDef) and node.name == "_wait_until":
            pytest.fail("lifecycle.py must not define module-level _wait_until")


def test_agent_package_does_not_import_tests() -> None:
    offenders: list[str] = []
    for path in sorted(_AGENT_PKG.rglob("*.py")):
        source = path.read_text(encoding="utf-8")
        tree = ast.parse(source)
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    if alias.name == "tests" or alias.name.startswith("tests."):
                        offenders.append(f"{path.relative_to(_REPO)}: import {alias.name}")
            elif isinstance(node, ast.ImportFrom):
                mod = node.module or ""
                if mod == "tests" or mod.startswith("tests."):
                    offenders.append(
                        f"{path.relative_to(_REPO)}: from {mod} import ..."
                    )
    assert not offenders, "pypost.agent must not import tests:\n" + "\n".join(offenders)
