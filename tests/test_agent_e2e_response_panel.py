"""PYPOST-869: Shared response-panel snapshot helpers for agent Send tests.

Unit proof (no Qt window): helpers exist under tests/helpers and behave on a
synthetic snapshot tree; Send consumer modules must not keep local
``_walk_values`` / ``_subtree_by_name`` copies.

PYPOST-948: sibling Send settle convention — mandatory agent e2e locks must
use identity-scoped ``wait_for_text`` on ``RESPONSE_STATUS`` / ``RESPONSE_BODY``
instead of ``wait_for_snapshot(_response_ready)`` panel-walk readiness.
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
)
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
