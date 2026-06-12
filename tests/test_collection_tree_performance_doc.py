"""Guards documented collection-tree refresh wiring (PYPOST-383)."""

from __future__ import annotations

from pathlib import Path
from unittest.mock import MagicMock

import pytest

from pypost.ui.main_window_signals import wire_presenter_signals


@pytest.mark.timeout(10)
def test_save_uses_full_refresh_save_as_uses_incremental_insert():
    """Inventory in doc/dev/collection_tree_performance.md must match signal wiring."""
    window = MagicMock()
    window.tabs = MagicMock()
    window.collections = MagicMock()

    wire_presenter_signals(window)

    saved_handlers = [
        call.args[0]
        for call in window.tabs.request_saved.connect.call_args_list
    ]
    save_as_handlers = [
        call.args[0]
        for call in window.tabs.request_save_as_completed.connect.call_args_list
    ]

    assert window.collections.refresh_tree in saved_handlers
    assert window.collections.add_saved_request_to_tree in save_as_handlers
    assert window.collections.refresh_tree not in save_as_handlers


@pytest.mark.timeout(10)
def test_collection_tree_performance_doc_exists_and_links_prior_debt():
    doc = Path("doc/dev/collection_tree_performance.md")
    text = doc.read_text(encoding="utf-8")
    for token in ("PYPOST-35", "PYPOST-334", "PYPOST-347", "PYPOST-319", "PYPOST-340"):
        assert token in text
