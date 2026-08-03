"""PYPOST-1045: decision lock on controlled HTTP backend recommendation.

Offline doc-lock (no network). Asserts ``ai-tasks/PYPOST-1045/20-architecture.md``
encodes the analysis recommendation: controlled backend yes, in-process loopback
HTTP stand-in (not agent_e2e patch primary, not live-only), the four smoke tool
ids, and Makefile target ``test-mcp-collection-e2e``.

See ``ai-tasks/PYPOST-1045/20-architecture.md`` § Mandatory — Failing Repro.
"""

from __future__ import annotations

from pathlib import Path

import pytest

from tests.helpers.packaging_doc_lock import (
    assert_substring,
    doc_label,
    read_doc,
)

pytestmark = pytest.mark.timeout(10)

_REPO_ROOT = Path(__file__).resolve().parents[1]
_ARCH = (
    _REPO_ROOT / "ai-tasks" / "PYPOST-1045" / "20-architecture.md"
)

# Explicit Decision Lock tokens (Step 4 must add this block to the architecture
# artifact). Loose prose alone is not enough — the lock is machine-checkable.
_DECISION_LOCK_HEADER = "## Decision Lock"
_REQUIRED_LOCK_TOKENS = (
    "controlled_backend_needed: yes",
    "recommended_form: in-process loopback HTTP stand-in",
    "agent_e2e_http_primary: no",
    "live_only: no",
    "makefile_target: test-mcp-collection-e2e",
    (
        "tool_ids: jira_get_current_user, jira_search_issues_jql, "
        "jira_get_issue, jira_list_boards"
    ),
)


def test_pypost_1045_architecture_recommendation_doc_lock() -> None:
    """Architecture must exist with an explicit Decision Lock for PYPOST-1045."""
    label = doc_label(_ARCH, _REPO_ROOT)
    if not _ARCH.is_file():
        pytest.fail(
            f"{label}: missing recommendation artifact — "
            "PYPOST-1045 architecture decision lock requires this file"
        )

    text = read_doc(_ARCH)
    assert_substring(
        text,
        _DECISION_LOCK_HEADER,
        doc_label_str=label,
        detail=(
            "add an explicit ## Decision Lock section encoding the "
            "controlled-backend recommendation"
        ),
    )
    for token in _REQUIRED_LOCK_TOKENS:
        assert_substring(
            text,
            token,
            doc_label_str=label,
            detail=(
                "Decision Lock must record yes / loopback stand-in / "
                "not agent_e2e primary / not live-only / four tool ids / "
                "test-mcp-collection-e2e"
            ),
        )
