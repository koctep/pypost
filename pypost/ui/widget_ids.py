"""Stable Qt widget identities for agents and automated UI tests.

Primary contract: ``QObject.objectName``. For ``QWidget`` instances the same
string is mirrored on ``accessibleIdentifier`` when the Qt API is available.
Do not use ``accessibleName`` or visible label text as automation identities —
those may change with locale or copy edits.

See ``doc/dev/ui_identity.md`` for the naming convention and lookup rules.
"""

from __future__ import annotations

from PySide6.QtCore import QObject
from PySide6.QtWidgets import QWidget

# Key surfaces (PYPOST-834). Values are stable across theme/locale.
MAIN_WINDOW = "pypost_main_window"
COLLECTION_TREE = "pypost_collection_tree"
REQUEST_TABS = "pypost_request_tabs"
METHOD_COMBO = "pypost_method_combo"
URL_INPUT = "pypost_url_input"
SEND_BUTTON = "pypost_send_button"
REQUEST_BODY_EDIT = "pypost_request_body_edit"
REQUEST_DETAIL_TABS = "pypost_request_detail_tabs"
RESPONSE_PANEL = "pypost_response_panel"
ENV_BAR = "pypost_env_bar"
ENV_SELECTOR = "pypost_env_selector"
ENV_MANAGE_BUTTON = "pypost_env_manage_button"
SETTINGS_BUTTON = "pypost_settings_button"
PLUS_TAB_PLACEHOLDER = "pypost_plus_tab_placeholder"

KEY_WIDGET_IDS = (
    MAIN_WINDOW,
    COLLECTION_TREE,
    REQUEST_TABS,
    METHOD_COMBO,
    URL_INPUT,
    SEND_BUTTON,
    REQUEST_BODY_EDIT,
    REQUEST_DETAIL_TABS,
    RESPONSE_PANEL,
    ENV_BAR,
    ENV_SELECTOR,
    ENV_MANAGE_BUTTON,
    SETTINGS_BUTTON,
)


def set_widget_id(widget: QObject, widget_id: str) -> None:
    """Set ``objectName`` and mirror ``accessibleIdentifier`` on QWidgets."""
    widget.setObjectName(widget_id)
    if isinstance(widget, QWidget):
        setter = getattr(widget, "setAccessibleIdentifier", None)
        if callable(setter):
            setter(widget_id)
