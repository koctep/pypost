"""PYPOST-918 / PYPOST-954: lock UI-action MCP packaging docs (path + no-mix).

873-style substring locks via tests.helpers.packaging_doc_lock — see
doc/dev/testing.md § Packaging doc lock strategy.
"""

from __future__ import annotations

from pathlib import Path

import pytest

from tests.helpers.packaging_doc_lock import (
    assert_any_substring,
    assert_substring,
    doc_label,
    read_doc,
)

pytestmark = pytest.mark.timeout(10)

_REPO_ROOT = Path(__file__).resolve().parents[1]
_UI_ACTIONS_DOC = _REPO_ROOT / "doc" / "dev" / "ui_actions.md"
_MCP_INTEGRATION_DOC = _REPO_ROOT / "doc" / "dev" / "mcp_integration.md"
_MCP_TRUST_DOC = _REPO_ROOT / "doc" / "dev" / "mcp_trust_model.md"

_DOC_ANCHOR = "PYPOST-918"
_OUT_OF_PROCESS = "out-of-process"
_PACKAGING_PATH = "packaging path"
# Stronger than today's "not a network MCP tool on MCPServerImpl" / "must not
# import" — packaging prose must forbid mounting/registering UI actions on
# product MCP. Exact multi-word tokens avoid false passes on unrelated "must
# not" / "never" sentences.
_NO_MIX_TOKENS = (
    "never mount",
    "never register",
    "must not mix",
    "do not mix",
    "must not register",
    "never mounted",
)


def test_ui_actions_doc_attributes_packaging_to_pypost_918() -> None:
    """ui_actions.md must attribute the packaging close to PYPOST-918."""
    text = read_doc(_UI_ACTIONS_DOC)
    assert_substring(
        text,
        _DOC_ANCHOR,
        doc_label_str=doc_label(_UI_ACTIONS_DOC, _REPO_ROOT),
        detail=(
            "attribute out-of-process UI-action MCP packaging to this debt"
        ),
    )


def test_ui_actions_doc_states_out_of_process_packaging_path() -> None:
    """ui_actions.md must document an out-of-process packaging path."""
    text = read_doc(_UI_ACTIONS_DOC)
    label = doc_label(_UI_ACTIONS_DOC, _REPO_ROOT)
    assert_substring(
        text,
        _OUT_OF_PROCESS,
        case_insensitive=True,
        doc_label_str=label,
        detail="close the out-of-process MCP packaging answer",
    )
    assert_substring(
        text,
        _PACKAGING_PATH,
        case_insensitive=True,
        doc_label_str=label,
        detail=(
            "name the documented packaging path (not only in-process API notes)"
        ),
    )


def test_ui_actions_doc_locks_no_mixing_with_product_mcp() -> None:
    """Packaging docs must forbid UI-action tools on product MCPServerImpl."""
    text = read_doc(_UI_ACTIONS_DOC)
    label = doc_label(_UI_ACTIONS_DOC, _REPO_ROOT)
    assert_substring(
        text,
        "MCPServerImpl",
        case_insensitive=True,
        doc_label_str=label,
        detail=(
            "name the product MCP surface that must stay free of UI-action tools"
        ),
    )
    assert_any_substring(
        text,
        _NO_MIX_TOKENS,
        case_insensitive=True,
        doc_label_str=label,
        detail=(
            "forbid registering/mounting UI actions on product MCP / "
            "MCPServerImpl (beyond 'not a network MCP tool')"
        ),
    )


def test_mcp_docs_cross_link_ui_actions_packaging() -> None:
    """Product MCP docs must point readers at the UI-actions packaging answer."""
    for path in (_MCP_INTEGRATION_DOC, _MCP_TRUST_DOC):
        text = read_doc(path)
        lower = text.lower()
        has_ui_actions_ref = "ui_actions.md" in lower
        has_packaging_pointer = (
            "packaging" in lower
            or _OUT_OF_PROCESS in lower
            or _DOC_ANCHOR.lower() in lower
        )
        if has_ui_actions_ref and has_packaging_pointer:
            return
    pytest.fail(
        f"Neither {doc_label(_MCP_INTEGRATION_DOC, _REPO_ROOT)} nor "
        f"{doc_label(_MCP_TRUST_DOC, _REPO_ROOT)} cross-links the "
        "UI-actions packaging answer (need ui_actions.md plus packaging / "
        f"{_OUT_OF_PROCESS!r} / {_DOC_ANCHOR})"
    )
