"""PYPOST-869: Shared response-panel snapshot helpers for agent Send tests.

Unit proof (no Qt window): helpers exist under tests/helpers and behave on a
synthetic snapshot tree; Send consumer modules must not keep local
``_walk_values`` / ``_subtree_by_name`` copies.
"""

from __future__ import annotations

import ast
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


def _toplevel_def_names(path: Path) -> set[str]:
    tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
    return {
        node.name
        for node in tree.body
        if isinstance(node, ast.FunctionDef | ast.AsyncFunctionDef)
    }


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
