"""Architectural import isolation tests for WebSocket modules (PYPOST-1127).

Guarantees:
1. PySide6.QtWebSockets is imported exclusively within
   `pypost/core/qt/websocket_transport.py` across the entire codebase.
2. `pypost/core/websocket_transport_protocol.py` and
   `pypost/core/websocket_session_policy.py` are strictly Qt-free (no PySide6/QtCore).
3. `pypost/core/qt/websocket_session.py` does not import UI widgets,
   `websocket_stream`, `Environment`, or sensitive data masking policies.
"""

from __future__ import annotations

import ast
from pathlib import Path

import pytest

pytestmark = pytest.mark.timeout(30)

REPO_ROOT = Path(__file__).resolve().parents[1]
PYPOST_DIR = REPO_ROOT / "pypost"


def _get_all_python_files(root: Path) -> list[Path]:
    return [p for p in root.rglob("*.py") if "__pycache__" not in p.parts]


def _extract_imports(file_path: Path) -> list[str]:
    """Parse AST of a Python file and return all imported module names."""
    if not file_path.exists():
        return []
    tree = ast.parse(file_path.read_text(encoding="utf-8"), filename=str(file_path))
    imported_modules: list[str] = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                imported_modules.append(alias.name)
        elif isinstance(node, ast.ImportFrom):
            if node.module:
                imported_modules.append(node.module)
    return imported_modules


def test_websocket_transport_protocol_is_qt_free():
    """`pypost/core/websocket_transport_protocol.py` must contain no Qt imports."""
    protocol_path = PYPOST_DIR / "core" / "websocket_transport_protocol.py"
    assert protocol_path.exists(), f"Expected {protocol_path} to exist"
    imports = _extract_imports(protocol_path)
    qt_imports = [imp for imp in imports if "PySide6" in imp or "Qt" in imp or "QtCore" in imp]
    assert not qt_imports, (
        f"pypost/core/websocket_transport_protocol.py violates Qt-free isolation: {qt_imports}"
    )


def test_websocket_session_policy_is_qt_free():
    """`pypost/core/websocket_session_policy.py` must contain no Qt imports."""
    policy_path = PYPOST_DIR / "core" / "websocket_session_policy.py"
    assert policy_path.exists(), f"Expected {policy_path} to exist"
    imports = _extract_imports(policy_path)
    qt_imports = [imp for imp in imports if "PySide6" in imp or "Qt" in imp or "QtCore" in imp]
    assert not qt_imports, (
        f"pypost/core/websocket_session_policy.py violates Qt-free isolation: {qt_imports}"
    )


def test_websocket_session_controller_decoupled_from_ui_and_masking():
    """`pypost/core/qt/websocket_session.py` must not import stream buffers or masking."""
    session_path = PYPOST_DIR / "core" / "qt" / "websocket_session.py"
    assert session_path.exists(), f"Expected {session_path} to exist"
    imports = _extract_imports(session_path)

    forbidden_patterns = [
        "websocket_stream",
        "sensitive_data_masking",
        "Environment",
        "pypost.ui",
    ]
    violations = [
        imp for imp in imports
        if any(pat in imp for pat in forbidden_patterns)
    ]
    assert not violations, (
        f"pypost/core/qt/websocket_session.py contains forbidden coupled imports: {violations}"
    )


def test_pyside6_qtwebsockets_sole_import_in_websocket_transport():
    """PySide6.QtWebSockets must only be imported in pypost/core/qt/websocket_transport.py."""
    transport_path = (PYPOST_DIR / "core" / "qt" / "websocket_transport.py").resolve()
    assert transport_path.exists(), f"Expected {transport_path} to exist"

    all_py_files = _get_all_python_files(PYPOST_DIR)
    unauthorized_importers: list[tuple[str, list[str]]] = []

    for py_file in all_py_files:
        if py_file.resolve() == transport_path:
            continue
        imports = _extract_imports(py_file)
        ws_imports = [imp for imp in imports if "QtWebSockets" in imp]
        if ws_imports:
            rel_path = str(py_file.relative_to(REPO_ROOT))
            unauthorized_importers.append((rel_path, ws_imports))

    assert not unauthorized_importers, (
        "Unauthorized PySide6.QtWebSockets imports detected outside websocket_transport.py: "
        f"{unauthorized_importers}"
    )
