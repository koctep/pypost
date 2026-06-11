"""Helpers for comparing persisted request fields across isolated tabs."""

from __future__ import annotations

from typing import TYPE_CHECKING

from pypost.models.models import RequestData

if TYPE_CHECKING:
    from pypost.ui.presenters.tabs_presenter import RequestTab

_PERSISTED_FIELD_NAMES = (
    "name",
    "url",
    "method",
    "headers",
    "params",
    "body",
    "body_type",
    "yaml_as_json",
    "post_script",
    "expose_as_mcp",
    "retry_policy",
)


def snapshot_persisted_fields(data: RequestData) -> RequestData:
    """Return a deep copy containing only fields persisted with a collection item."""
    return data.model_copy(deep=True)


def persisted_fields_equal(a: RequestData, b: RequestData) -> bool:
    """Return True when two requests match on all persisted editor fields."""
    for field_name in _PERSISTED_FIELD_NAMES:
        if getattr(a, field_name) != getattr(b, field_name):
            return False
    return True


def is_tab_dirty(tab: RequestTab) -> bool:
    """Return True when the tab editor differs from its adopted persisted baseline."""
    baseline = tab.persisted_baseline
    if baseline is None:
        return False
    ui_data = tab.request_editor.get_request_data_from_ui()
    return not persisted_fields_equal(ui_data, baseline)
