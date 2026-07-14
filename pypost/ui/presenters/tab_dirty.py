"""Tab dirty-state helpers (UI layer)."""

from __future__ import annotations

from typing import TYPE_CHECKING

from pypost.core.request_persisted_fields import persisted_fields_equal

if TYPE_CHECKING:
    from pypost.ui.presenters.tabs_presenter import RequestTab


def is_tab_dirty(tab: RequestTab) -> bool:
    """Return True when the tab editor differs from its adopted persisted baseline."""
    baseline = tab.persisted_baseline
    if baseline is None:
        return False
    ui_data = tab.request_editor.get_request_data_from_ui()
    return not persisted_fields_equal(ui_data, baseline)
