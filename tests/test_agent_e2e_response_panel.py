"""PYPOST-869: Shared response-panel snapshot helpers for agent Send tests.

Unit proof (no Qt window): helpers exist under tests/helpers and behave on a
synthetic snapshot tree; Send consumer modules must not keep local
``_walk_values`` / ``_subtree_by_name`` copies.

PYPOST-948: sibling Send settle convention — mandatory agent e2e locks must
use identity-scoped ``wait_for_text`` on ``RESPONSE_STATUS`` / ``RESPONSE_BODY``
instead of ``wait_for_snapshot(_response_ready)`` panel-walk readiness.

PYPOST-956: mapping snapshot Send settle must use shared
``wait_response_after_snapshot``; no module-local ``_wait_response``.

PYPOST-978: golden text waits must use ``session.wait_for_text`` with
``in_current_tab=True``; no free-function ``wait_for_text`` import.
"""

from __future__ import annotations

import ast
import re
from pathlib import Path

import pytest

pytestmark = pytest.mark.timeout(10)

_TESTS_DIR = Path(__file__).resolve().parent
_CONSUMER_MODULES = (
    "test_agent_golden_e2e.py",
    "test_agent_e2e_http_env.py",
    "test_agent_e2e_double_response_body.py",
    "test_agent_e2e_presentation_matrix.py",
)
_SEND_SETTLE_MODULES = (
    "test_agent_e2e_double_response_body.py",
    "test_agent_e2e_presentation_matrix.py",
    "test_agent_e2e_http_env.py",
    "test_agent_e2e_http_seed_post.py",
)
_SNAPSHOT_SEND_SETTLE_MODULES = ("test_agent_e2e_http_mapping_multi_url.py",)
_JSON_BODY_MODULES = frozenset({"test_agent_e2e_http_env.py"})
_WAIT_FOR_SNAPSHOT_RESPONSE_READY = re.compile(
    r"wait_for_snapshot\s*\(\s*_response_ready\b",
    re.DOTALL | re.MULTILINE,
)
_WAIT_FOR_TEXT_BODY_IN_SNAPSHOT = re.compile(
    r"wait_for_text\s*\([^)]*_BODY_IN_SNAPSHOT",
    re.DOTALL | re.MULTILINE,
)
_WAIT_RESPONSE_AFTER_SEND = re.compile(
    r"(?:^|[^\w.])wait_response_after_send\s*\(",
    re.MULTILINE,
)
_WAIT_RESPONSE_AFTER_SNAPSHOT = re.compile(
    r"(?:^|[^\w.])wait_response_after_snapshot\s*\(",
    re.MULTILINE,
)

_SYNTHETIC_SNAP: dict = {
    "name": "root",
    "value": "",
    "children": [
        {
            "name": "pypost_response_panel",
            "value": "Status: 200",
            "children": [
                {"name": "body", "value": '{"ok": true}', "children": []},
                {
                    "name": "padding",
                    "value": "x" * 450,
                    "children": [],
                },
            ],
        },
        {"name": "other", "value": "ignored", "children": []},
    ],
}


