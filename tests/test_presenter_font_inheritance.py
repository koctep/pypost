"""PYPOST-803: Presenter widgets inherit global application font (no apply_font)."""

import pytest

from pypost.ui.presenters.collections_presenter import CollectionsPresenter
from pypost.ui.presenters.tabs_presenter import TabsPresenter
from pypost.ui.styles.style_manager import StyleManager
from tests.helpers.collections_tree import FakeMetrics, FakeRequestManager, FakeStateManager
from tests.test_tabs_presenter import FakeRequestManager as TabsFakeRequestManager
from tests.test_tabs_presenter import FakeStateManager as TabsFakeStateManager
from pypost.models.settings import AppSettings

pytestmark = pytest.mark.timeout(60)


def _apply_font_size(qapp, size: int) -> None:
    StyleManager().apply_appearance(qapp, theme="system", font_size=size)

def test_collections_tree_inherits_application_font(qapp):
    presenter = CollectionsPresenter(
        FakeRequestManager([]),
        FakeStateManager(),
        FakeMetrics(),
        icons={},
    )
    _apply_font_size(qapp, 17)
    qapp.processEvents()
    assert presenter.widget.font().pointSize() == 17

def test_tabs_widget_inherits_application_font(qapp):
    presenter = TabsPresenter(
        TabsFakeRequestManager(),
        TabsFakeStateManager(),
        AppSettings(),
        metrics=FakeMetrics(),
    )
    presenter.add_new_tab()
    _apply_font_size(qapp, 19)
    assert presenter.widget.font().pointSize() == 19
