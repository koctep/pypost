"""Tests for code folding support in ResponseView (PYPOST-1365).

Validates format detection (JSON, YAML, XML, plain), fold region discovery,
gutter/button actions ("Fold All", "Unfold All"), context menu actions, and
search disclosure within collapsed regions.
"""

from __future__ import annotations

import json
from unittest.mock import MagicMock, patch

import pytest
from PySide6.QtCore import QPoint

from pypost.models.response import ResponseData
from pypost.ui.widgets.response_view import ResponseView

pytestmark = pytest.mark.timeout(60)

_QMENU_PATCH = "pypost.ui.widgets.response_view.QMenu"

_NESTED_JSON = json.dumps(
    {"users": [{"id": 1, "name": "Ada"}, {"id": 2, "name": "Bob"}]},
    indent=2,
)

_NESTED_YAML = """users:
  - id: 1
    name: Ada
  - id: 2
    name: Bob
"""

_NESTED_XML = """<root>
  <users>
    <user id="1">
      <name>Ada</name>
    </user>
  </users>
</root>
"""

_PLAIN_TEXT = "Just a simple log message line 1\nline 2\nline 3"


def _visible_block_count(view: ResponseView) -> int:
    block = view.body_view.document().firstBlock()
    count = 0
    while block.isValid():
        if block.isVisible():
            count += 1
        block = block.next()
    return count


class TestResponseViewFolding:
    """Verifies ResponseView integration with code folding."""

    def test_body_view_has_fold_controller(self, qapp):
        """ResponseView.body_view must expose fold_controller()."""
        view = ResponseView()
        try:
            assert hasattr(view.body_view, "fold_controller"), (
                "ResponseView.body_view must provide fold_controller()"
            )
            fc = view.body_view.fold_controller()
            assert fc is not None
        finally:
            view.close()

    def test_json_response_produces_fold_regions(self, qapp):
        """Displaying JSON response discovers fold regions."""
        view = ResponseView()
        try:
            resp = ResponseData(
                status_code=200,
                headers={"Content-Type": "application/json"},
                elapsed_time=0.1,
                size=len(_NESTED_JSON),
                body=_NESTED_JSON,
            )
            view.display_response(resp)

            fc = view.body_view.fold_controller()
            regions = fc.regions()
            assert len(regions) > 0, "JSON response should produce fold regions"
        finally:
            view.close()

    def test_yaml_response_produces_fold_regions(self, qapp):
        """Displaying YAML response discovers fold regions."""
        view = ResponseView()
        try:
            resp = ResponseData(
                status_code=200,
                headers={"Content-Type": "application/x-yaml"},
                elapsed_time=0.1,
                size=len(_NESTED_YAML),
                body=_NESTED_YAML,
            )
            view.display_response(resp)

            fc = view.body_view.fold_controller()
            regions = fc.regions()
            assert len(regions) > 0, "YAML response should produce fold regions"
        finally:
            view.close()

    def test_xml_response_produces_fold_regions(self, qapp):
        """Displaying XML response discovers fold regions."""
        view = ResponseView()
        try:
            resp = ResponseData(
                status_code=200,
                headers={"Content-Type": "application/xml"},
                elapsed_time=0.1,
                size=len(_NESTED_XML),
                body=_NESTED_XML,
            )
            view.display_response(resp)

            fc = view.body_view.fold_controller()
            regions = fc.regions()
            assert len(regions) > 0, "XML response should produce fold regions"
        finally:
            view.close()

    def test_plain_text_response_produces_no_fold_regions(self, qapp):
        """Displaying plain text response produces zero fold regions."""
        view = ResponseView()
        try:
            resp = ResponseData(
                status_code=200,
                headers={"Content-Type": "text/plain"},
                elapsed_time=0.05,
                size=len(_PLAIN_TEXT),
                body=_PLAIN_TEXT,
            )
            view.display_response(resp)

            fc = view.body_view.fold_controller()
            regions = fc.regions()
            assert len(regions) == 0, "Plain text response should have no fold regions"
        finally:
            view.close()

    def test_fold_all_and_unfold_all_actions(self, qapp):
        """Fold all collapses regions; unfold all expands them."""
        view = ResponseView()
        try:
            resp = ResponseData(
                status_code=200,
                headers={"Content-Type": "application/json"},
                elapsed_time=0.1,
                size=len(_NESTED_JSON),
                body=_NESTED_JSON,
            )
            view.display_response(resp)

            total_blocks = view.body_view.document().blockCount()
            assert _visible_block_count(view) == total_blocks

            assert hasattr(view.body_view, "fold_all"), "body_view must support fold_all()"
            assert hasattr(view.body_view, "unfold_all"), "body_view must support unfold_all()"

            view.body_view.fold_all()
            visible_after_fold = _visible_block_count(view)
            assert visible_after_fold < total_blocks, (
                f"Expected fewer visible blocks after fold_all: "
                f"{visible_after_fold} < {total_blocks}"
            )

            view.body_view.unfold_all()
            assert _visible_block_count(view) == total_blocks
        finally:
            view.close()

    def test_context_menu_has_fold_actions(self, qapp):
        """Context menu includes 'Fold All' and 'Unfold All' when regions exist."""
        view = ResponseView()
        try:
            resp = ResponseData(
                status_code=200,
                headers={"Content-Type": "application/json"},
                elapsed_time=0.1,
                size=len(_NESTED_JSON),
                body=_NESTED_JSON,
            )
            view.display_response(resp)

            mock_menu = MagicMock()
            mock_menu.isEmpty.return_value = True
            action_map = {}

            def add_action_impl(label):
                action = MagicMock()
                action_map[label] = action
                return action

            mock_menu.addAction.side_effect = add_action_impl

            with patch(_QMENU_PATCH, return_value=mock_menu):
                view.show_context_menu(QPoint(0, 0))

            assert "Fold All" in action_map, "Context menu should include 'Fold All'"
            assert "Unfold All" in action_map, "Context menu should include 'Unfold All'"
        finally:
            view.close()

    def test_search_reveals_folded_match(self, qapp):
        """Searching for a term inside a folded region expands it to show the match."""
        view = ResponseView()
        try:
            resp = ResponseData(
                status_code=200,
                headers={"Content-Type": "application/json"},
                elapsed_time=0.1,
                size=len(_NESTED_JSON),
                body=_NESTED_JSON,
            )
            view.display_response(resp)

            # Fold all blocks
            view.body_view.fold_all()
            total_blocks = view.body_view.document().blockCount()
            assert _visible_block_count(view) < total_blocks

            # Search for a term located in the folded interior ("Ada")
            view.search_input.setText("Ada")
            view._on_search_text_changed()

            # The block containing "Ada" should now be revealed / visible
            cursor = view.body_view.textCursor()
            selected = cursor.selectedText()
            assert selected == "Ada", f"Expected selection 'Ada', got '{selected}'"
            matched_block = cursor.block()
            assert matched_block.isVisible(), "Matched block inside fold must be revealed"
        finally:
            view.close()