def _module_source(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def _toplevel_def_names(path: Path) -> set[str]:
    tree = ast.parse(_module_source(path), filename=str(path))
    return {
        node.name
        for node in tree.body
        if isinstance(node, ast.FunctionDef | ast.AsyncFunctionDef)
    }


def _all_def_names(path: Path) -> set[str]:
    tree = ast.parse(_module_source(path), filename=str(path))
    return {
        node.name
        for node in ast.walk(tree)
        if isinstance(node, ast.FunctionDef | ast.AsyncFunctionDef)
    }


def _uses_wait_for_text_on(source: str, widget_id: str) -> bool:
    pattern = re.compile(
        rf"(?:^|[^\w.])(?:session\.)?wait_for_text\s*\("
        rf"[^)]*\b{re.escape(widget_id)}\b",
        re.DOTALL | re.MULTILINE,
    )
    return bool(pattern.search(source))


def _uses_wait_response_after_send(source: str) -> bool:
    return bool(_WAIT_RESPONSE_AFTER_SEND.search(source))


def _uses_wait_response_after_snapshot(source: str) -> bool:
    return bool(_WAIT_RESPONSE_AFTER_SNAPSHOT.search(source))


def test_golden_success_send_uses_shared_settle_helper() -> None:
    """PYPOST-970: Golden success settle imports and calls the shared helper."""
    path = _TESTS_DIR / "test_agent_golden_e2e.py"
    tree = ast.parse(_module_source(path), filename=str(path))

    helper_imported = any(
        isinstance(node, ast.ImportFrom)
        and node.module == "tests.helpers.agent_e2e_send_settle"
        and any(
            alias.name == "wait_response_after_send" for alias in node.names
        )
        for node in tree.body
    )
    success_helper = next(
        (
            node
            for node in tree.body
            if isinstance(node, ast.FunctionDef | ast.AsyncFunctionDef)
            and node.name == "_golden_fill_send_and_settle"
        ),
        None,
    )
    assert success_helper is not None, "missing _golden_fill_send_and_settle"
    helper_called = any(
        isinstance(node, ast.Call)
        and isinstance(node.func, ast.Name)
        and node.func.id == "wait_response_after_send"
        for node in ast.walk(success_helper)
    )

    assert helper_imported and helper_called, (
        "Golden successful Send settle must import and call "
        "tests.helpers.agent_e2e_send_settle.wait_response_after_send; "
        f"imported={helper_imported}, called_in_success_helper={helper_called}"
    )


def _is_free_wait_for_text_import(node: ast.AST) -> bool:
    """True if node imports free-function wait_for_text from agent/ui_wait."""
    if not isinstance(node, ast.ImportFrom):
        return False
    if node.module not in {"pypost.agent", "pypost.agent.ui_wait"}:
        return False
    return any(alias.name == "wait_for_text" for alias in node.names)


def _wait_for_text_calls(tree: ast.AST) -> list[ast.Call]:
    """Return every Call whose callee name is wait_for_text (Name or Attribute)."""
    calls: list[ast.Call] = []
    for node in ast.walk(tree):
        if not isinstance(node, ast.Call):
            continue
        func = node.func
        if isinstance(func, ast.Name) and func.id == "wait_for_text":
            calls.append(node)
        elif (
            isinstance(func, ast.Attribute)
            and func.attr == "wait_for_text"
        ):
            calls.append(node)
    return calls


def _is_session_wait_for_text_call(call: ast.Call) -> bool:
    """True if call is session.wait_for_text(...)."""
    func = call.func
    return (
        isinstance(func, ast.Attribute)
        and func.attr == "wait_for_text"
        and isinstance(func.value, ast.Name)
        and func.value.id == "session"
    )


def _has_in_current_tab_true(call: ast.Call) -> bool:
    """True if call passes keyword in_current_tab=True."""
    for keyword in call.keywords:
        if keyword.arg != "in_current_tab":
            continue
        return (
            isinstance(keyword.value, ast.Constant)
            and keyword.value.value is True
        )
    return False


def test_golden_text_waits_use_session_api_not_free_function() -> None:
    """PYPOST-978: Golden text waits use session API, not free wait_for_text."""
    path = _TESTS_DIR / "test_agent_golden_e2e.py"
    tree = ast.parse(_module_source(path), filename=str(path))

    free_imports = [
        node for node in tree.body if _is_free_wait_for_text_import(node)
    ]
    assert not free_imports, (
        "Golden must not import free-function wait_for_text from "
        "pypost.agent or pypost.agent.ui_wait; use session.wait_for_text"
    )

    calls = _wait_for_text_calls(tree)
    bare_name_calls = [
        call
        for call in calls
        if isinstance(call.func, ast.Name)
    ]
    assert not bare_name_calls, (
        "Golden wait_for_text calls must be session.wait_for_text "
        f"(Attribute), not bare Name; found {len(bare_name_calls)} bare call(s)"
    )

    for call in calls:
        assert _is_session_wait_for_text_call(call), (
            "Golden wait_for_text must be session.wait_for_text only"
        )
        assert _has_in_current_tab_true(call), (
            "session.wait_for_text must pass in_current_tab=True"
        )


def test_shared_response_panel_helpers_api_and_behavior() -> None:
    """FR1/FR3/FR4: import shared helpers; walk / subtree / excerpt / join."""
    from tests.helpers.agent_e2e_response_panel import (
        joined_panel_values,
        response_panel_excerpt,
        subtree_by_name,
        walk_values,
    )
    from pypost.ui.widget_ids import RESPONSE_PANEL

    panel = subtree_by_name(_SYNTHETIC_SNAP, RESPONSE_PANEL)
    assert panel is not None
    assert panel["name"] == RESPONSE_PANEL

    values = walk_values(panel)
    assert values[0] == "Status: 200"
    assert '{"ok": true}' in values
    assert any(v.startswith("x") for v in values)

    joined = joined_panel_values(_SYNTHETIC_SNAP)
    assert "Status: 200" in joined
    assert '{"ok": true}' in joined
    assert "\n" in joined

    excerpt = response_panel_excerpt(_SYNTHETIC_SNAP)
    assert "Status: 200" in excerpt
    assert len(excerpt) <= 401  # 400 chars + ellipsis
    assert excerpt.endswith("…")

    missing = joined_panel_values({"name": "root", "children": []})
    assert missing == ""
    missing_ex = response_panel_excerpt({"name": "root", "children": []})
    assert "not in snapshot" in missing_ex


@pytest.mark.parametrize("module_name", _CONSUMER_MODULES)
def test_send_modules_do_not_define_local_walk_helpers(
    module_name: str,
) -> None:
    """FR2: Send consumers import shared helpers; no local walk/subtree defs."""
    path = _TESTS_DIR / module_name
    assert path.is_file(), f"missing consumer module {path}"
    names = _toplevel_def_names(path)
    assert "_walk_values" not in names, (
        f"{module_name} still defines local _walk_values; "
        "import from tests.helpers.agent_e2e_response_panel"
    )
    assert "_subtree_by_name" not in names, (
        f"{module_name} still defines local _subtree_by_name; "
        "import from tests.helpers.agent_e2e_response_panel"
    )


@pytest.mark.parametrize("module_name", _SEND_SETTLE_MODULES)
def test_send_modules_use_identity_scoped_text_wait_settle(
    module_name: str,
) -> None:
    """PYPOST-948: Send settle uses RESPONSE_STATUS/BODY text waits, not panel walk."""
    path = _TESTS_DIR / module_name
    assert path.is_file(), f"missing Send settle module {path}"
    source = _module_source(path)

    uses_helper = _uses_wait_response_after_send(source)
    uses_inline_text_wait = _uses_wait_for_text_on(
        source, "RESPONSE_STATUS"
    ) and _uses_wait_for_text_on(source, "RESPONSE_BODY")

    if uses_helper:
        if "agent_e2e_send_settle" not in source:
            pytest.fail(
                f"{module_name} calls wait_response_after_send but does not import "
                "from tests.helpers.agent_e2e_send_settle"
            )
    else:
        if "RESPONSE_STATUS" not in source:
            pytest.fail(
                f"{module_name} must import RESPONSE_STATUS from pypost.ui.widget_ids "
                "for identity-scoped Send text-wait settle"
            )
        if "RESPONSE_BODY" not in source:
            pytest.fail(
                f"{module_name} must import RESPONSE_BODY from pypost.ui.widget_ids "
                "for identity-scoped Send text-wait settle"
            )
        if not uses_inline_text_wait:
            pytest.fail(
                f"{module_name} must call wait_for_text on RESPONSE_STATUS and "
                "RESPONSE_BODY after Send, or wait_response_after_send; still using "
                "panel-walk snapshot readiness"
            )

    if "_response_ready" in _all_def_names(path):
        pytest.fail(
            f"{module_name} still defines _response_ready; "
            "drop panel-walk readiness and use wait_for_text on RESPONSE_STATUS "
            "then RESPONSE_BODY"
        )
    if _WAIT_FOR_SNAPSHOT_RESPONSE_READY.search(source):
        pytest.fail(
            f"{module_name} still calls wait_for_snapshot(_response_ready) on the "
            "Send path; migrate to identity-scoped text waits"
        )

    if module_name in _JSON_BODY_MODULES and _WAIT_FOR_TEXT_BODY_IN_SNAPSHOT.search(
        source
    ):
        pytest.fail(
            f"{module_name} must not pass compact _BODY_IN_SNAPSHOT to "
            "wait_for_text; use display-form body text (indent=2)"
        )


def test_shared_send_settle_exports_wait_response_after_snapshot() -> None:
    """PYPOST-956: shared snapshot Send settle helper is importable."""
    from tests.helpers.agent_e2e_send_settle import wait_response_after_snapshot

    assert callable(wait_response_after_snapshot)


@pytest.mark.parametrize("module_name", _SNAPSHOT_SEND_SETTLE_MODULES)
def test_snapshot_send_settle_modules_use_shared_helper(
    module_name: str,
) -> None:
    """PYPOST-956: snapshot Send settle uses shared helper; no local _wait_response."""
    path = _TESTS_DIR / module_name
    assert path.is_file(), f"missing snapshot Send settle module {path}"
    source = _module_source(path)
    names = _toplevel_def_names(path)

    assert "_wait_response" not in names, (
        f"{module_name} still defines local _wait_response; "
        "import wait_response_after_snapshot from "
        "tests.helpers.agent_e2e_send_settle"
    )
    if "agent_e2e_send_settle" not in source:
        pytest.fail(
            f"{module_name} must import from tests.helpers.agent_e2e_send_settle "
            "for snapshot Send settle"
        )
    if not _uses_wait_response_after_snapshot(source):
        pytest.fail(
            f"{module_name} must call wait_response_after_snapshot for snapshot "
            "Send settle instead of local _wait_response"
        )
