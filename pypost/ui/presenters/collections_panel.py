"""Collection sidebar panel construction."""
from __future__ import annotations

from collections.abc import Callable

from PySide6.QtWidgets import QHBoxLayout, QPushButton, QTreeView, QVBoxLayout, QWidget

from pypost.core.collection_messages import (
    BUTTON_EXPORT_ALL_COLLECTIONS,
    BUTTON_EXPORT_COLLECTION,
    BUTTON_IMPORT_COLLECTION,
    BUTTON_IMPORT_COLLECTION_FROM_FILE,
    BUTTON_IMPORT_COLLECTION_FROM_LIBRARY,
)
from pypost.ui.widget_ids import (
    COLLECTION_EXPORT_ALL_BUTTON,
    COLLECTION_EXPORT_BUTTON,
    COLLECTION_IMPORT_BUTTON,
    COLLECTION_IMPORT_FILE_BUTTON,
    COLLECTION_IMPORT_LIBRARY_BUTTON,
    set_widget_id,
)


def build_collections_panel(
    tree_view: QTreeView,
    *,
    import_collection: Callable[[], None] | None = None,
    import_collection_from_file: Callable[[], None] | None = None,
    import_collection_from_library: Callable[[], None] | None = None,
    export_collection: Callable[[], None],
    export_all_collections: Callable[[], None],
) -> QWidget:
    """Build the collection tree panel and connect its action buttons."""
    file_import = import_collection_from_file or import_collection
    if file_import is None:
        raise ValueError("A file collection import callback is required")
    library_import = import_collection_from_library or (lambda: None)

    panel = QWidget()
    layout = QVBoxLayout(panel)
    layout.setContentsMargins(0, 0, 0, 0)

    import_btn = QPushButton(BUTTON_IMPORT_COLLECTION)
    set_widget_id(import_btn, COLLECTION_IMPORT_BUTTON)
    import_btn.clicked.connect(file_import)
    # Keep the legacy widget-ID seam for existing integrations and tests, while
    # exposing only the explicit source choices in the visible panel.
    import_btn.setVisible(False)

    file_import_btn = QPushButton(BUTTON_IMPORT_COLLECTION_FROM_FILE)
    set_widget_id(file_import_btn, COLLECTION_IMPORT_FILE_BUTTON)
    file_import_btn.clicked.connect(file_import)

    library_import_btn = QPushButton(BUTTON_IMPORT_COLLECTION_FROM_LIBRARY)
    set_widget_id(library_import_btn, COLLECTION_IMPORT_LIBRARY_BUTTON)
    library_import_btn.clicked.connect(library_import)

    export_btn = QPushButton(BUTTON_EXPORT_COLLECTION)
    set_widget_id(export_btn, COLLECTION_EXPORT_BUTTON)
    export_btn.clicked.connect(export_collection)

    export_all_btn = QPushButton(BUTTON_EXPORT_ALL_COLLECTIONS)
    set_widget_id(export_all_btn, COLLECTION_EXPORT_ALL_BUTTON)
    export_all_btn.clicked.connect(export_all_collections)

    buttons_row = QHBoxLayout()
    buttons_row.addWidget(import_btn)
    buttons_row.addWidget(file_import_btn)
    buttons_row.addWidget(library_import_btn)
    buttons_row.addWidget(export_btn)
    buttons_row.addWidget(export_all_btn)
    buttons_row.addStretch(1)

    layout.addWidget(tree_view)
    layout.addLayout(buttons_row)
    return panel
