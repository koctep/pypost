"""Collection sidebar panel construction."""
from __future__ import annotations

from collections.abc import Callable

from PySide6.QtWidgets import QHBoxLayout, QPushButton, QTreeView, QVBoxLayout, QWidget

from pypost.core.collection_messages import (
    BUTTON_EXPORT_ALL_COLLECTIONS,
    BUTTON_EXPORT_COLLECTION,
    BUTTON_IMPORT_COLLECTION,
)
from pypost.ui.widget_ids import (
    COLLECTION_EXPORT_ALL_BUTTON,
    COLLECTION_EXPORT_BUTTON,
    COLLECTION_IMPORT_BUTTON,
    set_widget_id,
)


def build_collections_panel(
    tree_view: QTreeView,
    *,
    import_collection: Callable[[], None],
    export_collection: Callable[[], None],
    export_all_collections: Callable[[], None],
) -> QWidget:
    """Build the collection tree panel and connect its action buttons."""
    panel = QWidget()
    layout = QVBoxLayout(panel)
    layout.setContentsMargins(0, 0, 0, 0)

    import_btn = QPushButton(BUTTON_IMPORT_COLLECTION)
    set_widget_id(import_btn, COLLECTION_IMPORT_BUTTON)
    import_btn.clicked.connect(import_collection)

    export_btn = QPushButton(BUTTON_EXPORT_COLLECTION)
    set_widget_id(export_btn, COLLECTION_EXPORT_BUTTON)
    export_btn.clicked.connect(export_collection)

    export_all_btn = QPushButton(BUTTON_EXPORT_ALL_COLLECTIONS)
    set_widget_id(export_all_btn, COLLECTION_EXPORT_ALL_BUTTON)
    export_all_btn.clicked.connect(export_all_collections)

    buttons_row = QHBoxLayout()
    buttons_row.addWidget(import_btn)
    buttons_row.addWidget(export_btn)
    buttons_row.addWidget(export_all_btn)
    buttons_row.addStretch(1)

    layout.addWidget(tree_view)
    layout.addLayout(buttons_row)
    return panel
