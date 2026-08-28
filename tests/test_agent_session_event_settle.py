"""PYPOST-1217: Assert AgentAppSession post-ready flush and tree settlement contracts."""

from __future__ import annotations

import pytest
from PySide6.QtCore import QTimer
from PySide6.QtGui import QStandardItem, QStandardItemModel
from PySide6.QtWidgets import QApplication, QHBoxLayout, QTreeView, QWidget

from pypost.agent.lifecycle import AgentAppSession
from pypost.agent.ui_actions import (
    UiTargetNotInteractableError,
    ui_select,
)
from pypost.ui.main_window import MainWindow
from pypost.ui.widget_ids import set_widget_id
from tests.helpers.qt_item_view import close_item_view_fixture

pytestmark = [
    pytest.mark.timeout(60),
    pytest.mark.agent_e2e,
]


def test_agent_session_start_drains_post_ready_events(
    qapp: QApplication,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """AgentAppSession.start() must drain queued event loop events before returning.

    Simulates an asynchronous single-shot event queued during/immediately upon
    MainWindow.is_ui_ready resolution (e.g. showEvent's deferred apply_settings
    call). Without an explicit post-ready QCoreApplication.processEvents() flush
    in AgentAppSession.start(), the queued event remains unexecuted upon return.
    """
    assert QApplication.instance() is qapp
    post_ready_callback_ran = False

    def _on_settle() -> None:
        nonlocal post_ready_callback_ran
        post_ready_callback_ran = True

    original_is_ui_ready_getter = MainWindow.is_ui_ready.fget
    queued = False

    def _hooked_is_ui_ready(window_self: MainWindow) -> bool:
        nonlocal queued
        ready = original_is_ui_ready_getter(window_self)
        if ready and not queued:
            queued = True
            QTimer.singleShot(0, _on_settle)
        return ready

    monkeypatch.setattr(MainWindow, "is_ui_ready", property(_hooked_is_ui_ready))

    with AgentAppSession(offscreen=True, ready_timeout=30.0) as session:
        assert session.window.is_ui_ready is True
        # In unpatched code, AgentAppSession.start() returns immediately after
        # wait_until(is_ui_ready) without a trailing processEvents() flush.
        # This assertion will fail (post_ready_callback_ran is False) until Step 4.
        assert post_ready_callback_ran is True, (
            "AgentAppSession.start() returned before draining post-ready queued events"
        )


def test_ui_select_tree_settles_layout_before_index_lookup(
    qapp: QApplication,
) -> None:
    """_select_tree() must pump events before index traversal.

    Ensures pending layout/paint passes or model updates settle before item
    lookup begins. When looking up an absent option, the tree layout pump must
    execute before UiTargetNotInteractableError('option not found') is raised.
    """
    root = QWidget()
    try:
        layout = QHBoxLayout(root)
        tree = QTreeView()
        model = QStandardItemModel()
        parent_item = QStandardItem("ParentNode")
        child_item = QStandardItem("ChildNode")
        parent_item.appendRow(child_item)
        model.appendRow(parent_item)
        tree.setModel(model)
        set_widget_id(tree, "fixture_tree")
        layout.addWidget(tree)
        root.show()
        qapp.processEvents()

        tree_settle_probe_ran = False

        def _tree_probe() -> None:
            nonlocal tree_settle_probe_ran
            tree_settle_probe_ran = True

        QTimer.singleShot(0, _tree_probe)

        with pytest.raises(UiTargetNotInteractableError) as exc_info:
            ui_select(root, "fixture_tree", "__nonexistent_tree_option__")

        # Invariant check: negative lookup contract must hold
        assert "option not found" in str(exc_info.value)

        # Settlement check: in unpatched code, _select_tree does not call _pump()
        # prior to traversal, so queued single-shot events remain unexecuted.
        # This assertion will fail (tree_settle_probe_ran is False) until Step 4.
        assert tree_settle_probe_ran is True, (
            "_select_tree() did not pump event loop to settle layout before lookup"
        )
    finally:
        close_item_view_fixture(root, qapp, "fixture_tree", view_type=QTreeView)
